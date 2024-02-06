from mathutils import Color, Vector
import os.path as OSPath
from .texhelper import newtex_image, newtex_missing
import logging
log = logging.getLogger('bpy.ops.import_mesh.bmd.matpipeline')
import bpy

# ### helper functions (some use those storage variables)

def makelink(nt, a, b):
    """automatically links a and b,
    `b` being a node socket and `a` being either another node socker or a value"""
    if isinstance(a, bpy.types.NodeSocket):
        nt.links.new(a,b)
    else:
        # sometimes, default_value behaves weirdly (with color, and maybe vector
        # Color()s have a length of 3 (except for recent dev versions of 2.79),
        # but default_value might want length 4 (the case for every new version, hopefully)
        try:
            b.default_value = a
        except Exception:
            # assume we are dealing with color for now.
            value = (a.r, a.g, a.b, 1.0)
            b.default_value = value

# function-local storage
MIX_GROUP_NODETREE_C = None
MIX_GROUP_NODETREE_A = None
def get_mixgroup(type):
    """returns a GLSL-style mix() as a node group (for colors or floats)"""
    global MIX_GROUP_NODETREE_C
    global MIX_GROUP_NODETREE_A
    if type == 'C':

        if MIX_GROUP_NODETREE_C is None:
            MIX_GROUP_NODETREE_C = gnt = bpy.data.node_groups.new('glsl_mix', 'ShaderNodeTree')
            in_n = gnt.nodes.new('NodeGroupInput')
            out_n = gnt.nodes.new('NodeGroupOutput')  # creating real input and output nodes
            if bpy.app.version >= (4,0,0):
                gnt.interface.new_socket('mixer',in_out='INPUT',socket_type='NodeSocketColor',
                    description='values used as coefficients for the mixing of individual color channels')
                gnt.interface.new_socket('color_0',in_out='INPUT',socket_type='NodeSocketColor',
                    description='the color obtained when `mixer=(0,0,0)`')
                gnt.interface.new_socket('color_1',in_out='INPUT',socket_type='NodeSocketColor',
                    description='the color obtained when `mixer=(1,1,1)`')
                gnt.interface.new_socket('output',in_out='OUTPUT',socket_type='NodeSocketColor')
            #gnt.inputs.new('COLOR', 'blend_value')
            #gnt.inputs.new('COLOR', 'input_A')
            #gnt.inputs.new('COLOR', 'input_B')
            #gnt.outputs.new('COLOR', 'output')

            factor_node = gnt.nodes.new('ShaderNodeSeparateRGB')
            gnt.links.new(in_n.outputs[0], factor_node.inputs[0])

            in_a = gnt.nodes.new('ShaderNodeSeparateRGB')
            in_b = gnt.nodes.new('ShaderNodeSeparateRGB')
            node = gnt.nodes.new('ShaderNodeCombineRGB')

            gnt.links.new(in_n.outputs[1], in_a.inputs[0])
            gnt.links.new(in_n.outputs[2], in_b.inputs[0])

            gnt.links.new(node.outputs[0], out_n.inputs[0])  # nodegroup output

            for compindex in (0, 1, 2):
                # this operation must be done for each color channel

                # generate multiplicator for second input
                inverted_factor = gnt.nodes.new('ShaderNodeMath')
                inverted_factor.operation = 'SUBTRACT'
                inverted_factor.inputs[0].default_value = 1.0
                gnt.links.new(factor_node.outputs[compindex], inverted_factor.inputs[1])

                # generate multiplied value (input 0)
                weighted_value_0 = gnt.nodes.new('ShaderNodeMath')
                weighted_value_0.operation = 'MULTIPLY'
                gnt.links.new(in_a.outputs[compindex], weighted_value_0.inputs[0])
                gnt.links.new(inverted_factor.outputs[0], weighted_value_0.inputs[1])

                # generate multiplied value (input 1)
                weighted_value_1 = gnt.nodes.new('ShaderNodeMath')
                weighted_value_1.operation = 'MULTIPLY'
                gnt.links.new(in_b.outputs[compindex], weighted_value_1.inputs[0])
                gnt.links.new(factor_node.outputs[compindex], weighted_value_1.inputs[1])

                # add both of them
                weighted_sum = gnt.nodes.new('ShaderNodeMath')
                weighted_sum.operation = 'ADD'
                gnt.links.new(weighted_value_0.outputs[0], weighted_sum.inputs[0])
                gnt.links.new(weighted_value_1.outputs[0], weighted_sum.inputs[1])

                # link channel to be combined
                gnt.links.new(weighted_sum.outputs[0], node.inputs[compindex])

        return MIX_GROUP_NODETREE_C
    elif type == 'A':
        if MIX_GROUP_NODETREE_A is None:
            MIX_GROUP_NODETREE_A = gnt = bpy.data.node_groups.new('float_mix', 'ShaderNodeTree')

            in_n = gnt.nodes.new('NodeGroupInput')
            out_n = gnt.nodes.new('NodeGroupOutput')  # creating real input and output nodes

            if bpy.app.version >= (4,0,0):
                gnt.interface.new_socket('mixer',in_out='INPUT',socket_type='NodeSocketFloat',
                    description='values used as coefficients for the mixing')
                gnt.interface.new_socket('color_0',in_out='INPUT',socket_type='NodeSocketFloat',
                    description='the value obtained when `mixer=0`')
                gnt.interface.new_socket('color_1',in_out='INPUT',socket_type='NodeSocketFloat',
                    description='the value obtained when `mixer=1`')
                gnt.interface.new_socket('output',in_out='OUTPUT',socket_type='NodeSocketFloat')

            inv_factor = gnt.nodes.new('ShaderNodeMath')
            inv_factor.operation = 'SUBTRACT'
            inv_factor.inputs[0].default_value = 1.0
            gnt.links.new(in_n.outputs[0], inv_factor.inputs[1])

            node = gnt.nodes.new('ShaderNodeMath')
            node.operation = 'ADD'

            factor_a = gnt.nodes.new('ShaderNodeMath')
            factor_b = gnt.nodes.new('ShaderNodeMath')
            factor_a.operation = factor_b.operation = 'MULTIPLY'

            gnt.links.new(in_n.outputs[1], factor_a.inputs[0])  # linking for weighting
            gnt.links.new(in_n.outputs[2], factor_b.inputs[0])
            gnt.links.new(in_n.outputs[0], factor_b.inputs[1])  # linking weight factors
            gnt.links.new(inv_factor.outputs[0], factor_a.inputs[1])

            gnt.links.new(factor_a.outputs[0], node.inputs[0])  # final linking
            gnt.links.new(factor_b.outputs[0], node.inputs[1])

            gnt.links.new(node.outputs[0], out_n.inputs[0])
        return MIX_GROUP_NODETREE_A

# function-local storage
MIX_GROUP_MTX = {}
def get_mtxmix(id, mtx):
    """returns a node group which multiplies a vector by a matrix (M*v)"""
    if id not in MIX_GROUP_MTX.keys():
        MIX_GROUP_MTX[id] = gnt = bpy.data.node_groups.new('matrix product(%x)'%id, 'ShaderNodeTree')
        in_n = gnt.nodes.new('NodeGroupInput')
        out_n = gnt.nodes.new('NodeGroupOutput')  # creating real input and output nodes
        #gnt.inputs.new('COLOR', 'blend_value')
        #gnt.inputs.new('COLOR', 'input_A')
        #gnt.inputs.new('COLOR', 'input_B')
        #gnt.outputs.new('COLOR', 'output')

        mtx_lines = [gnt.nodes.new('ShaderNodeVectorMath') for _ in (0,1,2)]

        recombine = gnt.nodes.new('ShaderNodeCombineXYZ')
        translation = gnt.nodes.new('ShaderNodeVectorMath')
        translation.operation = 'ADD'
        gnt.links.new(recombine.outputs[0], translation.inputs[0])
        gnt.links.new(translation.outputs[0], out_n.inputs[0])

        # XCX complete matrix

        for compindex in (0, 1, 2):
            # this operation must be done for each matrix row

            gnt.links.new(in_n.outputs[0], mtx_lines[compindex].inputs[1])
            mtx_lines[compindex].operation = 'DOT_PRODUCT'
            gnt.links.new(mtx_lines[compindex].outputs[1], recombine.inputs[compindex])

            # XCX complete mateix

    return MIX_GROUP_MTX[id]

def makeOpNode(placer, in1, in2, type='value', op='ADD', **placerkw):
    """ returns a node for mathematical operations""" # XCX redo this
    # type in 'value', 'color', 'vector'
    if type=='value':
        node = placer.add('ShaderNodeMath', **placerkw)
        in1_id = 0
        in2_id = 1
        node.operation=op
    elif type=='color':
        node = placer.add('ShaderNodeMixRGB', **placerkw)
        in1_id = 1
        in2_id = 2
        node.blend_type=op
        node.inputs[0].default_value = 1.0
    elif type=='vector':
        # TODO implement this
        log.error('the dev goofed')
        raise ValueError('THE DEV GOOFED')
    else:
        log.warning('makeOpNode: unknown node type %s', type)
        raise ValueError('blame the dev')

    makelink(placer.nt, in1, node.inputs[in1_id])
    makelink(placer.nt, in2, node.inputs[in2_id])
    return node, node.outputs[0]


class Holder:
    """class to hold a variable: this variable can be set after this object is returned"""
    def __init__(self, data=None):
        self.data = data

class Sampler:
    """a class to hold texture access information"""
    def __init__(self, name=None):
        self.name = name
        self.wrapS = True
        self.wrapT = True
        self.mirrorS = False
        self.mirrorT = False

    def setTexWrapMode(self, smode, tmode):
        if smode == 0:
            self.wrapS = False
        elif smode == 1:
            pass
        elif smode == 2:
            self.mirrorS = True
        else:
            raise ValueError('invalid WrapMode')

        if tmode == 0:
            self.wrapT = False
        elif tmode == 1:
            pass
        elif tmode == 2:
            self.mirrorT = True
        else:
            raise ValueError('invalid WrapMode')

    def export(self, placer, coords, is_alpha=False):
        """returns a node to get a texture acces
        (coords is the nodesocket giving the texture coordinates)"""

        if is_alpha == 'both':
            is_alpha_row = 0
        else:  # assume is_alpha is a bool
            is_alpha_row = int(is_alpha)
        if self.name is None:
            image = newtex_missing()
        else:
            image = newtex_image(self.name)
        texnode = placer.add('ShaderNodeTexImage', row=is_alpha_row)
        texnode.image = image

        if isinstance(coords, Vector):
            vectnode = placer.add('ShaderNodeCombineXYZ', row=is_alpha_row)
            vectnode.inputs[0].default_value = coords.x
            vectnode.inputs[1].default_value = coords.y
            vectnode.inputs[2].default_value = coords.z
            coords = vectnode.outputs[0]
        
        # XCX image mapping (clamp, mirror)
        if self.mirrorS or self.mirrorT:
            local_frame = placer.add('NodeFrame', 'mirroring', row=is_alpha_row)
            local_placer = NodePlacer(placer.nt, local_frame, 10, False, 2)

            sep = local_placer.add('ShaderNodeSeparateXYZ')
            cmb = local_placer.add('ShaderNodeCombineXYZ')

            # use ping-pong nodes for mirroring

            if self.mirrorS:
                node = local_placer.add('ShaderNodeMath', row=0)
                placer.nt.links.new(sep.outputs[0], node.inputs[0])
                placer.nt.links.new(node.outputs[0], cmb.inputs[0])
                node.operation = 'PINGPONG'
                node.inputs[1].default_value = 1
            else:
                placer.nt.links.new(sep.outputs[0], cmb.inputs[0])
            if self.mirrorT:
                node = local_placer.add('ShaderNodeMath', row=1)
                placer.nt.links.new(sep.outputs[1], node.inputs[0])
                placer.nt.links.new(node.outputs[0], cmb.inputs[1])
                node.operation = 'PINGPONG'
                node.inputs[1].default_value = 1
            else:
                placer.nt.links.new(sep.outputs[1], cmb.inputs[1])

            placer.nt.links.new(coords, sep.inputs[0])
            placer.nt.links.new(cmb.outputs[0], texnode.inputs[0])
            local_placer.reappend(cmb)
            local_placer.update()
        else:
            placer.nt.links.new(coords, texnode.inputs[0])

        if is_alpha == 'both':
            return (texnode.outputs[0], texnode.outputs[1])
        else:  # assume is_alpha is a bool.
            return texnode.outputs[is_alpha_row]


class NodePlacer:
    """a class to automatically place nodes on a 2D space, in a logical way."""
    
    def __init__(self, nt, frame=None, spacing=60, vertical=False, nrows=1):
        self.nt = nt
        self.frame = frame
        # self.pos = 0  # holds a position 'cursor'
        self.spacing = spacing
        self.is_vert = vertical
        self.rows = [[] for _ in range(nrows)]

    def add(self, nodetype, name=None, row=None):
        """adds a new node to the placer (and to the nodetree)"""
        node = self.nt.nodes.new(nodetype)
        if name is not None:
            node.name = name
            node.label = name
        if self.frame:
            node.parent = self.frame

        if row is not None:
            self.rows[row].append(node)
        else:  # all rows
            for r in self.rows:
                r.append(node)
        return node

    def update(self):
        """updates the placing for all registered nodes"""
        # first, update "vertical" row size (and store max ro length)
        max_row_length = len(self.rows[0])
        for i in range(1, len(self.rows)):
            max_y = 0
            max_row_length = max(max_row_length, len(self.rows[i]))
            for node in self.rows[i-1]:
                max_y = min(max_y, self.getend_c2(node))  # use minimum for y!
            for node in self.rows[i]:
                node.location[int(not self.is_vert)] = max_y - self.spacing

        # update "horizontal" position
        # that means column per columns, but all rows might not
        # have the same size
        prev_position = 0
        for i in range(max_row_length):
            new_position = prev_position
            for r in self.rows:
                if len(r) > i:
                    r[i].location[int(self.is_vert)] = prev_position
                    new_position = max(new_position, self.getend_c1(r[i]))
            prev_position = new_position + self.spacing
        # TODO: slight problem if a multi_row node is large and at different positions in rows

        # update frame dimentions
        if self.frame is None:
            return  # next part is useless if there is no frame

        max_y = 0
        for node in self.rows[-1]:
            if len(r):
                max_y = max(max_y, self.getend_c2(node))
        max_x = 0
        for r in self.rows:
            if len(r):
                max_x = max(max_x, self.getend_c1(r[-1]))
        if self.is_vert:
            self.frame.width = max_y + 60
            self.frame.height = max_x + 60
        else:
            self.frame.width = max_x + 60
            self.frame.height = max_y + 60  # this is native frame padding

    def reappend(self, node):
        for r in self.rows:
            if node in r:
                r.remove(node)
                r.append(node)

    def __del__(self):
        self.update()  # make a last layout change before closing

    def getend_c1(self, node):
        """returns 'end' of a node, with its first coordinate (usually x)"""
        if self.is_vert:
            return node.location[1] - node.height  # height goes negative!
        else:
            return node.location[0] + node.width
    def getend_c2(self, node):
        """returns 'end' of a node, with its first coordinate (usually y)"""
        if self.is_vert:
            return node.location[0] + node.width
        else:
            return node.location[1] - node.height

def getAlphaCompare(ac):
    if ac.comp0==0:
        a = False  # 'do not discard'
    elif ac.comp0==7:
        a = True
    else:
        return 'default'  # alpha compare depends(?) on actual alpha channel
        # quit this function early
    if ac.comp1==0:
        b=False
    elif ac.comp1==7:
        b=True
    else:
        return 'default'

    if ac.alphaOp == 0:
        return not (a and b)
    elif ac.alphaOp==1:
        return not (a or b)
    elif ac.alphaOp==2:
        return not a^b  # not xor
    else:
        return a^b

class MaterialSpace:
    """holds reused variables for code->node system conversion"""
    def __init__(self, nodetree):
        self.nt = nodetree

        self.finalcolorc = Holder()
        self.finalcolora = Holder()
        self.vertexcolorc = Holder()
        self.vertexcolora = Holder()
        self.reg1c = Holder()
        self.reg1a = Holder()
        self.reg2c = Holder()
        self.reg2a = Holder()
        self.reg3c = Holder()
        self.reg3a = Holder()
        self.ac_const = 'default'  # for alpha compare. can force transparent or opaque

        self.texcoords = []
        self.vcolorindex = 0  # somehow never used ??

        self.textures = [None]*8

        self.konsts = [None]*8

        self.placer = NodePlacer(self.nt)


    # those functions are used for node computation
    def getRegFromId(self, id):
        if id == 0:
            return self.finalcolorc, self.finalcolora
        elif id == 1:
            return self.reg1c, self.reg1a
        elif id == 2:
            return self.reg2c, self.reg2a
        elif id == 3:
            return self.reg3c, self.reg3a

    def getTexAccess(self, info, type, placer):
        return self.textures[info.texMap].export(placer, self.texcoords[info.texCoordId], type)
        #getTexture(placer, self.textures[info.texMap], self.texcoords[info.texCoordId], type)

    def getRasColor(self, info):
        return self.vertexcolorc.data, self.vertexcolora.data
        """switch(info.chanId)
          {
            case 0:
              return "gl_Color.rgb";
            case 1:
              return "gl_SecondaryColor.rgb";
            case 2:
              return "gl_Color.a";
            case 3:
              return "gl_SecondaryColor.a";
            case 4:
              return "return gl_Color";
            case 5:
              return "return gl_SecondaryColor";
            case 6:
              return "vec4(0.0, 0.0, 0.0, 0.0);";
            //TODO: 7, 8
            default:
            {
              warn("getRasColor(): unknown chanId 0x%x", info.chanId);
              return "vec4(0.0, 1.0, 0.0, 1.0);";
            }"""

    def getColorIn(self, op, konst, info, placer):
        if op <= 7:
            if op % 2:
                node = placer.add('ShaderNodeCombineRGB', row=0)
                for i in (0,1,2):
                    makelink(self.nt, self.getRegFromId(op//2)[1].data, node.inputs[i])
                return node.outputs[0]
            else:
                return self.getRegFromId(op//2)[0].data
        elif op == 8:
            return self.getTexAccess(info, 0, placer)
        elif op == 9:
            tex_out = self.getTexAccess(info, 1, placer)
            node = placer.add('ShaderNodeCombineRGB', row=0)
            for i in (0,1,2):
                self.nt.links.new(tex_out, node.inputs[i])
            return node.outputs[0]
            # XCX are you sure that alpha channel can be used like that?
        elif op == 10:
            return self.getRasColor(info)[0]
        elif op == 11:
            node = placer.add('ShaderNodeCombineRGB', row=0)
            for i in (0,1,2):
                makelink(self.nt, self.getRasColor(info)[1], node.inputs[i])
            return node.outputs[0]
        elif op == 12:
            return Color((1,1,1))
        elif op == 13:
            return Color((0.5, 0.5, 0.5))
        elif op == 14:
            if konst <= 7:
                val = (8-konst)/8
                return Color((val,val,val))
            elif konst < 0xc:
                log.warn("getColorOp(): unknown konst %x", konst)
                return Color((1,0,0))

            konst -= 0xc
            var = self.konsts[(konst % 4)*2]
            if konst//4 == 4:  # triple alpha
                node = placer.add('ShaderNodeCombineRGB', row=0)
                for i in (0,1,2):
                    makelink(self.nt, self.konsts[(konst % 4)*2+1], node.inputs[i])
                return node.outputs[0]
            elif konst//4 == 0:
                return var
            else:
                node1 = placer.add('ShaderNodeSeparateRGB', row=0)
                node2 = placer.add('ShaderNodeCombineRGB', row=0)
                makelink(self.nt, var, node1.inputs[0])
                for i in (0,1,2):
                    self.nt.links.new(node1.outputs[konst//4 -1], node2.inputs[i])
                return node2.outputs[0]
        else:
            if op != 15:
                log.warning("Unknown colorIn %d", op)
            return Color((0, 0, 0))

    def getAlphaIn(self, op, konst, info, placer):
        if op <= 3:
            if self.getRegFromId(op)[1].data is None:
                pass
            return self.getRegFromId(op)[1].data
        elif op == 4:
            # if self.getTexAccess(info, 'alpha') is None:
            #     pass  # XCX reimplement? erase?
            return self.getTexAccess(info, 1, placer)
        elif op == 5:
            if self.getRasColor(info)[1] is None:
                pass
            return self.getRasColor(info)[1]
        elif op == 6:
            if konst <= 7:
                return (8-konst)/8
            elif konst < 0x10:
                log.warn("getColorOp(): unknown konst %x", konst)
                return 0.0
            konst -= 0x10
            if konst // 4 == 3:  # alpha
                return self.konsts[(konst % 4) * 2 + 1]
            else:
                node = placer.add('ShaderNodeSeparateRGB', row=1)
                makelink(self.nt, self.konsts[(konst % 4) * 2], node.inputs[0])
                return node.outputs[konst//4]
        elif op == 7:
            return 0.0
        else:
            raise ValueError('undefined OPerator in GetAlphaIn')

    def getMods(self, destnode, dest, bias, scale, clamp, type, placer):
        if type not in (0,1):
            log.error("getMods(): unknown type %d", type)
            raise ValueError()
        if bias == 0:
            ret = dest
            node = destnode
        else:
            if bias <= 2:
                if bias == 2:
                    val = -0.5
                else:
                    val = 0.5
                if type == 0:
                    bias_out = Color((val, val, val))
                else:
                    bias_out = val
            else:
                log.warning("getMods(): unknown bias %d", bias)
                if type == 0:
                    bias_out = Color((0,0,0))
                else:
                    bias_out = 0
            if type==1:
                node, ret = makeOpNode(placer, dest, bias_out, 'value', 'ADD', row=1)
            else:
                node, ret = makeOpNode(placer, dest, bias_out, 'color', 'ADD', row=0)

        if scale == 0:
            pass
        elif 0 < scale <=3 :
            scale =  ('unused', 2, 4, 0.5)[scale]
            if type==1:
                node, ret = makeOpNode(placer, ret, scale, 'value', 'MULTIPLY', row=1)
            else:
                node, ret = makeOpNode(placer, ret, Color(3*(scale,)), 'color', 'MULTIPLY', row=0)

        else:
            log.warning("getMods(): unknown scale %d", scale)

        if clamp:
            node.use_clamp=True
        return ret

    def getOp(self, op, bias, scale, clamp, regId, ins, type, placer):
        dest = self.getRegFromId(regId)[type]

        if op in (0,1):
            if type==0:  # color
                nodegroup = get_mixgroup('C')
                node = placer.add('ShaderNodeGroup', row=0)
                node.node_tree = nodegroup

                makelink(self.nt, ins[2], node.inputs[0])
                makelink(self.nt, ins[0], node.inputs[1])
                makelink(self.nt, ins[1], node.inputs[2])
            else:  # alpha
                nodegroup = get_mixgroup('A')
                node = placer.add('ShaderNodeGroup', row=1)
                node.node_tree = nodegroup

                makelink(self.nt, ins[2], node.inputs[0])
                makelink(self.nt, ins[0], node.inputs[1])
                makelink(self.nt, ins[1], node.inputs[2])
            dest.data = node.outputs[0]
            mix_out = node.outputs[0]
            if op == 0:
                op_str = 'ADD'
            else:
                op_str = 'SUBTRACT'
                log.warning("getOp(): op 1 might not work (using subtraction)")

            node, ret = makeOpNode(placer, ins[3], mix_out, ['color', 'value'][type], op_str, row=type)

            #if type(typeeval) == Vector:
            #    node = nodetree.nodes.new('ShaderNodeVectorMath')
            #    node.operation = op_str
            #    self.nt.links.new(mix_out, node.inputs[0])
            #
            #    if self.inputs[1].type != 'val':  # vector values DO exist here
            #    in_b = self.inputs[1].export(self.nt)
            #        self.nt.links.new(in_b, node.inputs[1])
            #    else:
            #        node.inputs[1].default_value[0] = self.inputs[1].value.x
            #        node.inputs[1].default_value[1] = self.inputs[1].value.y
            #        node.inputs[1].default_value[2] = self.inputs[1].value.z

            dest.data = self.getMods(node, ret, bias, scale, clamp, type, placer)
            return

        elif op >= 8 and op <= 0xd:
            log.warning('as_int color comparaison is not supported yet. Using bland mixing instead')
            if type==0:  # color
                nodegroup = get_mixgroup('C')
                node = placer.add('ShaderNodeGroup', row=0)
                node.node_tree = nodegroup

                makelink(self.nt, Color((0.5,0.5,0.5)), node.inputs[0])
                makelink(self.nt, ins[2], node.inputs[1])
                makelink(self.nt, ins[3], node.inputs[2])
            else:  # alpha
                nodegroup = get_mixgroup('A')
                node = placer.add('ShaderNodeGroup', row=1)
                node.node_tree = nodegroup

                makelink(self.nt, 0.5, node.inputs[0])
                makelink(self.nt, ins[2], node.inputs[1])
                makelink(self.nt, ins[3], node.inputs[2])   
            dest.data = node.outputs[0]
            mix_out = node.outputs[0]
            return
            if type == 0:
                pass
                # out << "  if(";

                # if op >= 0xa:
                #     out << "dot(";

                # out << ins[0]

                # switch(op)
                # {
                # case 8:
                # case 9:
                #     out << ".r"; break;
                # case 0xa:
                # case 0xb:
                #     out << ".rg, vec2(255.0/65535.0, 255.0*256.0/65535.0))"; break;
                # case 0xc:
                # case 0xd:
                #     out << ".rgb, vec3(255.0/16777215.0, 255.0*256.0/16777215.0, 255.0*65536.0/16777215.0))"; break;
                # }

                # if op%2 == 0:
                #     out << " > ";
                # else:
                #     out << " == ";

                # if op >= 0xa:
                #     out << "dot(";

                # out << ins[1];

                # switch(op)
                # {
                # case 8:
                # case 9:
                #   out << ".r"; break;
                # case 0xa:
                # case 0xb:
                #     out << ".rg, vec2(255.0/65535.0, 255.0*256.0/65535.0))"; break;
                # case 0xc:
                # case 0xd:
                #     out << ".rgb, vec3(255.0/16777215.0, 255.0*256.0/16777215.0, 255.0*65536.0/16777215.0))"; break;
                # }


                # out << ")\n    " << dest << " = " << ins[2] << ";\n"
                #     << "  else\n    " << dest << " = " << ins[3] << ";\n";

                # //out << getMods(dest, 0, scale, clamp, type);
                # if(bias != 3 || scale != 1 || clamp != 1)
                #     warn("getOp() comp0: unexpected bias %d, scale %d, clamp %d", bias, scale, clamp);

                # return out.str();
            else:  # (type==1)
                pass
                # log.warning("getOp() type %d unexpected for op %x", type, op)  # TODO: need2fix

        elif op in (0xe, 0xf):
            if type == 1:
                # out << "  if(" << ins[0];
                # if(op == 0xe):
                #     out << " > ";
                # else:
                #     out << " == ";
                # out << ins[1] << ")\n    " << dest << " = " << ins[2] << ";\n"
                #    << "  else\n    " << dest << " = " << ins[3] << ";\n";

                # //out << getMods(dest, 0, scale, clamp, type)
                # if bias != 3 or scale != 1 or clamp != 1:
                #     log.warning("getOp() comp0: unexpected bias %d, scale %d, clamp %d", bias, scale, clamp)

                return
            # //TODO: gnd.bdl uses 0xe on type == 0

        else:
            log.warning("getOp(): unsupported op %d", op)
            if type == 0:
                dest.data = Vector((0,1,0))  # unsupported
            else:
                dest.data = 0.5  # unsupported
            return

    # this is a transfer function to create blender nodes
    def export(self):
        # then, create output and matertial nodes
        mat_node = self.placer.add('ShaderNodeBsdfDiffuse')
        alpha_node = self.placer.add('ShaderNodeBsdfTransparent')
        mix_node = self.placer.add('ShaderNodeMixShader')
        out_node = self.placer.add('ShaderNodeOutputMaterial')

        # link them
        self.nt.links.new(mat_node.outputs[0], mix_node.inputs[2])  # material:out_color -> output:color
        self.nt.links.new(alpha_node.outputs[0], mix_node.inputs[1])
        self.nt.links.new(mix_node.outputs[0], out_node.inputs[0])

        # create color and link
        makelink(self.nt, self.finalcolorc.data, mat_node.inputs[0])

        # create alpha and link
        # alpha testing!!

        if self.ac_const == 'default' or True:
            makelink(self.nt, self.finalcolora.data, mix_node.inputs[0])  # amount of alpha
        elif self.ac_const == True:  # discard
            mix_node.inputs[0].default_value = 0
        elif self.ac_const == False:
            mix_node.inputs[0].default_value = 1
        else:
            raise ValueError('alpha compare failed.')


def makeTexCoords(material, texGen, i, matbase, mat3, data_placer):
    """???"""
    if texGen.texGenType in (0, 1):
        if (texGen.texGenSrc >=4 and texGen.texGenSrc <=11):
            nodesrc = data_placer.add('ShaderNodeUVMap', row=i+2)
            nodesrc.uv_map = 'UV '+str(texGen.texGenSrc-4)
            dst = nodesrc.outputs[0]
        elif texGen.texGenSrc in (0,1):
            nodesrc = data_placer.add('ShaderNodeNewGeometry', row=i+2)
            log.warning("writeTexGen() type 0: Found src %d, might not yet work (use transformed or untransformed coordinate?)", texGen.texGenSrc)
            dst = nodesrc.outputs[texGen.texGenSrc]
        else:
            log.warning("writeTexGen() type %d: unsupported src 0x%x", texGen.texGenType, texGen.texGenSrc)
            dst = Vector((0,0,0))  # "null" vector

        if texGen.matrix == 0x3c:
            pass  # no texture matrix
        elif (texGen.matrix >= 0x1e and texGen.matrix <= 0x39):
            log.warning('Texture uses nativs matrix. Plz implement')
            # #(texGen.matrix - 0x1e)/3)  # XCX get the right matrix
            # nodemult = get_mtxmix((texGen.matrix - 0x1e)//3)
            # XCX trap: do not set this node with this value: act as multiplier right now
        else:
            log.warning("writeTexGen() type %s: unsupported matrix %x", texGen.texGenType, texGen.matrix)

        # dirty hack(doesn't work with animations for example) (TODO):

        # try if texcoord scaling is where i think it is
        if matbase.texMtxInfos[i] != 0xffff:
            tmi = mat3.texMtxInfos[matbase.texMtxInfos[i]]
            mapping = data_placer.add('ShaderNodeMapping', row=0)
            mapping.label=('TexCoordMatrix %d'%i)
            data_placer.nt.links.new(dst, mapping.inputs[0])
            mapping.inputs[3].default_value[0] = tmi.scaleU
            mapping.inputs[3].default_value[1] = tmi.scaleV
            mapping.inputs[1].default_value[0] = (tmi.scaleCenterX*(1 - tmi.scaleU))
            mapping.inputs[1].default_value[1] = (1 - tmi.scaleCenterY) * (1 - tmi.scaleV)
    elif texGen.texGenType == 0xa:
        if (texGen.matrix != 0x3c):
            log.warning("writeTexGen() type 0xa: unexpected matrix %x", texGen.matrix)
        if (texGen.texGenSrc != 0x13):
            log.warning("writeTexGen() type 0xa: unexpected src %x", texGen.texGenSrc)

        log.warning("writeTexGen(): Found type 0xa (SRTG), doesn't work right yet")
        dst = Vector((0,0,0))  # "null" vector

        #// t << "sphereMap*vec4(gl_NormalMatrix*gl_Normal, 1.0)";

        #out << "  vec3 u = normalize(gl_Position.xyz);\n";
        #out << "  vec3 refl = u - 2.0*dot(gl_Normal, u)*gl_Normal;\n";
        #out << "  refl.z += 1.0;\n";
        #out << "  float m = .5*inversesqrt(dot(refl, refl));\n";
        #out << "  " << dest << ".st = vec2(refl.x*m + .5, refl.y*m + .5);";

        #// out << "  " << dest << " = gl_MultiTexCoord0; //(unsupported)\n";
        #// out << "  " << dest << " = vec4(0.0, 0.0, 0.0, 0.0); //(unsupported)\n";
        #out << "  " << dest << " = color; //(not sure...)\n";
    else:
        log.warning("writeTexGen: unsupported type %x", hex(texGen.texGenType))
        dst = Vector((0,0,0))  # "null" vector
        #out << "  " << dest << " = vec4(0.0, 0.0, 0.0, 0.0); //(unsupported texgentype)\n"

    material.texcoords[i] = dst


def createMaterialSystem(matBase, mat3, tex1, texpath, extension, nt, params):
    """converts the data from a materialBase object to a blender node tree"""
    # ### vertex shader part:

    # ## first, delete existing nodes from tree
    while len(nt.nodes):
        nt.nodes.remove(nt.nodes[0])

    # ## then start preparing the material 'namespace'
    material = MaterialSpace(nt)
    if matBase.chanControls[0] < len(mat3.colorChanInfos):
        if __name__ == '__main__':  #XCX WHAT THE FLIP?!
            if mat3.colorChanInfos[matBase.chanControls[0]].matColorSource != 1:
                material.vcolorindex = 1

    data_placer = NodePlacer(nt, material.placer.add('NodeFrame', 'data'), 30, False,
                             3 + mat3.texGenCounts[matBase.texGenCountIndex])

    # missing light enabeling, seems so.
    if mat3.colorChanInfos[matBase.chanControls[0]].matColorSource == 1:
        node = data_placer.add('ShaderNodeVertexColor', row=0)
        node.layer_name = 'v_color_0'  # XCX what about layer 2 (this is more complicated than expected)?
        material.vertexcolorc.data = node.outputs[0]
        material.vertexcolora.data = node.outputs[1]
                
    else:
        c = mat3.color1[matBase.color1[0]]
        material.vertexcolorc.data = Color((c.r/255, c.g/255, c.b/255))
        material.vertexcolora.data = c.a/255
    if mat3.colorChanInfos[matBase.chanControls[0]].litMask:
        # XCX manage light better
        pass
        # material.vertexcolorc.data = material.vertexcolorc.data * Color((0.5, 0.5, 0.5))

        # # material.vertexcolora.data = material.vertexcolora.data * 0.5
        # # if matBase.color2[0] != 0xffff and matBase.color2[0] < len(mat3.color2):
        # #     amb = mat3.color2[matBase.color2[0]]

    material.texcoords = [None] * mat3.texGenCounts[matBase.texGenCountIndex]
    for i in range(mat3.texGenCounts[matBase.texGenCountIndex]):  # num TexGens == num Textures
        makeTexCoords(material, mat3.texGenInfos[matBase.texGenInfos[i]], i, matBase, mat3, data_placer)

    # ## fragment shader part
    for i in range(8):
        if matBase.texStages[i] != 0xffff:
            texId = mat3.texStageIndexToTextureIndex[matBase.texStages[i]]
            if len(tex1.texHeaders) <= texId:
                if params.PARANOID:
                    raise ValueError("Bad TEX/MAT section: texture {0:d} does not exist".format(texId))
                else:
                    material.textures[i] = Sampler()  # "missing" texture
                    log.warning("no known texture with  ID %d", texId)
            else:
                currTex = tex1.texHeaders[texId]
                material.textures[i] = Sampler(OSPath.join(texpath, tex1.stringtable[texId] + extension))
                material.textures[i].setTexWrapMode(currTex.wrapS, currTex.wrapT)  # XCX set min/mag filters ?
                
                    

    # konst colors
    # first determine if they are needed or not, then actually create the associated nodes.
    # XCX make it happen on the fly? not now.
    needK = [False]*4
    for i in range(mat3.tevCounts[matBase.tevCountIndex]):
        konstColor = matBase.constColorSel[i]
        konstAlpha = matBase.constAlphaSel[i]
        stage = mat3.tevStageInfos[matBase.tevStageInfo[i]]

        if (konstColor > 7 and konstColor < 0xc
           or konstAlpha > 7 and konstAlpha < 0x10):
            log.warning("createFragmentShaderString: Invalid color sel")
            continue  # should never happen

        if (konstColor > 7
            and (stage.colorIn[0] == 0xe or stage.colorIn[1] == 0xe
                 or stage.colorIn[2] == 0xe or stage.colorIn[3] == 0xe)):
            needK[(konstColor - 0xc) % 4] = True
        if (konstAlpha > 7
            and (stage.alphaIn[0] == 6 or stage.alphaIn[1] == 6
                 or stage.alphaIn[2] == 6 or stage.alphaIn[3] == 6)):
            needK[(konstAlpha - 0x10) % 4] = True

    for i in range(4):
        if needK[i]:
            c = mat3.color3[matBase.color3[i]]
            material.konsts[2*i] = Color((c.r/255, c.g/255, c.b/255))
            material.konsts[2*i+1] = c.a/255

     # same thing with the registries
    needReg = [False]*4
    for i in range(mat3.tevCounts[matBase.tevCountIndex]):
        stage = mat3.tevStageInfos[matBase.tevStageInfo[i]]
        needReg[stage.colorRegId] = True
        needReg[stage.alphaRegId] = True

        for j in range(4):
            if stage.colorIn[j] <= 7:
                needReg[stage.colorIn[j]//2] = True
            if stage.alphaIn[j] <= 3:
                needReg[stage.alphaIn[j]] = True

    for i in range(4):
        if needReg[i]:
            if i == 0:
                c = mat3.colorS10[matBase.colorS10[3]]
            else:
                c = mat3.colorS10[matBase.colorS10[i-1]]
            material.getRegFromId(i)[0].data = Color((c.r/255, c.g/255, c.b/255))
            material.getRegFromId(i)[1].data = c.a/255
    data_placer.update()

    # finally generate the tevStages
    for i in range(mat3.tevCounts[matBase.tevCountIndex]):
        order = mat3.tevOrderInfos[matBase.tevOrderInfo[i]]
        stage = mat3.tevStageInfos[matBase.tevStageInfo[i]]

        local_frame = material.placer.add('NodeFrame', 'tevStage %d' % i)
        local_placer = NodePlacer(material.nt, local_frame, 60, False, 2)

        colorIns = [None]*4
        for j in range(4):
            colorIns[j] = material.getColorIn(stage.colorIn[j], matBase.constColorSel[i], order, local_placer)

        material.getOp(stage.colorOp, stage.colorBias, stage.colorScale,
                       stage.colorClamp, stage.colorRegId, colorIns, 0, local_placer)

        alphaIns = [None]*4
        for j in range(4):
            alphaIns[j] = material.getAlphaIn(stage.alphaIn[j], matBase.constAlphaSel[i], order, local_placer)

        print(end='')
        material.getOp(stage.alphaOp, stage.alphaBias, stage.alphaScale,
                       stage.alphaClamp, stage.alphaRegId, alphaIns, 1, local_placer)

        local_placer.update()

    material.ac_const = getAlphaCompare(mat3.alphaCompares[matBase.alphaCompIndex])
    material.export()


def create_simple_material_system(matBase, mat3, tex1, texpath, extension, nt, params):
    """converts the data from a materialBase object to a blender node tree"""
    # ### vertex shader part:

    # ## first, delete existing nodes from tree
    while len(nt.nodes):
        nt.nodes.remove(nt.nodes[0])

    # ## then start preparing the material 'namespace'
    material = MaterialSpace(nt)
    data_placer = NodePlacer(
        nt,
        material.placer.add('NodeFrame', 'data'),
        30, False,
        mat3.texGenCounts[matBase.texGenCountIndex]+2
    )
    
    material.texcoords = [None] * mat3.texGenCounts[matBase.texGenCountIndex]
    for i in range(mat3.texGenCounts[matBase.texGenCountIndex]):  # num TexGens == num Textures
        makeTexCoords(material, mat3.texGenInfos[matBase.texGenInfos[i]], i, matBase, mat3, data_placer)

    sampler = None
    has_texture=True
    for i in range(8):
        if matBase.texStages[i] != 0xffff:
            texId = mat3.texStageIndexToTextureIndex[matBase.texStages[i]]
            currTex =tex1.texHeaders[texId]
            sampler = Sampler(OSPath.join(texpath, tex1.stringtable[texId] + extension))
            sampler.setTexWrapMode(currTex.wrapS, currTex.wrapT)
            break
    else:
        has_texture = False

    if has_texture:
        node_uv = data_placer.add('ShaderNodeUVMap', row=0)
        node_uv.uv_map = 'UV 0'
        material.finalcolorc.data, material.finalcolora.data = \
            sampler.export(data_placer, node_uv.outputs[0], is_alpha='both')
    else:
        colornode = data_placer.add('ShaderNodeRGB', 'ERROR')
        alphanode = data_placer.add('ShaderNodeValue', 'ERROR')
        colornode.outputs[0].default_value = [1,0,0,1]
        alphanode.outputs[0].default_value = 1
        
        material.finalcolorc.data = colornode.outputs[0]
        material.finalcolora.data = alphanode.outputs[0]

    data_placer.update()
    material.ac_const = getAlphaCompare(mat3.alphaCompares[matBase.alphaCompIndex])
    material.export()


DUMB_MAT = None
def get_dumb_material():
    global DUMB_MAT
    if DUMB_MAT is None:
        DUMB_MAT = bpy.data.materials.new('dumb material (used for nodes)')
    return DUMB_MAT
