#! /usr/bin/python3
if "bpy" in locals():  # trick to reload module on f8-press in blender
    LOADED = True
else:
    LOADED = False

from importlib import reload
from array import array
import os
from os import path as OSPath
import sys
from time import time

import bpy
from mathutils import Matrix, Vector, Euler, Color

if LOADED:
    for module in (BinaryReader, Mat44, Inf1, Vtx1, Shp1, Jnt1, Evp1, Drw1,
                   Bck, Mat3, Mat3V2, Tex1, Btp, MaxH, TexH, MatH, PBones):
        reload(module)

else:
    import blemd.BinaryReader as BinaryReader
    import blemd.Matrix44 as Mat44
    import blemd.Inf1 as Inf1
    import blemd.Vtx1 as Vtx1
    import blemd.Shp1 as Shp1
    import blemd.Jnt1 as Jnt1
    import blemd.Evp1 as Evp1
    import blemd.Drw1 as Drw1
    import blemd.Bck as Bck
    import blemd.Mat3 as Mat3
    import blemd.materialV2 as Mat3V2
    import blemd.Tex1 as Tex1
    import blemd.Btp as Btp
    import blemd.maxheader as MaxH
    import blemd.texhelper as TexH
    import blemd.materialhelper as MatH
    import blemd.pseudobones as PBones
del LOADED




class Prog_params:
    def __init__(self, filename, boneThickness, allowTextureMirror, forceCreateBones, loadAnimations, animationType,
                 exportTextures, exportType, includeScaling, imtype, dvg, use_nodes=False):
        self.filename = filename
        self.boneThickness = boneThickness
        self.allowTextureMirror = allowTextureMirror
        self.forceCreateBones = forceCreateBones
        self.loadAnimations = loadAnimations
        self.animationType = animationType
        # self.exportTextures = exportTextures
        # self.exportType = exportType
        self.includeScaling = includeScaling
        self.imtype = imtype
        self.DEBUGVG = dvg
        self.use_nodes = use_nodes
        # secondary parameters (computed)
        self.createBones = True


class LoopRepresentation:
    def __init__(self):
        self.vertex = -1
        self.UVs = [None]*8
        self.VColors = [None]*2
        self.normal = None

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

    def toarray(self, type):
        if type == 'co':
            ret = array('f', [0.0]*3*len(self.vertices))
            for num, com in enumerate(self.vertices):
                ret[3*num] = com.x
                ret[3*num+1] = com.y
                ret[3*num+2] = com.z
        elif type == 'loop_start':
            ret = array('i')
            for com in self.faces:
                ret.append(com.loop_start)
        elif type == 'normal':
            ret = array('f', [0.0] * 3 * len(self.loops))
            for num, com in enumerate(self.loops):
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
    # <variable _allowTextureMirror>
    # -- doesn't work on characters? required for stages?
    # <variable _forceCreateBones>
    # <variable _exportType>
    # -- #XFILE, #CHARACTER
    # <variable _runExtractTexturesCmd>
    # <variable _includeScaling>
    # <variable _reverseFaces>
    # -- required for .x export (render eyes before face)
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
        self.faceIndex = 0
        self._materialIDS = []
        self.vertexMultiMatrixEntry = []
        self._allowTextureMirror = False
        self.normals = []
        self._subMaterials = []

    def SetBmdViewExePath(self, value):
        self._bmdViewPathExe = value
        if not OSPath.exists(self._bmdViewPathExe + "BmdView.exe"):                        
            MaxH.MessageBox(self._bmdViewPathExe + "BmdView.exe not found. Place the BmdView.exe file"
                                                   "included in the zip file into the given path.")
            raise ValueError("ERROR")

    def TryHiddenDOSCommand(self, cmd, startpath):
                
        # --print "###################"
        # --print cmd
        # --print startpath
        try:
            MaxH.HiddenDOSCommand(cmd, startpath=startpath)
        except MaxH.subprocess.CalledProcessError as err:
            pass

    def BuildSingleMesh(self):
        # -----------------------------------------------------------------
        # -- mesh
        print('BuildSMesh : ', time())
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
        if len(self._materialIDS) > 0:
            for i in range(len(self._materialIDS), len(self.model.faces)):
                self._materialIDS.append(None)
        else:
            self._materialIDS = [None] * len(self.model.faces)

        for idx in range(len(self.model.vertices)):
            if self.model.vertices[idx] is None:
                self.model.vertices[idx] = temp_vtx = self.vtx.positions[idx]  # XCX should not have to do this
                # add vertices without matrix transformation
                temp_vtx.z *= -1
                temp_vtx.xyz = temp_vtx.xzy  # transform coordinates here

        modelMesh = bpy.data.meshes.new(MaxH.getFilenameFile(self._bmdFilePath))
        modelMesh.vertices.add(len(self.model.vertices))
        modelMesh.vertices.foreach_set('co', self.model.toarray('co'))
        modelMesh.loops.add(len(self.model.loops))
        modelMesh.loops.foreach_set('vertex_index', self.model.toarray('v_indexes'))
        modelMesh.polygons.add(len(self.model.faces))
        modelMesh.polygons.foreach_set('loop_start', self.model.toarray('loop_start'))
        modelMesh.polygons.foreach_set('loop_total', array('i', [3]*len(self.model.faces)))

        modelMesh.update()
        modelObject = bpy.data.objects.new(MaxH.getFilenameFile(self._bmdFilePath), modelMesh)
        bpy.context.scene.objects.link(modelObject)

        # XCX: find a way to replace that too.
        bm_to_pm = {}  # index shifter: material, get mat index
        for i in range(len(self._subMaterials)):
            MatH.add_material(modelObject, self._subMaterials[i])
        errmat = MatH.add_err_material(modelObject)
        for num, com in enumerate(modelObject.material_slots):
            bm_to_pm[com.material] = num
        f_to_rf = list(range(len(self.model.faces)))
        for num, com in enumerate(self._materialIDS):  # assign materials to faces
            # DEBUG reversed index
            if f_to_rf[num] is not None:
                if com is not None:
                    modelMesh.polygons[f_to_rf[num]].material_index = com  # bm_to_pm[com]
                else:
                    modelMesh.polygons[f_to_rf[num]].material_index = bm_to_pm[errmat]

        active_uv = None

        for uv in range(8):
            if self.model.hasTexCoords[uv]:
                TexH.newUVlayer(modelMesh, self.model, uv)
        active_uv = modelMesh.uv_textures[0]

        with MaxH.active_object(modelObject):
            if not active_uv:
                bpy.ops.paint.add_simple_uvs()
                active_uv = modelMesh.uv_textures[0]

            modelMesh.update()

            if self.model.hasColors[0]:
                # if len(self.vtx.colors) and len(self.vtx.colors[0]):  # has colors?
                alpha_image = MatH.add_vcolor(modelMesh, self.model, 0)
            if self.model.hasColors[1]:
                # if len(self.vtx.colors) > 1 and len(self.vtx.colors[1]):
                MatH.add_vcolor(modelMesh, self.model, 1)
        # update(modelMesh)

        # -----------------------------------------------------------------

        if self.params.createBones or self.params.DEBUGVG:
            with MaxH.active_object(modelObject):
                mod = modelObject.modifiers.new('Armature', type='ARMATURE')
                arm = bpy.data.armatures.new(modelObject.name+'_bones')
                self.arm_obj = arm_obj = bpy.data.objects.new(modelObject.name+'_armature', arm)
                bpy.context.scene.objects.link(arm_obj)
                modelObject.parent = arm_obj
                mod.object = arm_obj
                bpy.context.scene.update()

            with MaxH.active_object(arm_obj):
                bpy.ops.object.mode_set(mode='EDIT')
                for bone in self._bones:
                    arm.edit_bones.new(bone.name.fget())
                    if isinstance(bone.parent.fget(), PBones.Pseudobone):
                        if bone.parent.fget().name.fget() not in [temp.name.fget() for temp in self._bones]:
                            tempbone = arm.edit_bones.new(bone.parent.fget().name.fget())
                            if bone.parent.fget().parent.fget() is not None:
                                tempbone.parent = arm.edit_bones[bone.parent.fget().parent.fget().name.fget()]
                            tempbone.head = Vector(bone.parent.fget().position)
                            tempbone.tail = Vector(bone.parent.fget().endpoint)
                for bone in self._bones:
                    realbone = arm.edit_bones[bone.name.fget()]
                    if isinstance(bone.parent.fget(), PBones.Pseudobone):
                        realbone.parent = arm.edit_bones[bone.parent.fget().name.fget()]
                    realbone.head = Vector(bone.position)
                    realbone.tail = Vector(bone.endpoint)
                    modelObject.vertex_groups.new(bone.name.fget())

                if len(self.vertexMultiMatrixEntry) != len(self.model.vertices):
                    MaxH.MessageBox("Invalid skin")
                    raise ValueError("E")
                if self.params.createBones:
                    # XCX should not need this
                    for idx in range(len(self.vertexMultiMatrixEntry)):
                        if self.vertexMultiMatrixEntry[idx] is None:
                            self.vertexMultiMatrixEntry[idx] = Mat44.MultiMatrix()
                    for i in range(len(self.model.vertices)):
                        for num, vg_id in enumerate(self.vertexMultiMatrixEntry[i].indices):
                            modelObject.vertex_groups[vg_id].add([i], self.vertexMultiMatrixEntry[i].weights[num], 'REPLACE')

                    for bone in self._bones:
                        realbone = arm.edit_bones[bone.name.fget()]
                        vec = realbone.head
                        grp = modelObject.vertex_groups[bone.name.fget()]
                for com in self.DEBUGvgroups.keys():  # DEBUG vertex groups to fix UVs
                    vg = modelObject.vertex_groups.new(com)
                    vg.add(self.DEBUGvgroups[com], 1, 'REPLACE')

                bpy.context.scene.update()
                bpy.ops.object.mode_set(mode='OBJECT')

        modelMesh.update()

        modelMesh.create_normals_split()  # does this stabilize normals?

        for face in modelMesh.polygons:
            face.use_smooth = True  # normals have effect only if smooth shading

        # create custom data to write normals correctly?
        modelMesh.update()

        # begin not understood black box (where does this thing write to make normals stable?)
        clnors = self.model.toarray('normal')

        modelMesh.polygons.foreach_set("use_smooth", [True] * len(modelMesh.polygons))

        modelMesh.normals_split_custom_set(tuple(
                                                 zip(*(iter(clnors),) * 3)
                                                ))
        modelMesh.use_auto_smooth = True
        modelMesh.show_edge_sharp = True
        # end not understood black box

        # modelMesh.validate(clean_customdata=False)  # only validate now, if at all
        modelMesh.update()

        return modelMesh

    def LoadModel(self, filePath):
        """loads mesh data from file"""

        print("Load : ", time())
        # -- load model
        br = BinaryReader.BinaryReader()
        br.Open(filePath)
        self._bmdFilePath = filePath
        self._bmdDir = MaxH.getFilenamePath(self._bmdFilePath)
        self._bmdFileName = MaxH.getFilenameFile(self._bmdFilePath)
        self._bmdDir += self._bmdFileName + "\\"
        try:
            os.mkdir(self._bmdDir)
        except FileExistsError:
            pass
        self._texturePath = self._bmdDir + "Textures\\"

        br.SeekSet(0x20)

        iSize = 0
        strTag = ""  # 4 characters
        iTell = 0

        self.inf = Inf1.Inf1()
        self.vtx = Vtx1.Vtx1()
        self.shp = Shp1.Shp1()
        self.jnt = Jnt1.Jnt1()
        self.evp = Evp1.Evp1()
        self.drw = Drw1.Drw1()
        self._mat1 = Mat3.Mat3()
        self._mat1V2 = Mat3V2.Mat3()
        self.tex = Tex1.Tex1()

        while strTag != "TEX1":  # "TEX1 tag is the last one every time"
            br.SeekCur(iSize)
            streamPos = br.Position()
            strTag = br.ReadFixedLengthString(4)
            iSize = br.ReadDWORD()

            br.SeekSet(streamPos)
            if strTag == "INF1":
                self.inf.LoadData(br)
            elif strTag == "VTX1":
                self.vtx.LoadData(br)
            elif strTag == "SHP1":
                self.shp.LoadData(br)
            elif strTag == "JNT1":
                self.jnt.LoadData(br)
            elif strTag == "EVP1":
                self.evp.LoadData(br)
            elif strTag == "DRW1":
                self.drw.LoadData(br)
            elif strTag == "MAT3":
                self._mat1.LoadData(br)
                br.SeekSet(streamPos)
                self._mat1V2.LoadData(br)
            elif strTag == "TEX1":
                self.tex.LoadData(br)
            else:
                raise ValueError(strTag+' tag not recognized')
            br.SeekSet(streamPos)

        self.tex.LoadData(br)
        br.Close()

    def DrawBatch(self, index, matIndex):
        """assigns material and compute faces, vertex color and UV assignation to a "batch" """
        currBatch = self.shp.batches[index]
        batchid = index

        if not currBatch.attribs.hasPositions:
            raise ValueError("found batch without positions")

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

        matrixTable =[]
        # there should NEVER be more than 20 matrices per packet imo...even 10 sound like a lot...
        isMatrixWeighted = []
        # pos?
        multiMatrixTable = []
        # should be same count as matrixTable
        maxWeightIndices = 0


        # print (self.vtx.self.texCoords.count as string)

        for uv in range(8):  # copying vtx.texcoords into self.tverts
            if self.vtx.texCoords[uv] is not None:
                while len(self.tverts) <= uv:
                    self.tverts.append([])
                for i_temp in range(len(self.vtx.texCoords[uv])):
                    tvert = self.vtx.texCoords[uv][i_temp]
                    while len(self.tverts[uv]) <= i_temp:
                        self.tverts[uv].append(None)
                    self.tverts[uv][i_temp] = (tvert.s, -tvert.t+1, 0)  # flip uv v element

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
                            MaxH.MessageBox("WARNING: if (mod currPrimitive.points[m].matrixIndex 3) != 0 then " +
                                       str(currPrimitive.points[m].matrixIndex))
                        multiMat = multiMatrixTable[(currPrimitive.points[m].matrixIndex//3)]  # fixed

                    if currBatch.attribs.hasNormals:
                        temp_normals[currPrimitive.points[m].normalIndex] =\
                            self.vtx.normals[currPrimitive.points[m].normalIndex].copy()
                        temp_normals[currPrimitive.points[m].normalIndex].rotate(mat)

                    while len(self.vertexMultiMatrixEntry) <= posIndex:
                        self.vertexMultiMatrixEntry.append(None)
                    self.vertexMultiMatrixEntry[posIndex] = multiMat
                    newPos = mat*(self.vtx.positions[posIndex])
                    while len(self.model.vertices) <= posIndex:
                        self.model.vertices.append(None)
                    self.model.vertices[posIndex] = Vector((newPos.x, -newPos.z, newPos.y))

                # manage primitive type
                if currPrimitive.type == 0x98:
                    iterator = Vtx1.StripIterator(currPrimitive.points)
                    # GL_TRIANGLE_STRIP
                elif currPrimitive.type == 0xa0:
                    iterator = Vtx1.FanIterator(currPrimitive.points)
                    # GL_TRIANGLE_FAN
                else:
                    raise ValueError("unknown primitive type")
                for p0, p1, p2 in iterator:
                    posIndex0 = p0.posIndex
                    posIndex1 = p1.posIndex
                    posIndex2 = p2.posIndex

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
            effP = parentMatrix*Mat44.FrameMatrix(f)
            while len(self.jnt.matrices) <= n.index:
                self.jnt.matrices.append(None)
            self.jnt.matrices[n.index] = effP

            fstartPoint = parentMatrix*f.t
            fstartPoint = Vector(fstartPoint.xzy)
            fstartPoint.y *= -1

            bone = PBones.Pseudobone(parentBone, f, effP,
                                     fstartPoint,
                                     fstartPoint+Vector((0, self.params.boneThickness, 0)))

            bone.scale = (f.sx, f.sy, f.sz)

            mTransform = Euler((f.rx, f.ry, f.rz), 'XYZ').to_matrix().to_4x4() * parentMatrix
            # mx = mathutils.Matrix.Rotation(f.rx, 4, 'X')
            # my = mathutils.Matrix.Rotation(f.ry, 4, 'Y')
            # mz = mathutils.Matrix.Rotation(f.rz, 4, 'Z')
            # mTransform = (mx * my * mz) * parentMatrix

            bone.rotation_euler = mTransform.to_euler("XYZ")
            bone.width = bone.height = self.params.boneThickness

        for com in sg.children:
            self.CreateBones(com, effP, bone)

        if parentBone is None:
            return bone

    # convenient method for a less messy scenegraph analysis
    def buildSceneGraph(self, inf1, sg, j=0):
        """builds sceneGraph tree from inf1 descriptors in an array"""
        i = j
        while i < len(inf1.scenegraph):
            n = inf1.scenegraph[i]
            if n.type == 1:
                i += self.buildSceneGraph(inf1, sg.children[-1], i+1)
            elif n.type == 2:
                return i - j + 1
            elif n.type == 0x10 or n.type == 0x11 or n.type == 0x12:
                t = Inf1.SceneGraph()
                t.type = n.type
                t.index = n.index
                sg.children.append(t)
            else:
                print("buildSceneGraph(): unexpected node type %d", n.type, file=sys.stderr)
            i += 1

        # note: this code can only be reached by the top level function,
        # AKA the one where the loops end by itself
        # return first "real" node
        if len(sg.children) == 1:
            return sg.children[0]
        else:
            sg.type = sg.index = -1
            print("buildSceneGraph(): Unexpected size %d", len(sg.children), file=sys.stderr)
        return 0

    def DrawScenegraph(self, sg, parentMatrix, onDown=True, matIndex=0):
        """create faces and assign UVs, Vcolors, materials"""

        effP = parentMatrix.copy()

        n = sg

        if n.type == 0x10:  # -joint
            self.jnt.matrices[n.index] = Mat44.updateMatrix(self.jnt.frames[n.index], effP)  # XCX update matrix needed?
            effP = self.jnt.matrices[n.index]  # setup during CreateFrameNodes
            self.jnt.frames[n.index].incr_matrix = effP
        elif n.type == 0x11:  # build material

            matIndex=n.index

            # build material (old version)
            #matName = self._mat1.stringtable[n.index]

            if not self.params.use_nodes:
                mat = self._mat1.materials[self._mat1.indexToMatIndex[n.index]]  # corrected *2
                self._currMaterial = MatH.build_material(self, self._mat1, mat, self.tex,
                                                    self._images, self.ExtractImages)  # material build, first version
            else:
                mat = self._mat1V2.materials[self._mat1V2.indexToMatIndex[n.index]]
                self._currMaterial = Mat3V2.create_material(mat)


            onDown = mat.flag == 1
            if self._currMaterial is not None:  # mat.texStages[0] != 0xffff:  # do it if any texture has been made
                # XCX is that the good condition?
                if self.params.use_nodes:
                    self._currMaterial.name = self._mat1V2.stringtable[n.index]
                else:
                    self._currMaterial.name = self._mat1.stringtable[n.index]
                while self._currMaterialIndex >= len(self._subMaterials):  # create one more slot
                    self._subMaterials.append(None)
                self._subMaterials[self._currMaterialIndex] = self._currMaterial
                self._currMaterialIndex += 1

        elif n.type == 0x12 and onDown:  # - type = 18
            self.DrawBatch(n.index, matIndex)  # fixed

        for com in sg.children:
            self.DrawScenegraph(com, effP, onDown, matIndex)  # -- note: i and j start at 1 instead of 0

        if n.type == 0x12 and not onDown:  # - type = 18
            self.DrawBatch(n.index, matIndex)  # fixed

    def DrawScene(self):
        print("DrawScene : ", time())

        sg = Inf1.SceneGraph()  # prepare scenegraph
        sg = self.buildSceneGraph(self.inf, sg)
        self.model = ModelRepresentation()
        rootBone = self.CreateBones(sg, Matrix.Identity(4), None)
        # remove dummy root bone:
        print("frame node created", time())
        # -- FIX: Force create bone option allows to generate bones independently of their count
        if len(rootBone.children) == 1 and len(rootBone.children[0].children) == 0 and \
                                                                        not self.params.forceCreateBones:
            self.params.createBones = False
        origWorldBonePos = None

        if self.params.use_nodes:
            self._mat1V2.convert(self.tex, self._texturePath)  # + self.params.texturePrefix)
        # prepare material nodes

        if self.params.createBones:
            #self._bones = rootFrameNode.CreateBones(self.params.boneThickness, "")
            self._bones = rootBone.tree_to_array()

            origWorldBonePos = self._bones[0].position  # fixed

            # -- easier than recalculating all bone transforms
            d = Vector()
            self._bones[0].parent.fset(d)  # fixed
            d.rotate(Euler((90, 0, 0), 'XZY'))
        i = Matrix.Identity(4)

        self.DrawScenegraph(sg, i)
        modelMesh = self.BuildSingleMesh()

        if self.params.createBones:  # XCX is this needed?
            try:
                os.mkdir(self._bmdDir + "\\Animations")
            except FileExistsError: pass

        if self.params.createBones and self.params.loadAnimations:
            print("animations: ", time())
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
                bckFiles += MaxH.getFiles(self._bmdDir + bckPath)
            for f in bckFiles:
                bckFileName = MaxH.getFilenameFile(f)
                # savePath = self._bmdDir + "Animations\\" + bckFileName + ".anm"

                # saveMaxAnimName = self._bmdDir + bckFileName + ".max"  # -- .chr?
                b = Bck.Bck_in()
                b.LoadBck(f, len(self._bones))
                if not len(b.anims):
                    # file loader already knows that it won't fit
                    errMsg += bckFileName + "\n"
                else:
                    if self.params.animationType == 'SEPARATE':
                        b.AnimateBoneFrames(1, self._bones, 1, self.params.includeScaling)
                        action = PBones.apply_animation(self._bones, self.arm_obj, self.jnt.frames, bckFileName)
                        for com in self._bones:
                            com.position_kf = {}
                            com.position_tkf = {}
                            com.rotation_kf = {}
                            com.rotation_tkf = {}
                            com.scale_kf = {}
                            com.scale_tkf = {}
                        bpy.context.scene.frame_end = startFrame + b.animationLength + 100
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
                        b.AnimateBoneFrames(startFrame, self._bones, 1, self.params.includeScaling)
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
                PBones.apply_animation(self._bones, self.arm_obj, self.jnt.frames)

            elif self.params.animationType == 'SEPARATE':
                self.arm_obj.animation_data.action = None

    def ExtractImages(self, force=False):
                
        imageType = ".tga"

        bmdViewExe = self._bmdViewPathExe + "BmdView.exe"
        bmdPath = MaxH.getFilenamePath(self._bmdFilePath) + MaxH.getFilenameFile(self._bmdFilePath)
        try:
            os.mkdir(bmdPath)
        except FileExistsError:
            pass
        try:
            os.mkdir(self._texturePath)
        except FileExistsError:
            pass
        # -- if no tga files are found then extract the
        tgaFiles = MaxH.getFiles(self._texturePath + "*.tga")
        ddsFiles = MaxH.getFiles(self._texturePath + "*.dds")

        self._images = tgaFiles+ddsFiles

        # -- cannot use shellLaunch because it doesn't wait for a return value
        # -- don't use DOSCommand. Doesn't support spaces in full exe path. e.g. C:Program files\
        # -- if using version before 2008 then use DOSCommand and set BmdView.exe into a known path

        if (len(tgaFiles) == 0 and len(ddsFiles) == 0) or force:
            self.TryHiddenDOSCommand("BmdView.exe \"" + self._bmdFilePath + "\" \"" +
                                 self._texturePath+ "\\\"", self._bmdViewPathExe)

        ddsFiles = MaxH.getFiles(self._texturePath + "*.dds")
        # -- create tga file and delete dds file
        for f in MaxH.getFiles(self._texturePath + "*.dds"):
            TexH.addforcedname(f, f[:-4]+'.tga')

        # TODO: need to update BmdView.exe to process all file formats like BmdView2
        errorMessage = "Error generating dds / tga image file(s).\
                       Use BmdView2 to export the missing tga file(s)\
                       then delete the *.ERROR file(s) and run the importer again"
        errorFiles = MaxH.getFiles(self._texturePath + "*.ERROR")
        for f in errorFiles:
            errorMessage += f + "\n"  # report file
            MaxH.newfile(f[:-6]+'.dds')  # and avoid crashes in the future
            TexH.addforcedname(f, f[:-4] + '.tga')
        if len(errorFiles) != 0:
            MaxH.MessageBox(errorMessage)
            return False

        return True

    def CreateBTPDataFile(self):
        btpFiles = MaxH.getFiles(self._bmdDir + "..\\..\\btp\\*.btp")
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
            if firstLoop:
                firstLoop = False
            else:
                print("#", file=fBTP)
                print("%", matName, file=fBTP)
        print("</Materials>\n", file=fBTP)
        print("\t<Animations>\n", file=fBTP)
        for bckFile in btpFiles:
            self.textureAnim = Btp.Btp()
            self.textureAnim.LoadBTP(bckFile)
            print("\t\t<Animation>\n", file=fBTP)
            print("\t\t\t<Name>%</Name>\n", MaxH.getFilenameFile(bckFile), file=fBTP)
            firstLoop = True
            for anim in self.textureAnim.anims:
                print("\t\t\t<Material>\n", file=fBTP)
                print("\t\t\t\t<MaterialIndex>%</MaterialIndex>\n", anim.materialIndex, file=fBTP)
                # -- print("\t\t\t\t<Name>%</Name>\n", anim.materialName, file=fBTP)
                animaitonKeys = ""
                for key in anim.keyFrameIndexTable:
                    if firstLoop:
                        firstLoop = False
                    else:
                        animaitonKeys = animaitonKeys + "#"
                        animaitonKeys = animaitonKeys + str(key)
                print("\t\t\t\t<KeyFrames>%</KeyFrames>\n", animaitonKeys, file=fBTP)
                print("\t\t\t</Material>\n", file=fBTP)
                # --messageBox (anim.animationName + ":" + animaitonKeys)
            print("\t\t</Animation>\n", file=fBTP)
        print("\t</Animations>\n", file=fBTP)
        print("</TextureAnimation>", file=fBTP)
        fBTP.close()

    def Import(self, filename, boneThickness, allowTextureMirror, forceCreateBones, loadAnimations, exportTextures,
               exportType, includeScaling, imtype, dvg, use_nodes=False):
        self.params = Prog_params(filename, boneThickness, allowTextureMirror, forceCreateBones,
                                  loadAnimations != 'DONT', loadAnimations,
                                  exportTextures, exportType, includeScaling, imtype, dvg, use_nodes)

        self._bckPaths.append("..\\..\\bck\\*.bck")
        self._bckPaths.append("..\\..\\bcks\\*.bck")
        self._bckPaths.append("..\\..\\scrn\\*.bck")

        TexH.MODE = self.params.imtype
        TexH.textures_reset()  # avoid use of potentially deleted data

        # print(filename)
        self.LoadModel(filename)

        bmdPath = "".join(OSPath.splitext(self._bmdFilePath)) + "\\"  # generates dir name from file name?
        try:
            os.mkdir(bmdPath)
        except FileExistsError:
            pass
        try:
            os.mkdir(self._texturePath)
        except FileExistsError:
            pass

        #  XCX this should not be needed vvv
        # if (not exportTextures) or (exportTextures and self.ExtractImages()):
        if True:
            self.ExtractImages()
            self.DrawScene()
        self.CreateBTPDataFile()

    def __del__(self):
        if self._bones:
            self._bones[0].pre_delete()  # fixes momory leak
        # object.__del__(self)