#! /usr/bin/python3
if "bpy" in locals():  # trick to reload module on f8-press in blender
    LOADED = True
else:
    LOADED = False

from importlib import reload
from array import array
import os

import bpy
from mathutils import Matrix, Vector, Euler
import logging
log = logging.getLogger('bpy.ops.import_mesh.bmd.main')

if LOADED:
    for module in (BinaryReader, BinaryWriter, Mat44, Inf1, Vtx1, Shp1, Jnt1, Evp1, Drw1,
                   Bck, Mat3, Tex1, Mdl3, Btp, common, TexH, MatH, PBones):
        reload(module)

else:
    from . import (
        BinaryReader, BinaryWriter,
        Matrix44 as Mat44,
        Inf1, Vtx1, Shp1, Jnt1, Evp1, Drw1, Bck, Tex1, Btp, Mdl3, Mat3,
        common,
        texhelper as TexH,
        materialhelper as MatH,
        pseudobones as PBones
    )

del LOADED


class LoopRepresentation:
    def __init__(self):
        self.vertex = -1
        self.UVs = [None]*8
        self.VColors = [None]*2
        self.normal = None
        self.mm = -1  # reference to the multimatrix entry used to move the point

    # def __eq__(self, other):
    #    return self.vertex == other.vertex and \
    #           self.UVs == other.UVs and \
    #           self.VColors == other.VColors and \
    #           self.normal == other.normal


class FaceRepresentation:
    def __init__(self):
        self.loop_start = -1
        self.material = None


class ModelRepresentation:
    def __init__(self):
        self.vertices = []
        self.faces = []
        self.loops = []
        self.hasTexCoords = [False]*8  # will be set to true if necessary
        self.hasColors = [False]*2
        self.hasMatrixIndices = False
        self.hasNormals = False

        self.dedup_verts = {} # {original_id: (new ids)}
        # some faces might reference the same vert multiple times:
        # for this (somewhat dumb and corner-case) occasion,
        # "cloned" verts must be kept.

    def toarray(self, type):
        if type == 'co':
            ret = array('f', [0.0]*3*len(self.vertices))
            if common.GLOBALS.no_rot_conversion:
                for num, com in enumerate(self.vertices):
                    ret[3*num] = com.x
                    ret[3*num+1] = com.y
                    ret[3*num+2] = com.z
            else:
                for num, com in enumerate(self.vertices):
                    ret[3*num] = com.x
                    ret[3*num+1] = -com.z
                    ret[3*num+2] = com.y
        elif type == 'loop_start':
            ret = array('i')
            for com in self.faces:
                ret.append(com.loop_start)
        elif type == 'normal':
            ret = array('f', [0.0] * 3 * len(self.loops))
            if common.GLOBALS.no_rot_conversion:
                for num, com in enumerate(self.loops):
                    if com.normal is None:
                        ret[3*num] = ret[3*num+1] = ret[3*num+2] = 0
                    else:
                        ret[3 * num] = com.normal.x
                        ret[3 * num + 1] = com.normal.y
                        ret[3 * num + 2] = com.normal.z
            else:
                for num, com in enumerate(self.loops):
                    if com.normal is None:
                        ret[3*num] = ret[3*num+1] = ret[3*num+2] = 0
                    else:
                        ret[3 * num] = com.normal.x
                        ret[3 * num + 1] = -com.normal.z
                        ret[3 * num + 2] = com.normal.y
        elif type == 'v_indexes':
            ret = array('i')
            for com in self.loops:
                ret.append(com.vertex)
        else:
            raise ValueError('wrong array type')

        return ret

    def getLoop(self, faceidx, i):
        assert 0 <= i <= 2
        return self.loops[self.faces[faceidx].loop_start + i]

    def getLoops(self, faceidx):
        return (self.loops[self.faces[faceidx].loop_start],
                self.loops[self.faces[faceidx].loop_start+1],
                self.loops[self.faces[faceidx].loop_start+2])

    def getVerts(self, faceidx):
        l1 = self.faces[faceidx].loop_start
        return (self.loops[l1].vertex,
                self.loops[l1+1].vertex,
                self.loops[l1+2].vertex)


class BModel:
    """# <variable _boneThickness>
    # <variable inf>
    # <variable vtx>
    # <variable shp>
    # <variable jnt>
    # <variable evp>
    # <variable drw>
    # <variable _mat1>
    # <variable tex>
    # <variable _bmdViewPathExe>
    # <variable _bones>
    # <variable _iconSize>
    # <variable _currMaterialIndex>
    # <variable _currMaterial>
    # <variable _texturePath>
    # <variable _texturePrefix>
    # <variable _bckPaths>
    # <variable _bmdFilePath>
    # <variable _bmdDir>
    # <variable _bmdFileName>
    # <variable _createBones>
    # <variable _loadAnimations>
    # <variable vertices>
    # <variable faces>
    # <variable tverts>
    # <variable tFaces>
    # <variable normals>
    # <variable vcFaces>
    # -- vertex color
    # <variable vertexMultiMatrixEntry>
    # <variable _materialIDS>
    # <variable _subMaterials>
    # <variable _parentBoneIndexs>
    # -- doesn't work on characters? required for stages?
    # <variable _forceCreateBones>
    # <variable _exportType>
    # -- #XFILE, #CHARACTER
    # <variable _runExtractTexturesCmd>
    # <variable _includeScaling>
    # <variable _reverseFaces>
    # -- required for .x export (render eyeraises before face)
    # <function>


    # <function>

    # <function>

    # <function>

    # <function>

    # <function>

    # <function>

    # <function>

    # --newVertIndex = 1,
    # <variable faceIndex>
    # <function>

    # <function>

    # -- create frame nodes and setup jnt.matrices
    # <function>

    # <function>

    # <function>

    # <function>

    # <function>

    # <function>

    # <function>"""

    def __init__(self):  # GENERATED!
        self.vtx = None
        self.DEBUGvgroups = {}
        self._bmdFilePath = ""
        self._runExtractTexturesCmd = True
        self._currMaterialIndex = 0
        self.tverts = [[], [], [], [], [], [], [], []]  # texture vertices
        self._bones = []
        self._bckPaths = []
        self._btpPaths = []
        self.faceIndex = 0
        self._materialIDS = []
        self.vertexMultiMatrixEntry = []
        self.normals = []
        self._subMaterials = []

    def SetBmdViewExePath(self, value):
        self._bmdViewPathExe = value


    def BuildSingleMesh(self):
        # -----------------------------------------------------------------
        # -- mesh
        log.debug('BuildSMesh point reached')
        """if False:  #self._reverseFaces and False:
            self.model.faces = ReverseArray(self.model.faces)
            self._materialIDS = ReverseArray(self._materialIDS)
            #for com in range(len(self._materialIDS)):
            #    self._materialIDS[com] = len(self._subMaterials)-1-self._materialIDS[com]
            for uv in range(8):
                self.tFaces[uv] = ReverseArray(self.tFaces[uv])
                for num, com in enumerate(self.tv_to_f_v[uv]):
                    for num2, com2 in enumerate(com):
                        com2 = (len(self.model.faces)-1-com2[0], com2[1])
                        com[num2] = com2
                    self.tv_to_f_v[uv][num] = com
            # vertex colors are now similar to uv textures
            for cv in range(2):
                self.vcFaces[cv] = ReverseArray(self.vcFaces[cv])
                for num, com in enumerate(self.cv_to_f_v[cv]):
                    for num2, com2 in enumerate(com):
                        com2 = (len(self.model.faces)-1-com2[0], com2[1])
                        com[num2] = com2
                    self.cv_to_f_v[cv][num] = com"""

        # TODO: should never have undefined materials

        # adjust length of _materialIDS
        self._materialIDS += [None] * (len(self.model.faces) - len(self._materialIDS))

        for idx in range(len(self.model.vertices)):
            if self.model.vertices[idx] is None:
                self.model.vertices[idx] = self.vtx.positions[idx]  # XCX should not have to do this
                # vertices will be adapted in the toarray() cinverter

        modelMesh = bpy.data.meshes.new(common.getFilenameFile(self._bmdFilePath))
        modelMesh.vertices.add(len(self.model.vertices))
        modelMesh.vertices.foreach_set('co', self.model.toarray('co'))
        modelMesh.loops.add(len(self.model.loops))
        modelMesh.loops.foreach_set('vertex_index', self.model.toarray('v_indexes'))
        modelMesh.polygons.add(len(self.model.faces))
        modelMesh.polygons.foreach_set('loop_start', self.model.toarray('loop_start'))
        modelMesh.polygons.foreach_set('loop_total', array('i', [3]*len(self.model.faces)))

        modelMesh.update()
        modelObject = bpy.data.objects.new(common.getFilenameFile(self._bmdFilePath), modelMesh)
        bpy.context.collection.objects.link(modelObject)

        # XCX: find a way to replace that too.
        try:
            bm_to_pm = {}  # index shifter: material, get mat index
            for i in range(len(self._subMaterials)):
                MatH.add_material(modelObject, self._subMaterials[i])
            errmat = MatH.add_err_material(modelObject)
            for num, com in enumerate(modelObject.material_slots):
                bm_to_pm[com.material] = num
            for num, com in enumerate(self._materialIDS):  # assign materials to faces
                # DEBUG reversed index
                if com is not None:
                    modelMesh.polygons[num].material_index = com
                else:
                    modelMesh.polygons[num].material_index = bm_to_pm[errmat]
        except Exception as err:
            log.error('Materials couldn\'t be completely applied (error is %s)', err)

        active_uv = None

        for uv in range(8):
            if self.model.hasTexCoords[uv]:
                try:
                    TexH.newUVlayer(modelMesh, self.model, uv)
                except Exception as err:
                    log.error('Couldn\'t create UV layer %d (error is %s)', uv, err)
        try:
            active_uv = modelMesh.uv_layers[0]
        except Exception as err:
            pass  # it will be fixed later anyways

        with common.active_object(modelObject):
            if not active_uv:
                bpy.ops.paint.add_simple_uvs()
                active_uv = modelMesh.uv_layers[0]

            modelMesh.update()

            if self.model.hasColors[0]:
                # if len(self.vtx.colors) and len(self.vtx.colors[0]):  # has colors?
                try:
                    alpha_image = MatH.add_vcolor(modelMesh, self.model, 0)
                except Exception as err:
                    if self.params.PARANOID:
                        raise
                    else:
                        log.error('Vertex color layer 0 failed (error is %s)', err)
            if self.model.hasColors[1]:
                # if len(self.vtx.colors) > 1 and len(self.vtx.colors[1]):
                try:
                    MatH.add_vcolor(modelMesh, self.model, 1)
                except Exception as err:
                    log.error('Vertex color layer 1 failed (error is %s)', err)
        # update(modelMesh)

        # -----------------------------------------------------------------

        if self.params.createBones or self.params.DEBUGVG:
            try:
                with common.active_object(modelObject):
                    mod = modelObject.modifiers.new('Armature', type='ARMATURE')
                    arm = bpy.data.armatures.new(modelObject.name+'_bones')
                    self.arm_obj = arm_obj = bpy.data.objects.new(modelObject.name+'_armature', arm)
                    bpy.context.collection.objects.link(arm_obj)
                    modelObject.parent = arm_obj
                    mod.object = arm_obj
                    bpy.context.view_layer.update()

                with common.active_object(arm_obj):

                    bpy.ops.object.mode_set(mode='EDIT')
                    for bone in self._bones:
                        arm.edit_bones.new(bone.name.fget())
                        # create ALL bones before starting referencing them
                    for bone in self._bones:
                        realbone = arm.edit_bones[bone.name.fget()]
                        if isinstance(bone.parent.fget(), PBones.Pseudobone):
                            realbone.parent = arm.edit_bones[bone.parent.fget().name.fget()]
                        
                        realbone.head.xyz = bone.position.xyz
                        if self.params.naturalBones and len(bone.children)==1:
                            realbone.tail.xyz = bone.children[0].position.xyz
                        else:
                            realbone.tail.xyz = bone.endpoint.xyz
                        # correct the bone rotation (or not)

                        if not self.params.no_rot_conversion:
                            realbone.head.xyz = realbone.head.xzy
                            realbone.head.y *= -1
                            realbone.tail.xyz = realbone.tail.xzy
                            realbone.tail.y *= -1
                        # TODO might need to fix this (vvv) for no_rot_conversion mode
                        realbone.align_roll(bone.get_z())  # get_z translates into blender coodrinates by itself
                        modelObject.vertex_groups.new(name=bone.name.fget())

                    if len(self.vertexMultiMatrixEntry) != len(self.model.vertices):
                        log.error("Faulty multimatrix skin interpolation")
                        raise ValueError("E")  # for now, this cannot be avoided
                    if self.params.createBones:
                        # XCX should not need this
                        for idx in range(len(self.vertexMultiMatrixEntry)):
                            if self.vertexMultiMatrixEntry[idx] is None:
                                self.vertexMultiMatrixEntry[idx] = Evp1.MultiMatrix()
                        for i in range(len(self.model.vertices)):
                            for num, vg_id in enumerate(self.vertexMultiMatrixEntry[i].indices):
                                modelObject.vertex_groups[vg_id].add([i], self.vertexMultiMatrixEntry[i].weights[num], 'REPLACE')

                        for bone in self._bones:
                            realbone = arm.edit_bones[bone.name.fget()]
                            vec = realbone.head
                            grp = modelObject.vertex_groups[bone.name.fget()]
                    for com in self.DEBUGvgroups.keys():  # DEBUG vertex groups to fix UVs
                        vg = modelObject.vertex_groups.new(name=com)
                        vg.add(self.DEBUGvgroups[com], 1, 'REPLACE')

                    bpy.context.view_layer.update()
                    bpy.ops.object.mode_set(mode='OBJECT')

            except Exception as err:
                log.error('Animation bones not created. Animtions will fail. (error is %s)', err)

        modelMesh.update()

        ### deal with normals

        try:
            modelMesh.create_normals_split()  # does this stabilize normals?

            for face in modelMesh.polygons:
                face.use_smooth = True  # loop normals have effect only if smooth shading

            # create custom data to write normals correctly?
            modelMesh.update()

            # begin not understood black box (where does this thing write to make normals stable?)
            clnors = self.model.toarray('normal')

            modelMesh.polygons.foreach_set("use_smooth", [True] * len(modelMesh.polygons))

            modelMesh.normals_split_custom_set(tuple(
                                                     zip(*(iter(clnors),) * 3)
                                                    ))
            modelMesh.use_auto_smooth = True
            #modelMesh.show_edge_sharp = True
            # end not understood black box

            if self.params.validate_mesh:
                ll = len(modelMesh.loops)
                fl = len(modelMesh.polygons)
                modelMesh.validate(clean_customdata=False)  # only validate now, if at all
                if ll != len(modelMesh.loops):
                    log.warning('mesh validation lost data! (%d loops, %d faces)',
                                len(modelMesh.loops)-ll, len(modelMesh.polygons)-fl)
        except Exception as err:
            log.error('Normals weren\'t set (error is %s)', err)
        modelMesh.update()

            
        return modelObject

    def LoadModel(self, filePath):
        """loads mesh data from file"""

        log.debug("Load : ")
        # -- load model
        br = BinaryReader.BinaryReader()
        br.Open(filePath)

        br.SeekSet(0x20)

        iSize = 0
        strTag = ""  # 4 characters

        self.inf = Inf1.Inf1()
        self.vtx = Vtx1.Vtx1()
        self.shp = Shp1.Shp1()
        self.jnt = Jnt1.Jnt1()
        self.evp = Evp1.Evp1()
        self.drw = Drw1.Drw1()
        self._mat1 = Mat3.Mat3()
        self.tex = Tex1.Tex1()
        self.mdl = Mdl3.Mdl3()

        while strTag != "TEX" and not br.is_eof():  # "TEX1 tag is the last one every time"
            br.SeekCur(iSize)
            streamPos = br.Position()
            if br.is_eof():
                break
            strTag = br.ReadFixedLengthString(3)
            _ = br.GetByte()
            iSize = br.ReadDWORD()

            print(strTag, chr(_))
            br.SeekSet(streamPos)
            if strTag == "INF":  #usually INF1
                self.inf.LoadData(br)
            elif strTag == "VTX":  # VTX1
                self.vtx.LoadData(br)
            elif strTag == "SHP":  # SHP1
                self.shp.LoadData(br)
            elif strTag == "JNT":  # JNT1
                self.jnt.LoadData(br)
            elif strTag == "EVP":  # EVP1
                self.evp.LoadData(br)
            elif strTag == "DRW":  # DRW1
                self.drw.LoadData(br)
            elif strTag == "MAT":  # MAT2, MAT3
                self._mat1.LoadData(br)
            elif strTag == "TEX":  # TEX1
                self.tex.LoadData(br)
            elif strTag == "MDL":  # MDL3
                self.mdl.LoadData(br)
            else:
                log.warning('Tag (%s) not recognized. Resulting mesh could be weird', strTag)
            br.SeekSet(streamPos)

        # self.tex.LoadData(br)  # why the heck would it be loaded twice?!
        br.Close()

    def DrawBatch(self, index, matIndex):
        """assigns material and compute faces, vertex color and UV assignation to a "batch" """
        currBatch = self.shp.batches[index]
        batchid = index

        if not currBatch.attribs.hasPositions:
            if self.params.PARANOID:
                raise ValueError("found batch without positions. cannot proceed further")
            else:
                log.error('A batch without position was found. skipping...')
                return

        for i in (0, 1):
            if currBatch.attribs.hasColors[i]:
                self.model.hasColors[i] = True
        for i in range(8):
            if currBatch.attribs.hasTexCoords[i]:
                self.model.hasTexCoords[i] = True
        if currBatch.attribs.hasMatrixIndices:
            self.model.hasMatrixIndices = True
        if currBatch.attribs.hasNormals:
            self.model.hasNormals = True
        else:
            log.warning('batch %d has no normal coordinates. Expect crash later on', index)

        matrixTable = []
        # there should NEVER be more than 20 matrices per packet imo...even 10 sound like a lot...
        isMatrixWeighted = []
        # pos?
        multiMatrixTable = []
        # should be same count as matrixTable
        maxWeightIndices = 0

        # XCX should only be done once
        for uv in range(8):  # copying vtx.texcoords into self.tverts
            if self.vtx.texCoords[uv] is not None:
                while len(self.tverts) <= uv:
                    self.tverts.append([])
                self.tverts[uv] = [None] * len(self.vtx.texCoords[uv])
                for i_temp in range(len(self.vtx.texCoords[uv])):
                    tvert = self.vtx.texCoords[uv][i_temp]
                    self.tverts[uv][i_temp] = (tvert.s, tvert.t)  # flip uv v element

        for packnum, currPacket in enumerate(currBatch.packets):
            Mat44.updateMatrixTable(self.evp, self.drw, self.jnt, currPacket,
                                    multiMatrixTable, matrixTable, isMatrixWeighted, self.params.includeScaling)

            # if no matrix index is given per vertex, 0 is the default.
            # otherwise, mat is overwritten later.
            mat = matrixTable[0]
            multiMat = multiMatrixTable[0]
            for primnum, currPrimitive in enumerate(currPacket.primitives):
                temp_normals = {}
                for m in range(len(currPrimitive.points)):
                    posIndex = currPrimitive.points[m].posIndex
                    if currBatch.attribs.hasMatrixIndices:
                        mat = matrixTable[(currPrimitive.points[m].matrixIndex//3)]
                        if currPrimitive.points[m].matrixIndex % 3:
                            log.warning("if (mod currPrimitive.points[m].matrixIndex 3) != 0 then " +
                                       str(currPrimitive.points[m].matrixIndex))  # XCX does it work for fans?
                        multiMat = multiMatrixTable[(currPrimitive.points[m].matrixIndex//3)]  # fixed

                    if currBatch.attribs.hasNormals:
                        temp_normals[currPrimitive.points[m].normalIndex] =\
                            self.vtx.normals[currPrimitive.points[m].normalIndex].copy()
                        temp_normals[currPrimitive.points[m].normalIndex].rotate(mat)

                    while len(self.vertexMultiMatrixEntry) <= posIndex:
                        self.vertexMultiMatrixEntry.append(None)
                    self.vertexMultiMatrixEntry[posIndex] = multiMat
                    newPos = mat@(self.vtx.positions[posIndex])
                    while len(self.model.vertices) <= posIndex:
                        self.model.vertices.append(None)
                    self.model.vertices[posIndex] = newPos.copy()

                # manage primitive type
                if currPrimitive.type == 0x98:
                    iterator = Vtx1.StripIterator(currPrimitive.points)
                    # GL_TRIANGLE_STRIP
                elif currPrimitive.type == 0xa0:
                    iterator = Vtx1.FanIterator(currPrimitive.points)
                    # GL_TRIANGLE_FAN
                else:
                    if self.params.PARANOID:
                        raise ValueError("unknown primitive type")
                    else:
                        log.warning('Unknown primitive %d', currPrimitive.type)
                for p0, p1, p2 in iterator:
                    posIndex0 = p0.posIndex
                    posIndex1 = p1.posIndex
                    posIndex2 = p2.posIndex

                    # vertex deduplication: if two of the `posIndex`es
                    # are the same, vertex clones must be introduced for stability
                    # (a polygon mustn't refer to the same vertex more than once)
                    if posIndex0==posIndex1:
                        if self.model.dedup_verts.get(posIndex0, None) is None:
                            self.model.vertices.append(self.model.vertices[posIndex0])
                            posIndex1 = len(self.model.vertices)-1
                            self.model.dedup_verts[posIndex0] = (posIndex1,)
                        else:
                            posIndex1 = self.model.dedup_verts[posIndex0][0]

                    if posIndex0==posIndex2:
                        if self.model.dedup_verts.get(posIndex0, None) is None:
                            self.model.vertices.append(self.model.vertices[posIndex0])
                            posIndex2 = len(self.model.vertices)-1
                            self.model.dedup_verts[posIndex0] = (posIndex2,)
                        else:
                            posIndex2 = self.model.dedup_verts[posIndex0][0]

                    # third vert deduplication might sound trickier because duplication
                    # might come from the original file but might also come from here,
                    # but in truth, the second case just means that
                    # the shared posIndex value is aready one of the vertex clones
                    if posIndex1==posIndex2:
                        if self.model.dedup_verts.get(posIndex1, None) is None:
                            self.model.vertices.append(self.model.vertices[posIndex1])
                            posIndex2 = len(self.model.vertices)-1
                            self.model.dedup_verts[posIndex1] = (posIndex2,)
                        else:
                            posIndex2 = self.model.dedup_verts[posIndex1][0]


                    if self.params.DEBUGVG:
                        tempvg = self.DEBUGvgroups.get(str(batchid), None)
                        if not tempvg:
                            tempvg = []
                            self.DEBUGvgroups[str(batchid)] = tempvg
                        tempvg.append(posIndex0)
                        tempvg.append(posIndex1)
                        tempvg.append(posIndex2)
                        tempvg = self.DEBUGvgroups.get(str(batchid)+','+str(packnum), None)
                        if not tempvg:
                            tempvg = []
                            self.DEBUGvgroups[str(batchid)+','+str(packnum)] = tempvg
                        tempvg.append(posIndex0)
                        tempvg.append(posIndex1)
                        tempvg.append(posIndex2)
                        tempvg = self.DEBUGvgroups.get(str(batchid)+','+str(packnum)+','+str(primnum), None)
                        if not tempvg:
                            tempvg = []
                            self.DEBUGvgroups[str(batchid)+','+str(packnum)+','+str(primnum)] = tempvg
                        tempvg.append(posIndex0)
                        tempvg.append(posIndex1)
                        tempvg.append(posIndex2)

                    face = FaceRepresentation()
                    loop_0 = LoopRepresentation()
                    loop_1 = LoopRepresentation()
                    loop_2 = LoopRepresentation()
                    self.model.faces.append(face)
                    self.model.loops.append(loop_0)
                    self.model.loops.append(loop_1)
                    self.model.loops.append(loop_2)
                    face.loop_start = self.model.loops.index(loop_0)

                    loop_0.vertex = posIndex0
                    loop_1.vertex = posIndex1
                    loop_2.vertex = posIndex2

                    # create texture-coordinates data for correct assignation (later)
                    for uv in range(8):
                        if currBatch.attribs.hasTexCoords[uv]:
                            loop_0.UVs[uv] = self.tverts[uv][p0.texCoordIndex[uv]]
                            loop_1.UVs[uv] = self.tverts[uv][p1.texCoordIndex[uv]]
                            loop_2.UVs[uv] = self.tverts[uv][p2.texCoordIndex[uv]]

                    # create normal assignation data
                    if currBatch.attribs.hasNormals:
                        loop_0.normal = temp_normals[p0.normalIndex].copy()
                        loop_1.normal = temp_normals[p1.normalIndex].copy()
                        loop_2.normal = temp_normals[p2.normalIndex].copy()
                        if loop_0.normal == Vector((0,0,0)):
                            loop_0.normal.xyz = (0,0,1)
                        if loop_1.normal == Vector((0,0,0)):
                            loop_1.normal.xyz = (0,0,1)
                        if loop_2.normal == Vector((0,0,0)):
                            loop_2.normal.xyz = (0,0,1)
                        loop_0.normal.normalize()
                        loop_1.normal.normalize()
                        loop_2.normal.normalize()


                    # materials
                    while len(self._materialIDS) <= self.faceIndex:
                        self._materialIDS.append(None)
                    face.material = matIndex
                    self._materialIDS[self.faceIndex] = matIndex

                    # vertex colors
                    for vc in (0, 1):
                        if currBatch.attribs.hasColors[vc]:
                            loop_0.VColors[vc] = self.vtx.colors[vc][p0.colorIndex[vc]]
                            loop_1.VColors[vc] = self.vtx.colors[vc][p1.colorIndex[vc]]
                            loop_2.VColors[vc] = self.vtx.colors[vc][p2.colorIndex[vc]]
                    self.faceIndex += 1

                # end if currPrimitive.type == 0x98
            # end for currPrimitive in currPacket.primitives
         # end for currPacket in currBatch.packets

    def CreateBones(self, sg, parentMatrix, parentBone):
        """creates bone hierarchy (FrameNodes) and apply matrices(jnt1.frames used to compute jnt1.matrices)"""
        effP = parentMatrix.copy()
        # fNode = parentBone
        bone = parentBone
        n = sg

        if n.type == 0x10:
            # --joint
            f = self.jnt.frames[n.index]  # fixed
            effP = parentMatrix @ f.getFrameMatrix()
            f.matrix = effP

            fstartPoint = parentMatrix @ f.t

            orientation = (Mat44.rotation_part(parentMatrix) @  # use rotation part of parent matrix
                            Euler((f.rx, f.ry, f.rz), 'XYZ').to_matrix().to_4x4())  # apply local rotation
            
            # the final blender bone orientation should be always "towards global Y"
            # this position might be achieved after Y-up -> Z-up conversion, if it happens.
            # define the pseudobone default orientation correctly (in Y-up space / BMD space)
            if self.params.no_rot_conversion:
                orientation = orientation @Vector((0, self.params.boneThickness, 0))
            else:
                orientation = orientation @Vector((0, 0, -self.params.boneThickness))

            bone = PBones.Pseudobone(parentBone, f, effP,
                                     fstartPoint,
                                     fstartPoint + orientation)
            bone.scale = (f.sx, f.sy, f.sz)

            bone.width = bone.height = self.params.boneThickness

        for com in sg.children:
            self.CreateBones(com, effP, bone)

        if parentBone is None:
            return bone

    def DrawScenegraph(self, sg, parentMatrix, onDown=True, matIndex=0):
        """create faces and assign UVs, Vcolors, materials"""

        effP = parentMatrix.copy()

        n = sg

        if n.type == 0x10:  # joint
            self.jnt.matrices[n.index] = Mat44.updateMatrix(self.jnt.frames[n.index], effP)  # XCX update matrix needed?
            effP = self.jnt.matrices[n.index]  # setup during CreateFrameNodes
            self.jnt.frames[n.index].incr_matrix = effP
        elif n.type == 0x11:  # build material

            matIndex = self._currMaterialIndex
            # assign index of the next material to the material index that will be applied to all children

            # build material
            try:
                mat = self._mat1.materialbases[self._mat1.indexToMatIndex[n.index]]
                # materials can be reused in a single file: cache them
                if mat.material:
                    self._currMaterial = mat.material[0].copy()
                    log.debug("material was cached")
                    # matIndex = mat.material[1]
                else:
                    if not self.params.use_nodes:
                        self._currMaterial = MatH.build_material_simple(
                            self._mat1.indexToMatIndex[n.index],
                            self._mat1, self.tex,
                            self._texturePath, '.' + self.params.imtype.lower(),
                            self.params,
                        )
                    else:
                        try:
                            self._currMaterial = MatH.build_material_v3(
                                self._mat1.indexToMatIndex[n.index],
                                self._mat1, self.tex,
                                self._texturePath, '.' + self.params.imtype.lower(),
                                self.params,
                            )
                        except Exception as err:

                            if self.params.PARANOID:
                                log.error('couldn\'t build material %d', matIndex)
                                raise
                            else:
                                log.error('node (GLSL) materials went wrong.'+
                                    'Falling back to incomplete materials.'+
                                    '(error is %s)', err)
                                self._currMaterial = MatH.build_material_simple(
                                    self._mat1.indexToMatIndex[n.index],
                                    self._mat1, self.tex,
                                    self._texturePath, '.' + self.params.imtype.lower(),
                                    self.params
                                )

            except Exception as err:
                log.error('Material not built correctly (error is %s)', err)
                if self.params.PARANOID:
                    raise
                self._currMaterial = None

                # keep the correct material indexes : include void material
                while self._currMaterialIndex >= len(self._subMaterials):
                    self._subMaterials.append(None)
                self._subMaterials[self._currMaterialIndex] = self._currMaterial
                self._currMaterialIndex += 1
            finally:
                onDown = (mat.flag == 1)


            if self._currMaterial is not None:  # mat.texStages[0] != 0xffff:  # do it if any texture has been made
                # XCX is that the good condition?
                self._currMaterial.name = self._mat1.stringtable[n.index]

                while self._currMaterialIndex >= len(self._subMaterials):
                    self._subMaterials.append(None)
                self._subMaterials[self._currMaterialIndex] = self._currMaterial
                self._currMaterialIndex += 1

        elif n.type == 0x12 and onDown:  # - type = 18
            self.DrawBatch(n.index, matIndex)  # fixed

        for com in sg.children:
            self.DrawScenegraph(com, effP, onDown, matIndex)  # -- note: i and j start at 1 instead of 0

        if n.type == 0x12 and not onDown:  # - type = 18
            self.DrawBatch(n.index, matIndex)  # fixed

        if n.type < 0x10 or n.type > 0x12:
            log.error("SceneGraph node has incorrect type. Might cause chaos.")

    def BuildScenegraph(self, sg, bone):
        sg.index = len(self._bones)
        self._bones.append(bone)
        for child in bone.children:
            childSG = Inf1.SceneGraph()
            sg.children.append(childSG)
            childSG.type = 0x10
            self.BuildScenegraph(childSG, child)

    def DrawScene(self):
        log.debug("DrawScene point reached")
        try:
            sg = self.inf.rootSceneGraph
            self.model = ModelRepresentation()
            rootBone = self.CreateBones(sg, Matrix.Identity(4), None)
            # remove dummy root bone:
            log.debug("frame node created")
            # -- FIX: Force create bone option allows to generate bones independently of their count
            if len(rootBone.children) == 1 and len(rootBone.children[0].children) == 0 and \
                                                                            not self.params.forceCreateBones:
                self.params.createBones = False
            origWorldBonePos = None
        except Exception as err:
            log.critical('Scenegraph (mesh description) is bad. stopping... (error is %s)', err)
            return

        if self.params.createBones:
            self._bones = rootBone.tree_to_array()

            origWorldBonePos = self._bones[0].position

            # -- easier than recalculating all bone transforms
            d = Vector()
            self._bones[0].parent.fset(d)
            if not self.params.no_rot_conversion:
                d.rotate(Euler((90, 0, 0), 'XZY'))
        i = Matrix.Identity(4)

        try:
            self.DrawScenegraph(sg, i)
        except Exception as err:
            log.critical('Mesh description in scene graph is nonsensical. (error is %s)', err)
            raise

        try:
            modelObj = self.BuildSingleMesh()
        except Exception as err:
            log.critical('mesh couldn\'t be built (error is %s)', err)
            raise

        if self.params.createBones and self.params.loadAnimations:
            self.LoadAnimations()

    def LoadAnimations(self):
        log.debug("animations: ")
        animationCount = 1  # default pose at frame 0

        startFrame = 1
        errMsg = ""

        if self.arm_obj.animation_data is None:
            self.arm_obj.animation_data_create()
            if self.params.animationType == 'SEPARATE':  # add NLA track compilation
                track = self.arm_obj.animation_data.nla_tracks.new()
                track.name = self.arm_obj.name + '_track'

        bckFiles = []
        for bckPath in self._bckPaths:
            bckFiles += common.getFiles(bckPath)
        #btpFiles = []
        #for btpPath in self._btpPaths:
        #    btpFiles += common.getFiles(btpPath)
        #btpFileNames = [common.getFilenameFile(f) for f in btpFiles]

        for f in bckFiles:
            bckFileName = common.getFilenameFile(f)
            b = Bck.Bck_in()
            try:
                b.LoadBck(f, len(self._bones))
            except Exception as err:
                log.warning('an animation file was corrupted. (error is %s)', err)
                continue

            # load the possibly existing btp file accompanying the bck one
            #try:
            #    btpIndex = btpFileNames.index('bckFiles')
            #except ValueError:  # no btp file to go with this bck file
            #    btp = None
            #else:
            #    btp = Btp.Btp()
            #    btp.LoadBtp(btpFiles[btpIndex])
            #    del btpFiles[btpIndex]
            #    del btpFileNames[btpIndex]

            if not len(b.anims):
                # file loader already knows that it won't fit
                errMsg += bckFileName + "\n"
            else:
                if self.params.animationType == 'SEPARATE':
                    try:
                        b.AnimateBoneFrames(0, self._bones, 1, self.params.includeScaling)
                        action = PBones.apply_animation(self._bones, self.arm_obj, self.jnt.frames, bckFileName)
                        action.bck_loop_type = b.loopType.name
                    except Exception as err:
                        log.error('animation file doesn\'t apply as expected (error is %s)', err)
                        continue
                    finally:
                        for com in self._bones:
                            com.reset()
                    bpy.context.scene.frame_end = startFrame + b.animationLength + 5
                    # (create space to insert strip)
                    try:
                        track.strips.new(bckFileName+'_strip', startFrame, action)
                    except Exception as err:
                        # assume the previous action is out of range: move it.
                        corrupted_action_track = self.arm_obj.animation_data.nla_tracks.new()
                        corrupted_action_track.name = 'CORRUPTED_ACTION_'+str(animationCount)
                        corrupted_action = track.strips[-1].action
                        corrupted_action_track.strips.new('action', track.strips[-1].frame_start,
                                                          corrupted_action)
                        track.strips.remove(track.strips[-1])
                        track.strips.new(bckFileName + '_strip', startFrame, action)  # try again
                    # add action to NLA compilation

                elif self.params.animationType == 'CHAINED':
                    try:
                        b.AnimateBoneFrames(startFrame, self._bones, 1, self.params.includeScaling)
                    except Exception as err:
                        log.error('Animation file doesn\'t apply as expected (error is %s)', err)
                        continue
                numberOfFrames = b.animationLength
                if b.animationLength <= 0:
                    numberOfFrames = 1
                endFrame = startFrame + b.animationLength

                    # kwXPortAnimationName += bckFileName + "," + str(startFrame) + "," + str(numberOfFrames)+ ",1;"
                startFrame = endFrame + 1
                animationCount += 1

        if self.params.animationType == 'CHAINED':
            bpy.context.scene.frame_start = 0
            bpy.context.scene.frame_end = startFrame
            try:
                PBones.apply_animation(self._bones, self.arm_obj, self.jnt.frames)
            except Exception as err:
                if self.params.PARANOID:
                    raise
                else:
                    log.error('Animation doesn\'t apply as expected. Change animation importation parameters'
                              'to isolate faulty file (error is %s)', err)

        elif self.params.animationType == 'SEPARATE':
            self.arm_obj.animation_data.action = None

    def ExtractImages(self, force=False):

        imageExt = '.' + self.params.imtype.lower()

        try:
            os.mkdir(self._texturePath)
        except FileExistsError:
            pass

        self._images = common.getFiles("*"+imageExt, basedir=self._texturePath)

        if len(self._images) == 0 or force:
            try:
                common.SubProcCall(
                    "bmdview",  # DO NOT capitalize: unix-like OSes use case-sensitive paths.
                    [self._bmdFilePath, self._texturePath, self.params.imtype],
                    self._bmdViewPathExe,
                )
            except common.subprocess.CalledProcessError as err:
                log.error('subprocess error: %s. Expect missing/glitchy textures', err) 

        # TODO: need to update BmdView.exe to process all file formats like BmdView2
        errorMessage = "Error generating dds / tga image file(s).\
                       Use BmdView2 to export the missing tga file(s)\
                       then delete the *.ERROR file(s) and run the importer again"
        errorFiles = common.getFiles("*.ERROR", basedir=self._texturePath)
        for f in errorFiles:
            errorMessage += f + "\n"  # report file
            common.newfile(f[:-6] + imageExt)  # and avoid crashes in the future
        if len(errorFiles) != 0:
            log.error(errorMessage)
            return False

        return True

    def CreateBTPDataFile(self):
        btpFiles = common.getFiles("..", "btp", "*.btp", basedir=self._bmdDir)
        # --messageBox (bckFiles as string)

        fBTP = open(self._bmdDir + "TextureAnimations.xml", 'w')

        print("<?xml version=1.0 encoding=utf-8?>\n", file=fBTP)
        print("<TextureAnimation>\n", file=fBTP)
        print("\t<Textures>", file=fBTP)

        firstLoop = True
        for self.texName in self.tex.stringtable:
            if firstLoop :
                firstLoop = False
            else:
                print("#", file=fBTP)
                print("%", self.texName, file=fBTP)
        print("</Textures>\n", file=fBTP)
        print("\t<Materials>", file=fBTP)
        firstLoop = True
        for matName in self._mat1.stringtable:
            print("#", file=fBTP)
            print("%", matName, file=fBTP)
        print("</Materials>\n", file=fBTP)
        print("\t<Animations>\n", file=fBTP)
        for btpFile in btpFiles:
            self.textureAnim = Btp.Btp()
            self.textureAnim.LoadBTP(btpFile)
            print("\t\t<Animation>\n", file=fBTP)
            print("\t\t\t<Name>%s</Name>\n" % common.getFilenameFile(btpFile), file=fBTP)
            firstLoop = True
            for anim in self.textureAnim.anims:
                print("\t\t\t<Material>\n", file=fBTP)
                print("\t\t\t\t<MaterialIndex>%d</MaterialIndex>\n" %anim.materialIndex, file=fBTP)
                # -- print("\t\t\t\t<Name>%</Name>\n", anim.materialName, file=fBTP)
                animaitonKeys = ""
                for key in anim.indices:
                    animaitonKeys = animaitonKeys + "#"
                    animaitonKeys = animaitonKeys + str(key)
                print("\t\t\t\t<KeyFrames>%s</KeyFrames>\n" %animaitonKeys, file=fBTP)
                print("\t\t\t</Material>\n", file=fBTP)
                # --messageBox (anim.animationName + ":" + animaitonKeys)
            print("\t\t</Animation>\n", file=fBTP)
        print("\t</Animations>\n", file=fBTP)
        print("</TextureAnimation>", file=fBTP)
        fBTP.close()

    def Import(self, filename, **kw):
        # contents of kw:
        # imtype, tx_pck (packTextures), sv_anim (loadAnimations, animationType),
        # nat_bn (naturalBones, disables loadAnimations and animationType),
        # ic_sc (includeScaling), frc_cr_bn (forceCreateBones),
        # boneThickness, dvg (DEBUGBG), val_msh (valudate_mesh), paranoia (PARANOID)
        # use_nodes, no_rot_cv (no_rot_conversion)
        self.params = common.Prog_params(filename, **kw)
        
        # provide access to parameters to other modules in this plugin. (kinda hacky solution)
        common.GLOBALS = self.params


        TexH.MODE = self.params.packTextures
        TexH.textures_reset()  # avoid use of potentially deleted data

        #if filename = 'P:\ath\to\file.bmd',
        self._bmdFilePath = filename
        # this is 'P:\ath\to\file' and '.bmd' (the second string is useful because it can also be 'bdl'
        temp_path, temp_ext = os.path.splitext(filename)
        # this is 'P:\ath\to\file_bmd\'
        self._bmdDir = temp_path+ '_' + temp_ext[1:] + os.sep  # generates dir name from file name?
        # P:\ath\to'
        self._bmdPath = os.path.split(temp_path)[0]
        # file(.bmd?)
        self._bmdFileName = common.getFilenameFile(filename)
        # P:\ath\to\file_bmd\Textures
        self._texturePath = self._bmdDir + "Textures"


        self._bckPaths.append("{1}{0}..{0}bck{0}*.bck".format(os.sep, self._bmdPath))
        self._bckPaths.append("{1}{0}..{0}bcks{0}*.bck".format(os.sep, self._bmdPath))
        self._bckPaths.append("{1}{0}..{0}scrn{0}*.bck".format(os.sep, self._bmdPath))
        self._bckPaths.append("{1}{0}*.bck".format(os.sep, self._bmdPath))
        self._btpPaths.append("{1}{0}..{0}btp{0}*.btp".format(os.sep, self._bmdPath))

        try:
            os.mkdir(self._bmdDir)
        except FileExistsError:
            pass

        try:
            self.LoadModel(filename)
        except Exception as err:
            log.critical('Could not load bmd file: looks corrupted (error is %s)', err)
            raise

        #  XCX this should not be needed vvv
        # if (not exportTextures) or (exportTextures and self.ExtractImages()):
        if True:
            try:
                self.ExtractImages()
            except Exception as err:
                log.error('Could not extract images. This could be the cause of a plugin crash'
                            ' later on (error is %s)', err)
            self.DrawScene()

        try:
            self.CreateBTPDataFile()
        except Exception as err:
            log.warning('couldn\'t transform BTP animations into xml files. Model should beave normally nevertheless')
        log.debug('end!')

    def __del__(self):
        if self._bones:
            self._bones[0].pre_delete()  # fixes momory leak

        MatH.MPL.MIX_GROUP_MTX = {}
        common.GLOBALS = None
        # object.__del__(self)

