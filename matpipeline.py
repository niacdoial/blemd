from mathutils import Color, Vector
from math import log2
from .texhelper import newtex_tex
import bpy

class Holder:
    """class to hold a variable: this variable can be set after this object is returned"""
    def __init__(self, data):
        self.data = data


class Node:
    """goal: temporary node system describing shader, to be converted in blender nodes.
    MaterialSpace holds reused variables from original glsl application"""

    def __init__(self, op='', data=0.0, inputs=()):

        if op:
            self.type = 'op'
            if type(op) == Color:
                print(end='')
            self.op = op
            self.value = data
            self.inputs = inputs
            if op == 'mixC' and inputs[1] == None:
                pass
        else:
            self.type = 'val'
        self.value = data

        self.exported = None  # exported blender node

    def __add__(self, other):
        if not isinstance(other, Node):
            other = Node(data=other)
        if other.type == 'val':
            if other.value in (0, Color((0,0,0)), Vector((0,0,0))):
                return self  # useless addition if other is zero
        if self.type == 'val':
            if self.value in (0, Color((0,0,0)), Vector((0,0,0))):
                return other  # useless addition if other is zero
        return Node('ADD', inputs=(self, other))

    def __mul__(self, other):
        if not isinstance(other, Node):
            other = Node(data=other)
        if other.type == 'val':
            if other.value in (1, Color((1,1,1)), Vector((1,1,1))):
                return self  # useless addition if other is zero
        if self.type == 'val':
            if self.value in (1, Color((1,1,1)), Vector((1,1,1))):
                return other  # useless addition if other is zero
        return Node('MULTIPLY', inputs=(self, other))

    def __sub__(self, other):
        if not isinstance(other, Node):
            other = Node(data=other)
        if other.type == 'val':
            if other.value in (0, Color((0,0,0)), Vector((0,0,0))):
                return self  # useless addition if other is zero
        if self.type == 'val':
            if self.value in (0, Color((0,0,0)), Vector((0,0,0))):
                return other  # useless addition if other is zero
        return Node('SUBTRACT', inputs=(self, other))

    def __le__(self, other):
        if not isinstance(other, Node):
            other = Node(data=other)
        return Node("bool", other - self + 0.000001)

    def __ge__(self, other):
        if not isinstance(other, Node):
            other = Node(data=other)
        return Node("bool", self - other + 0.000001)

    def __lt__(self, other):
        if not isinstance(other, Node):
            other = Node(data=other)
        return Node("bool", other - self)

    def __gt__(self, other):
        if not isinstance(other, Node):
            other = Node(data=other)
        return Node("bool", self - other)

    def export(self, nodetree):
        if self.exported is None:
            self.exported = self.export_inner(nodetree)
        return self.exported

    def export_inner(self, nodetree):
        """creates blender nodes from Node class.
        returns blender node output socket"""
        # to return, explicitly do it with a special socket,
        # or leave `node` as name of the final blender node which output 0 should be used

        # nodes that holds a value
        node = 'UNDEFINED'  # XCX DEBUG value to detect error and not crash stupidly
        if self.type == 'val':

            if type(self.value) in (float, int):  # value
                node = nodetree.nodes.new('ShaderNodeValue')
                node.outputs[0].default_value = self.value

            elif type(self.value) == Color:
                node = nodetree.nodes.new('ShaderNodeRGB')
                node.outputs[0].default_value = (self.value.r, self.value.g, self.value.b, 1.0)

            elif type(self.value) == Vector:
                raise ValueError('Vector inputs should have been dealed with beforehand')

            elif self.value[:2] == 'uv':  # get UV coordinates
                node = nodetree.nodes.new('ShaderNodeGeometry')
                node.uv_layer = 'UV '+self.value[2]
                return node.outputs[4]

            elif self.value == 'pos':  # get TRANSFORMED position
                node = nodetree.nodes.new('ShaderNodeGeometry')
                return node.outputs[0]

            elif self.value == 'nor':  # get TRANSFORMED normal
                node = nodetree.nodes.new('ShaderNodeGeometry')
                return node.outputs[5]

            elif self.value == 'VcolorC':  # get Vcolor
                node = nodetree.nodes.new('ShaderNodeGeometry')
                node.color_layer = 'v_color_0'  # XCX what about layer 2?
                return node.outputs[6]

            elif self.value == 'VcolorA':  # get Vcolor alpha
                node = nodetree.nodes.new('ShaderNodeGeometry')
                node.color_layer = 'v_color_alpha_0'
                return node.outputs[6]

        else:  # operation nodes
            if len(self.inputs) > 1:  # for type-sensitive operations,
                # need to detect type, but first input might be typeless
                if type(self.inputs[0].value) not in (float, int, Color, Vector)\
                        or self.inputs[0].type == 'op':
                    # the first input is special. the second one should have a defined type
                    if self.inputs[1].type == 'op':  # both special:
                        if self.inputs[1].op in ('mixC', 'triple'):
                            typeeval = Color()  # type is color: use a dumb var to express it
                        elif self.inputs[1].op in ('mixA', 'get_r', 'get_g', 'get_b'):
                            typeeval = 0.0  # type is number: use a dumb var to express it

                        else:
                            raise ValueError('operator not recognized for type detection. ({})'
                                             .format(self.inputs[1].op))
                    else:
                        typeeval = self.inputs[1].value
                else:
                    typeeval = self.inputs[0].value
            if self.op in ('ADD', 'SUBTRACT'):
                if type(typeeval) in (float, int):  # value
                    node = nodetree.nodes.new('ShaderNodeMath')
                    in_a = self.inputs[0].export(nodetree)
                    in_b = self.inputs[1].export(nodetree)
                    node.operation = self.op
                    nodetree.links.new(in_a, node.inputs[0])
                    nodetree.links.new(in_b, node.inputs[1])

                if type(typeeval) == Color:
                    node = nodetree.nodes.new('ShaderNodeMixRGB')
                    in_a = self.inputs[0].export(nodetree)
                    in_b = self.inputs[1].export(nodetree)
                    node.blend_type = self.op
                    node.inputs[0].default_value = 1.0  # make sure the factor is 1
                    nodetree.links.new(in_a, node.inputs[1])
                    nodetree.links.new(in_b, node.inputs[2])

                if type(typeeval) == Vector:
                    node = nodetree.nodes.new('ShaderNodeVectorMath')
                    node.operation = self.op
                    if self.inputs[0].type != 'val':  # vector values doesn't exist here
                        in_a = self.inputs[0].export(nodetree)
                        nodetree.links.new(in_a, node.inputs[0])
                    else:
                        node.inputs[0].default_value[0] = self.inputs[0].value.x
                        node.inputs[0].default_value[1] = self.inputs[0].value.y
                        node.inputs[0].default_value[2] = self.inputs[0].value.z
                    if self.inputs[1].type != 'val':
                        in_b = self.inputs[1].export(nodetree)
                        nodetree.links.new(in_b, node.inputs[1])
                    else:
                        node.inputs[1].default_value[0] = self.inputs[1].value.x
                        node.inputs[1].default_value[1] = self.inputs[1].value.y
                        node.inputs[1].default_value[2] = self.inputs[1].value.z

            elif self.op == 'MULTIPLY':  # vector multiplication is more difficult: need to do it with RGB

                if type(typeeval) in (float, int):  # value
                    node = nodetree.nodes.new('ShaderNodeMath')
                    in_a = self.inputs[0].export(nodetree)
                    in_b = self.inputs[1].export(nodetree)
                    node.operation = self.op
                    nodetree.links.new(in_a, node.inputs[0])
                    nodetree.links.new(in_b, node.inputs[1])

                if type(typeeval) == Color:
                    node = nodetree.nodes.new('ShaderNodeMixRGB')
                    in_a = self.inputs[0].export(nodetree)
                    in_b = self.inputs[1].export(nodetree)
                    node.blend_type = self.op
                    node.inputs[0].default_value = 1.0  # make sure the factor is 1
                    nodetree.links.new(in_a, node.inputs[1])
                    nodetree.links.new(in_b, node.inputs[2])

                if type(typeeval) == Vector:  # need color mix to multiply vectors
                    node = nodetree.nodes.new('ShaderNodeMixRGB')
                    node.blend_type = self.op
                    node.inputs[0].default_value = 1
                    if self.inputs[0].type != 'val' or type(self.inputs[0].value) == str:
                        # vector values doesn't exist here
                        in_a = self.inputs[0].export(nodetree)
                        nodetree.links.new(in_a, node.inputs[1])
                    else:
                        node.inputs[1].default_value[0] = self.inputs[0].value.x
                        node.inputs[1].default_value[1] = self.inputs[0].value.y
                        node.inputs[1].default_value[2] = self.inputs[0].value.z
                    if self.inputs[1].type != 'val' or type(self.inputs[1].value) == str:
                        in_b = self.inputs[1].export(nodetree)
                        nodetree.links.new(in_b, node.inputs[2])
                    else:
                        node.inputs[2].default_value[0] = self.inputs[1].value.x
                        node.inputs[2].default_value[1] = self.inputs[1].value.y
                        node.inputs[2].default_value[2] = self.inputs[1].value.z

            elif self.op == 'clamp':
                in_n = self.value.export(nodetree)
                if in_n.node.type in ('MATH', 'MIX_RGB'):
                    in_n.node.use_clamp = True
                    return in_n  # clamp can be done on previous nodes (for color and floats)
                else:  # need to add clamping node:
                    if in_n.type == 'VALUE':  # treat floats
                        node = nodetree.nodes.new('ShaderNodeMath')
                        node.operation = 'ADD'  # add zero to clamp
                        node.use_clamp = True
                        node.inputs[1].default_value = 0.0

                        nodetree.links.new(in_n, node.inputs[0])  # link with other node
                    else:  # treat color or vector
                        node = nodetree.nodes.new('ShaderNodeMixRGB')
                        node.blend_type = 'ADD'  # add zero to clamp
                        node.use_clamp = True
                        node.inputs[0].default_value = 1.0  # add fully

                        node.inputs[2].default_value[0] = 0.0  # add zero
                        node.inputs[2].default_value[1] = 0.0
                        node.inputs[2].default_value[2] = 0.0

                        nodetree.links.new(in_n, node.inputs[1])  # link with other node

            elif self.op == 'mixC':
                in_n = self.value.export(nodetree)
                if self.value.type == 'val':
                    if self.value.value in (Color((0,0,0)), Vector((0,0,0))):
                        return self.inputs[0].export(nodetree)
                    elif self.value.value in (Color((1,1,1)), Vector((1,1,1))):
                        return self.inputs[1].export(nodetree)
                if in_n.node.type == 'COMBRGB' and False:  # use it PLZ
                    pass
                else:
                    nodegroup = get_mixgroup('C')
                    node = nodetree.nodes.new('ShaderNodeGroup')
                    node.node_tree = nodegroup

                    nodetree.links.new(in_n, node.inputs[0])
                    nodetree.links.new(self.inputs[0].export(nodetree), node.inputs[1])
                    nodetree.links.new(self.inputs[1].export(nodetree), node.inputs[2])

            elif self.op == 'mixA':
                if self.value.type == 'val':
                    if self.value.value == 0.0:
                        return self.inputs[0].export(nodetree)
                    elif self.value.value == 1.0:
                        return self.inputs[1].export(nodetree)

                in_n = self.value.export(nodetree)

                nodegroup = get_mixgroup('A')
                node = nodetree.nodes.new('ShaderNodeGroup')
                node.node_tree = nodegroup

                nodetree.links.new(in_n, node.inputs[0])
                nodetree.links.new(self.inputs[0].export(nodetree), node.inputs[1])
                nodetree.links.new(self.inputs[1].export(nodetree), node.inputs[2])




            elif self.op in ('get_3r', 'get_3g', 'get_3b'):
                channelid = ['r','g','b'].index(self.op[-1])
                in_n = nodetree.nodes.new('ShaderNodeSeparateRGB')
                nodetree.links.new(self.value.export(nodetree), in_n.inputs[0])
                node = nodetree.nodes.new('ShaderNodeCombineRGB')
                nodetree.links.new(in_n.outputs[channelid], node.inputs[0])
                nodetree.links.new(in_n.outputs[channelid], node.inputs[1])
                nodetree.links.new(in_n.outputs[channelid], node.inputs[2])

            elif self.op in ('get_r', 'get_g', 'get_b'):
                channelid = ['r', 'g', 'b'].index(self.op[-1])
                in_n = nodetree.nodes.new('ShaderNodeSeparateRGB')
                nodetree.links.new(self.value.export(nodetree), in_n.inputs[0])
                return in_n.outputs[channelid]

            elif self.op == 'triple':
                in_n = self.value.export(nodetree)
                node = nodetree.nodes.new('ShaderNodeCombineRGB')
                nodetree.links.new(in_n, node.inputs[0])
                nodetree.links.new(in_n, node.inputs[1])
                nodetree.links.new(in_n, node.inputs[2])

            elif self.op in ('texture_color', 'texture_alpha', 'texture_3alpha'):  # no need for 3alpha?
                method = ['alpha', 'color'].index(self.op[-5:])
                texture = newtex_tex(self.inputs[0].name)
                texnode = nodetree.nodes.new('ShaderNodeTexture')
                texnode.texture = texture
                uv_vect = self.value.export(nodetree)
                # XCX image mapping (clamp, mirror)
                if self.inputs[0].mirrorS or self.inputs[0].mirrorT:
                    r_fct = 1
                    g_fct = 1
                    if self.inputs[0].mirrorS:
                        r_fct = 0.5
                        texture.repeat_x = 2
                        texture.use_mirror_x = True
                    if self.inputs[0].mirrorT:
                        g_fct = 0.5
                        texture.repeat_y = 2
                        texture.use_mirror_y = True
                    multnode = nodetree.nodes.new('ShaderNodeMixRGB')
                    multnode.inputs[2].default_value[0] = r_fct
                    multnode.inputs[2].default_value[1] = g_fct
                    multnode.inputs[2].default_value[2] = 0
                    multnode.inputs[0].default_value = 1
                    multnode.blend_type = 'MULTIPLY'
                    nodetree.links.new(uv_vect, multnode.inputs[1])
                    if self.inputs[0].mirrorT:  # scale done around (0,1)
                        addnode = nodetree.nodes.new('ShaderNodeMixRGB')
                        addnode.blend_type = 'SUBTRACT'
                        addnode.inputs[0].default_value = 1
                        addnode.inputs[1].default_value[0] = 0
                        addnode.inputs[1].default_value[1] = 1.5
                        addnode.inputs[1].default_value[2] = 0
                        nodetree.links.new(multnode.outputs[0], addnode.inputs[2])
                        nodetree.links.new(addnode.outputs[0], texnode.inputs[0])
                    else:
                        nodetree.links.new(multnode.outputs[0], texnode.inputs[0])

                else:
                    nodetree.links.new(uv_vect, texnode.inputs[0])
                return texnode.outputs[method]

        return node.outputs[0]  # default


class Sampler:
    def __init__(self, name):
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


class MaterialSpace:
    """holds reused variables for code->node system conversion"""
    def __init__(self):
        self.finalcolorc = Holder(Node(data=Color()))
        self.finalcolora = Holder(Node(data=0.0))
        self.vertexcolorc = Holder(Node(data=Color()))
        self.vertexcolora = Holder(Node(data=0.0))
        self.reg1c = Holder(Node(data=Color()))
        self.reg1a = Holder(Node(data=0.0))
        self.reg2c = Holder(Node(data=Color()))
        self.reg2a = Holder(Node(data=0.0))
        self.reg3c = Holder(Node(data=Color()))
        self.reg3a = Holder(Node(data=0.0))

        self.texcoords = []
        self.vcolorindex = 0

        self.textures = [None]*8

        self.konsts = [None]*8

        self.flag = 0  # scenegraph use

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

    def getTexAccess(self, info, type):
        return Node(op='texture_'+type, data=self.texcoords[info.texCoordId], inputs=(self.textures[info.texMap],))

    def getRasColor(self, info):
        return self.vertexcolorc.data, self.vertexcolora.data
        # return self.vertexcolorc, self.vertexcolora
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

    def getColorIn(self, op, konst, info):
        if op <= 7:
            if op % 2:
                return Node('triple', self.getRegFromId(op//2)[1].data)
            else:
                return self.getRegFromId(op//2)[0].data
        elif op == 8:
            return self.getTexAccess(info, 'color')
        elif op == 9:
            return Node('triple', self.getTexAccess(info, 'alpha'))
            # XCX are you sure that alpha channel can be used like that?
        elif op == 10:
            return self.getRasColor(info)[0]
        elif op == 11:
            return Node('triple', self.getRasColor(info)[1])
        elif op == 12:
            return Node(data=Color((1,1,1)))
        elif op == 13:
            return Node(data=Color((0.5, 0.5, 0.5)))
        elif op == 14:
            if konst <= 7:
                val = (8-konst)/8
                return Node(data=Color((val,val,val)))
            elif konst < 0xc:
                print("getColorOp(): unknown konst", hex(konst))
                return Node(data=Color((1,0,0)))

            konst -= 0xc
            var = self.konsts[(konst % 4)*2]
            if konst//4 == 4:  # triple alpha
                return Node('triple', self.konsts[(konst % 4)*2+1])
            elif konst//4 == 0:
                return var
            elif konst//4 == 1:
                return Node('get_3r', var)
            elif konst//4 == 2:
                return Node('get_3g', var)
            elif konst//4 == 3:
                return Node('get_3b', var)
        else:
            if op != 15:
                print("Unknown colorIn", op)
            return Node(data=Color((0, 0, 0)))

    def getAlphaIn(self, op, konst, info):
        if op <= 3:
            if self.getRegFromId(op)[1].data is None:
                pass
            return self.getRegFromId(op)[1].data
        elif op == 4:
            if self.getTexAccess(info, 'alpha') is None:
                pass
            return self.getTexAccess(info, 'alpha')
        elif op == 5:
            if self.getRasColor(info)[1] is None:
                pass
            return self.getRasColor(info)[1]
        elif op == 6:
            if konst <= 7:
                return Node(data=(8-konst)/8)
            elif konst < 0x10:
                print("getColorOp(): unknown konst", hex(konst))
                return Node(data=0.0)
            konst -= 0x10
            var = self.konsts[(konst % 4) * 2]
            if konst // 4 == 3:  # alpha
                return self.konsts[(konst % 4) * 2 + 1]
            elif konst // 4 == 0:
                return Node('get_r', var)
            elif konst // 4 == 1:
                return Node('get_g', var)
            elif konst // 4 == 2:
                return Node('get_b', var)
        elif op == 7:
            return Node(data=0.0)
        else:
            raise ValueError('undefined OP')

    def getMods(self, dest, bias, scale, clamp, type):
        if bias == 0:
            ret = dest
        elif bias <= 2:
            if bias == 2:
                val = -0.5
            else:
                val = 0.5
            if type == 1:
                ret = Node(data=Color((val, val, val)))
            else:
                ret = Node(data=val)
            ret = dest + ret
        else:
            print("getMods(): unknown bias", bias)
            if type == 1:
                ret = Node(data=Color((0,0,0)))
            else:
                ret = Node(data=0)

        if scale == 0:
            pass
        elif scale == 1:
            ret *= (Node('triple', Node(data=2)), 2)[type]  # auto select type
        elif scale == 2:
            ret *= (Node('triple', Node(data=4)), 4)[type]
        elif scale == 3:
            ret *= (Node('triple', Node(data=0.5)), 0.5)[type]
        else:
            print("getMods(): unknown scale", scale)

        if clamp:
            ret = Node('clamp', ret)

        return ret

    def getOp(self, op, bias, scale, clamp, regId, ins, type):

        dest = self.getRegFromId(regId)[type]

        if op in (0,1):
            if type==0:  #color
                dest.data = Node('mixC', ins[2], (ins[0], ins[1]))
            else:  # alpha
                dest.data = Node('mixA', ins[2], (ins[0], ins[1]))
            if op == 0:
                dest.data = ins[3] + dest.data
            else:
                dest.data = ins[3] - dest.data
                print("getOp(): op 1 might not work")

            dest.data = self.getMods(dest.data, bias, scale, clamp, type)
            return

        elif op >= 8 and op <= 0xd:
            if type == 0:
              # out << "  if("

                temp = ins[0]

                if op in (8,9):
                    temp = Node('get_r', temp)
                elif op in (0xa,0xb):
                    temp = Node('dot', inputs=(Node('get_rg',temp),
                                               Node(data=Vector((255.0/65535.0, 255.0*256.0/65535.0, 0))) ))
                elif op in (0xc, 0xd):
                    temp = Node('dot', inputs=(temp, Node(Vector((255.0/16777215.0,
                                                                  255.0*256.0/16777215.0,
                                                                  255.0*65536.0/16777215.0))) ))

                temp2 = ins[0]

                if op in (8, 9):
                    temp2 = Node('get_r', temp)
                elif op in (0xa, 0xb):
                    temp2 = Node('dot', inputs=(Node('get_rg', temp),
                                               Node(data=Vector((255.0 / 65535.0, 255.0 * 256.0 / 65535.0, 0)))))
                elif op in (0xc, 0xd):
                    temp2 = Node('dot', inputs=(temp, Node(Vector((255.0 / 16777215.0,
                                                                  255.0 * 256.0 / 16777215.0,
                                                                  255.0 * 65536.0 / 16777215.0)))))

                # if(op%2 == 0) out << "temp > temp2";
                # else out << "temp == temp2";  # XCX this is not working yet

                #out << ")\n    " << dest << " = " << ins[2] << ";\n"
                #    << "  else\n    " << dest << " = " << ins[3] << ";\n";

                #out << getMods(dest, 0, scale, clamp, type);
                if(bias != 3 or scale != 1 or clamp != 1):
                   print("getOp() comp0: unexpected bias %d, scale %d, clamp %d"% (bias, scale, clamp))

                dest.data=None
                return

            else:  # (type==1)
                pass  # TODO: need2fix

        elif op in (0xe, 0xf):
            if type == 1:
                #out << "  if(" << ins[0];
                #if(op == 0xe):
                #    out << " > ";
                #else:
                #    out << " == ";
                #out << ins[1] << ")\n    " << dest << " = " << ins[2] << ";\n"
                #    << "  else\n    " << dest << " = " << ins[3] << ";\n";

                # out << getMods(dest, 0, scale, clamp, type)
                if bias != 3 or scale != 1 or clamp != 1:
                  print("getOp() comp0: unexpected bias %d, scale %d, clamp %d" % (bias, scale, clamp))

                return
            # //TODO: gnd.bdl uses 0xe on type == 0

        else:
            print("getOp(): unsupported op", op)
            if type == 0:
              dest.data = None  # " = vec3(0., 1., 0.); //(unsupported)";
            else:
              dest.data = None  # " = 0.5; //(unsupported)";
            return

    # this is a transfer function to create blender nodes
    def export(self, nodetree):
        # first, delete existing nodes
        while len(nodetree.nodes):
            nodetree.nodes.remove(nodetree.nodes[0])

        # then, create output and matertial nodes
        out_node = nodetree.nodes.new('ShaderNodeOutput')
        mat_node = nodetree.nodes.new('ShaderNodeMaterial')
        mat_node.material = get_dumb_material()

        # link them
        nodetree.links.new(mat_node.outputs[0], out_node.inputs[0])  # material:out_color -> output:color

        # create alpha and link
        alnode = self.finalcolora.data.export(nodetree)
        # converter = nodetree.nodes.new('ShaderNodeRGBToBW')
        #nodetree.links.new(alnode, converter.inputs[0])
        #nodetree.links.new(converter.outputs[0], out_node.inputs[1])
        nodetree.links.new(alnode, out_node.inputs[1])
        # node:out_alpha -> output:alpha

        # create color and link
        colnode = self.finalcolorc.data.export(nodetree)

        nodetree.links.new(colnode, mat_node.inputs[0])  # node:out_color -> material:diffuse


def writeTexGen(material, texGen, i, matbase, mat3):
    while len(material.texcoords) <= i:
        material.texcoords.append(None)
    dst = Node(data=1)

    if texGen.texGenType in (0, 1):
        if texGen.matrix == 0x3c:
            pass  # no texture matrix
        elif (texGen.matrix >= 0x1e and texGen.matrix <= 0x39):
            dst = Node(data=1)  #(texGen.matrix - 0x1e)/3)  # XCX get the right matrix
            # XCX trap: do not set this node with this value: act as multiplier right now
        else:
            print("writeTexGen() type "+str(texGen.texGenType)+": unsupported matrix"+hex(texGen.matrix))

        if (texGen.texGenSrc >=4 and texGen.texGenSrc <=11):
            dst = dst*Node(data='uv'+str(texGen.texGenSrc-4))
        elif texGen.texGenSrc == 0:
            print("writeTexGen() type 0: Found src 0, might not yet work (use transformed or untransformed pos?)")
            dst = dst*Node(data='pos')
        elif texGen.texGenSrc == 1:
            print("writeTexGen() type 0: Found src 1, might not yet work (use transformed or untransformed normal?)")
            dst = dst*Node(data='nor')
        else:
            print("writeTexGen() type %d: unsupported src 0x%x", texGen.texGenType, texGen.texGenSrc)
            dst = Node(data=Vector((0,0,0)))  # "null" vector

        # dirty hack(doesn't work with animations for example) (TODO):

        # try if texcoord scaling is where i think it is
        if matbase.texMtxInfos[i] != 0xffff:
            tmi = mat3.texMtxInfos[matbase.texMtxInfos[i]]
            dst = dst*Node(data=Vector((tmi.scaleU, tmi.scaleV, 1)))
            dst = dst+Node(data=Vector((tmi.scaleCenterX*(1 - tmi.scaleU),
                                        (1 - tmi.scaleCenterY) * (1 - tmi.scaleV), 0)))

    elif texGen.texGenType == 0xa:
        if (texGen.matrix != 0x3c):
            print("writeTexGen() type 0xa: unexpected matrix", hex(texGen.matrix))
        if (texGen.texGenSrc != 0x13):
            print("writeTexGen() type 0xa: unexpected src", hex(texGen.texGenSrc))

        print("writeTexGen(): Found type 0xa (SRTG), doesn't work right yet")

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
        print("writeTexGen: unsupported type", hex(texGen.texGenType))
        #out << "  " << dest << " = vec4(0.0, 0.0, 0.0, 0.0); //(unsupported texgentype)\n"

    material.texcoords[i] = dst


def createMaterialSystem(index, mat3, tex1, texpath):
    # ## vertex shader part: ###########
    currMat = mat3.materialbases[index]
    material = MaterialSpace()
    if currMat.chanControls[0] < len(mat3.colorChanInfos):
        if __name__ == '__main__':
            if mat3.colorChanInfos[currMat.chanControls[0]].matColorSource != 1:
                material.vcolorindex = 1

    # missing light enabeling, seems so.
    if mat3.colorChanInfos[currMat.chanControls[0]].matColorSource == 1:
        material.vertexcolorc.data = Node(data='VcolorC')
        material.vertexcolora.data = Node('get_r', Node(data='VcolorA'))
    else:
        c = mat3.color1[currMat.color1[0]]
        material.vertexcolorc.data = Node(data=Color((c.r/255, c.g/255, c.b/255)))
        material.vertexcolora.data = Node(data=c.a/255)
    if mat3.colorChanInfos[currMat.chanControls[0]].litMask:
        material.vertexcolorc.data = material.vertexcolorc.data * Color((0.5, 0.5, 0.5))
        # material.vertexcolora.data = material.vertexcolora.data * 0.5
        # if currMat.color2[0] != 0xffff and currMat.color2[0] < len(mat3.color2):
        #     amb = mat3.color2[currMat.color2[0]]

    for i in range(mat3.texGenCounts[currMat.texGenCountIndex]):  # num TexGens == num Textures
        writeTexGen(material, mat3.texGenInfos[currMat.texGenInfos[i]], i, currMat, mat3)

    # ## fragment shader part
    for i in range(8):
        if currMat.texStages[i] != 0xffff:
            texId = mat3.texStageIndexToTextureIndex[currMat.texStages[i]]
            currTex =tex1.texHeaders[texId]
            material.textures[i] = Sampler(texpath+tex1.stringtable[texId]+'.tga')
            material.textures[i].setTexWrapMode(currTex.wrapS, currTex.wrapT)  # XCX set min/mag filters

    # konst colors
    needK = [False]*4
    for i in range(mat3.tevCounts[currMat.tevCountIndex]):
        konstColor = currMat.constColorSel[i]
        konstAlpha = currMat.constAlphaSel[i]
        stage = mat3.tevStageInfos[currMat.tevStageInfo[i]]

        if (konstColor > 7 and konstColor < 0xc
           or konstAlpha > 7 and konstAlpha < 0x10):
            print("createFragmentShaderString: Invalid color sel")
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
            c = mat3.color3[currMat.color3[i]]
            material.konsts[2*i] = Node(data=Color((c.r/255, c.g/255, c.b/255)))
            material.konsts[2*i+1] = Node(data=c.a/255)

    needReg = [False]*4
    for i in range(mat3.tevCounts[currMat.tevCountIndex]):
        stage = mat3.tevStageInfos[currMat.tevStageInfo[i]]
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
                c = mat3.colorS10[currMat.colorS10[3]]
            else:
                c = mat3.colorS10[currMat.colorS10[i-1]]
            material.getRegFromId(i)[0].data = Node(data=Color((c.r/255, c.g/255, c.b/255)))
            material.getRegFromId(i)[1].data = Node(data=c.a/255)

    for i in range(mat3.tevCounts[currMat.tevCountIndex]):
        order = mat3.tevOrderInfos[currMat.tevOrderInfo[i]]
        stage = mat3.tevStageInfos[currMat.tevStageInfo[i]]

        colorIns = [None]*4
        for j in range(4):
            colorIns[j] = material.getColorIn(stage.colorIn[j], currMat.constColorSel[i], order)

        material.getOp(stage.colorOp, stage.colorBias, stage.colorScale,
                       stage.colorClamp, stage.colorRegId, colorIns, 0)

        alphaIns = [None]*4
        for j in range(4):
            alphaIns[j] = material.getAlphaIn(stage.alphaIn[j], currMat.constAlphaSel[i], order)

        print(end='')
        material.getOp(stage.alphaOp, stage.alphaBias, stage.alphaScale,
                       stage.alphaClamp, stage.alphaRegId, alphaIns, 1)

    return material


MIX_GROUP_NODETREE_C = None
MIX_GROUP_NODETREE_A = None
def get_mixgroup(type):
    global MIX_GROUP_NODETREE_C
    global MIX_GROUP_NODETREE_A
    if type == 'C':

        if MIX_GROUP_NODETREE_C is None:
            MIX_GROUP_NODETREE_C = gnt = bpy.data.node_groups.new('glsl_mix', 'ShaderNodeTree')
            in_n = gnt.nodes.new('NodeGroupInput')
            out_n = gnt.nodes.new('NodeGroupOutput')  # creating real input and output nodes
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

DUMB_MAT = None
def get_dumb_material():
    global DUMB_MAT
    if DUMB_MAT is None:
        DUMB_MAT = bpy.data.materials.new('dumb material (used for nodes)')
    return DUMB_MAT