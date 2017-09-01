#! /usr/bin/python3
if "bpy" in locals():  # trick to reload module on f8-press in blender
    LOADED = True
else:
    LOADED = False

from importlib import import_module, reload

import bpy
if LOADED:
    del FrameMatrix, updateMatrixTable
    reload(MModule)

    from .Matrix44 import *
else:
    from .Matrix44 import *
    MModule = import_module('.Matrix44', "blemd")
del LOADED

from .BinaryReader import *
from .Matrix44 import *
from array import array
from .Inf1 import *
from .Vtx1 import *
from .Shp1 import *
from .Jnt1 import *
from .Evp1 import *
from .Drw1 import *
from .Bck import *
from .Mat3 import *
from .materialV2 import Mat3 as Mat3V2, create_material
from .Tex1 import *
from .StringHelper import *
from .FrameNode import *
# from .ReassignRoot import *
from .Btp import *
from os import path as OSPath
from .maxheader import *
import math
from .texhelper import newtex_tslot, getTexImage, showTextureMap, getTexSlot, newUVlayer, addforcedname
texhelper = import_module('.texhelper', 'blemd')
from mathutils import Matrix, Vector, Euler, Color
from .materialhelper import add_vcolor, add_material, add_err_material, build_material
from .pseudobones import apply_animation
from time import time


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
        self.tverts= [[],[],[],[],[],[],[],[]]  # texture vertices
        self.tv_to_f_v = [[], [], [], [], [], [], [], []]  # texVerts to vertices_faces
        self._createBones = True
        self._exportType = 'XFILE'  # XCX: delete those unused vars
        self._boneThickness = 10
        self.vertices = []
        self._bones = []
        self._bckPaths = []
        self._reverseFaces = True
        self._loadAnimations = True
        self.faceIndex = 0
        self._materialIDS = []
        self._includeScaling = False
        self._parentBoneIndexs = []
        self.tFaces = [[],[],[],[],[],[],[],[]]
        self.faces = []
        self.vertexMultiMatrixEntry = []
        self._allowTextureMirror = False
        self.normals = []
        self.nFaces = []
        self.nc_to_f_v = []
        self.vcFaces = [[], []]  # vertex colors
        self.cv_to_f_v = [[], []]  # color-vertices to tuple(face, vertex)
        self._forceCreateBones = False
        self._subMaterials = []

    def SetBmdViewExePath(self, value):
        self._bmdViewPathExe = value
        if not OSPath.exists(self._bmdViewPathExe + "BmdView.exe"):                        
            MessageBox(self._bmdViewPathExe + "BmdView.exe not found. Place the BmdView.exe file included in the zip file into the given path.")
            raise ValueError("ERROR")
            #		if ((findString self._bmdViewPathExe " ") != undefined) then
            #		(
            #			try
            #			(
            #				HiddenDOSCommand "cmd dir"
            #			)
            #			catch 
            #			(
            #				MessageBox "DosCommand does not support a BmdView path that contains spaces. Move the BmdView.exe file to a path without spaces and update the code int ImportUI.ms (search for 'UPDATE BMDVIEW.EXE PATH')"
            #				throw
            #			)
            #		)

    def TryHiddenDOSCommand(self, cmd, startpath):
                
        # --print "###################"
        # --print cmd
        # --print startpath
        try:
            HiddenDOSCommand(cmd, startpath=startpath)
        except Exception as err:
            pass
            # -- Uncomment the line below for if the startpath contains spaces
            # -- startpath = "C:\\" -- and place BmdView.exe in "C:\\" directory
            #if startpath.index(" ") != -1 :
            #    msg = "The startpath contains spaces (unable to run DosCommand). Place BmdView.exe in a path without spaces an update the startpath value in the BModel.ms file"
            #    MessageBox(msg)
            #    raise ValueError()
            #DosCommand (startpath + cmd)

    def ReverseArray(self, inputArray):
        i = 0
        rev = []
        i = len(inputArray)
        while i > 0:
            rev.append(inputArray[i-1])  # corrected!
            i -= 1
        # -- inputArray = rev doesn't work
        return rev

    def BuildSingleMesh(self):
        # -----------------------------------------------------------------
        # -- mesh
        print('BuildSMesh : ', time())
        if self._reverseFaces:
            self.faces = self.ReverseArray(self.faces)
            self._materialIDS = self.ReverseArray(self._materialIDS)
            #for com in range(len(self._materialIDS)):
            #    self._materialIDS[com] = len(self._subMaterials)-1-self._materialIDS[com]
            for uv in range(8):
                self.tFaces[uv] = self.ReverseArray(self.tFaces[uv])
                for num, com in enumerate(self.tv_to_f_v[uv]):
                    for num2, com2 in enumerate(com):
                        com2 = (len(self.faces)-1-com2[0], com2[1])
                        com[num2] = com2
                    self.tv_to_f_v[uv][num] = com
            # vertex colors are now similar to uv textures
            for cv in range(2):
                self.vcFaces[cv] = self.ReverseArray(self.vcFaces[cv])
                for num, com in enumerate(self.cv_to_f_v[cv]):
                    for num2, com2 in enumerate(com):
                        com2 = (len(self.faces)-1-com2[0], com2[1])
                        com[num2] = com2
                    self.cv_to_f_v[cv][num] = com


        # -- TODO: should never have undefined materials
        for i in range(len(self._materialIDS)):
            if self._materialIDS[i] is None:
                pass  # self._materialIDS[i] = -1  # -- not found index

        # -- FIX: Fill missing material IDs

        if len(self._materialIDS) > 0:
            for i in range(len(self._materialIDS), len(self.faces)):
                self._materialIDS.append(None)  # -1)
        else:
            self._materialIDS = [-1] * len(self.faces)

        for idx in range(len(self.vertices)):
            if self.vertices[idx] is None:
                self.vertices[idx] = (0, 0, 0)  # XCX should not have to do this
        modelMesh = bpy.data.meshes.new(getFilenameFile(self._bmdFilePath))
        modelMesh.from_pydata(self.vertices, [], self.faces)
        modelMesh.update()
        modelObject = bpy.data.objects.new(getFilenameFile(self._bmdFilePath), modelMesh)
        #while modelObject.material_slots[0].material is None:
        #    tempbk = bpy.context.scene.objects.active  # remove empty material slot
        #    bpy.context.scene.objects.active = modelObject
        #    modelObject.active_material_index = 0
        #    bpy.ops.object.material_slot_remove()
        #    bpy.context.scene.objects.active = tempbk
        #    del tempbk
        bpy.context.scene.objects.link(modelObject)
        bm_to_pm = {}  # index shifter: material, get mat index
        for i in range(len(self._subMaterials)):
            add_material(modelObject, self._subMaterials[i])
        errmat = add_err_material(modelObject)
        for num, com in enumerate(modelObject.material_slots):
            bm_to_pm[com.material] = num
        f_to_rf = [None]*len(self.faces)
        for num, temp in enumerate(modelMesh.polygons):
            index = self.faces.index(tuple(temp.vertices))
            while f_to_rf[index] is not None:
                index = self.faces.index(tuple(temp.vertices), index+1)
            f_to_rf[index] = num
        for num, com in enumerate(self._materialIDS):  # assign materials to faces
            # DEBUG reversed index
            if f_to_rf[num] is not None:
                if com is not None:
                    modelMesh.polygons[f_to_rf[num]].material_index = com  # bm_to_pm[com]
                else:
                    modelMesh.polygons[f_to_rf[num]].material_index = bm_to_pm[errmat]
        #for com in self._materialIDS:
        #    add_material(modelObject, com)

        if len(self._materialIDS) > 0:  # - FIX: Do not set texcoord faces when there are no textures on model.
            pass
            # buildTVFaces(modelMesh, False) # XCX

        active_uv = None

        for uv in range(8):
            if len(self.tverts[uv]) and len(self.tFaces[uv]):
                newUVlayer(modelMesh, self.tverts[uv], self.tFaces[uv], self.faces, self.tv_to_f_v[uv])
                active_uv = modelMesh.uv_textures[0]

        with active_object(modelObject):
            if not active_uv:
                bpy.ops.paint.add_simple_uvs()
                active_uv = modelMesh.uv_textures[0]

            # XCX normals should be set here, but updating the mesh seems to delete this info

            modelMesh.update()

            if len(self.vtx.colors) and len(self.vtx.colors[0]):  #- has colors? fixed.
                alpha_image = add_vcolor(modelMesh, self.vtx.colors[0], self.cv_to_f_v[0], self.faces, active_uv, 0)
                if len(self.vtx.colors) > 1 and len(self.vtx.colors[1]):  # fixed
                    add_vcolor(modelMesh, self.vtx.colors[1], self.cv_to_f_v[1], self.faces, active_uv, 1)  # fixed


        # update(modelMesh)

        # -----------------------------------------------------------------

        if self._createBones or self.DEBUGVG:
            with active_object(modelObject):
                mod = modelObject.modifiers.new('Armature', type='ARMATURE')
                arm = bpy.data.armatures.new(modelObject.name+'_bones')
                self.arm_obj = arm_obj = bpy.data.objects.new(modelObject.name+'_armature', arm)
                bpy.context.scene.objects.link(arm_obj)
                modelObject.parent = arm_obj
                mod.object = arm_obj
                bpy.context.scene.update()

            with active_object(arm_obj):
                bpy.ops.object.mode_set(mode='EDIT')
                for bone in self._bones:
                    arm.edit_bones.new(bone.name.fget())
                    if isinstance(bone.parent.fget(), Pseudobone):
                        if bone.parent.fget().name.fget() not in [temp.name.fget() for temp in self._bones]:
                            tempbone = arm.edit_bones.new(bone.parent.fget().name.fget())
                            tempbone.parent = arm.edit_bones[bone.parent.fget().parent.fget().name.fget()]
                            tempbone.head = Vector(bone.parent.fget().position)
                            tempbone.tail = Vector(bone.parent.fget().endpoint)
                for bone in self._bones:
                    realbone = arm.edit_bones[bone.name.fget()]
                    if isinstance(bone.parent.fget(), Pseudobone):
                        realbone.parent = arm.edit_bones[bone.parent.fget().name.fget()]
                    realbone.head = Vector(bone.position)  #mathutils.Vector((0,0,0))
                    realbone.tail = Vector(bone.endpoint)  #mathutils.Vector((0,0,1))
                    modelObject.vertex_groups.new(bone.name.fget())
                    # skinOps.addBone(mysk, bone, 0) # XCX DONE?

                if len(self.vertexMultiMatrixEntry) != len(self.vertices):
                    MessageBox("Invalid skin")
                    raise ValueError("E")
                if self._createBones:
                    # XCX should not need this
                    for idx in range(len(self.vertexMultiMatrixEntry)):
                        if self.vertexMultiMatrixEntry[idx] is None:
                            self.vertexMultiMatrixEntry[idx] = MultiMatrix()
                    for i in range(len(self.vertices)):
                        for num, vg_id in enumerate(self.vertexMultiMatrixEntry[i].indices):
                            modelObject.vertex_groups[vg_id].add([i], self.vertexMultiMatrixEntry[i].weights[num], 'REPLACE')

                    for bone in self._bones:
                        realbone = arm.edit_bones[bone.name.fget()]
                        vec = realbone.head
                        grp = modelObject.vertex_groups[bone.name.fget()]
                        # old bone displacement method
                        #for num in range(len(self.vertices)):
                        #    try:
                        #        with stdout_redirected():  # stop this call to print junk in stdout
                        #            tmp = grp.weight(num)
                        #    except RuntimeError:  # vert not in group
                        #        tmp = 0
                        #    modelMesh.vertices[num].co += (vec*tmp)
                for com in self.DEBUGvgroups.keys():  # DEBUG vertex groups to fix UVs
                    vg = modelObject.vertex_groups.new(com)
                    vg.add(self.DEBUGvgroups[com], 1, 'REPLACE')

                bpy.context.scene.update()
                bpy.ops.object.mode_set(mode='OBJECT')

        modelMesh.update()

        modelMesh.create_normals_split()  # does this stabilize normals?

        for face in modelMesh.polygons:
            face.use_smooth = True  # normals have effect only if smooth shading

        # for i in range(len(self.vertices)):  # set normals here because they seem to be lost in some calulations
        #    if self.normals[i] is not None:
        #        modelMesh.vertices[i].normal = -Vector(self.normals[i])  # XCX normals are recalculated: WTF?

        setNormals(modelMesh, self.faces, self.nc_to_f_v, self.vtx.normals)
        # for loop in modelMesh.loops:
        #    if self.normals[loop.vertex_index] is not None:
        #        loop.normal = Vector(self.normals[loop.vertex_index])  # XCX is the [:] necessary?
        #    else:
        #        loop.normal = modelMesh.vertices[loop.vertex_index].normal
        #    # print(type(loop.normal), loop.normal)

        # create custom data to write normals correctly?
        modelMesh.validate(clean_customdata=False)  # *Very* important to not remove loop normals here!
        modelMesh.update()

        # begin not understood black box (where does this thing write to make normals stable?)
        clnors = array('f', [0.0] * (len(modelMesh.loops) * 3))
        modelMesh.loops.foreach_get("normal", clnors)

        modelMesh.polygons.foreach_set("use_smooth", [True] * len(modelMesh.polygons))

        modelMesh.normals_split_custom_set(tuple(zip(*(iter(clnors),) * 3)))
        modelMesh.use_auto_smooth = True
        modelMesh.show_edge_sharp = True
        # end not understood black box

        return modelMesh

    def LoadModel(self, filePath):
        """loads mesh data from file"""

        print("Load : ", time())
        # -- load model
        br = BinaryReader()
        br.Open(filePath)
        self._bmdFilePath = filePath
        self._bmdDir = getFilenamePath(self._bmdFilePath)
        self._bmdFileName = getFilenameFile(self._bmdFilePath)
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

        self.inf = Inf1()
        self.vtx = Vtx1()
        self.shp = Shp1()
        self.jnt = Jnt1()
        self.evp = Evp1()
        self.drw = Drw1()
        self._mat1 = Mat3()
        self._mat1V2 = Mat3V2()
        self.tex = Tex1()

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
                # -- print (self.shp as string)
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

    """def DrawVerts(self):
        for vec in self.vtx.positions:
            # p = bpy.types.MeshVertex(pos=[vec.x, vec.y, vec.z], cross=on, Box=off)
            print(vec)"""  # XCX is this needed anyways?

    def DrawBatch(self, index, effP, matIndex):
        """assigns material and compute faces, vertex color and UV assignation to a "batch" """
        currBatch = self.shp.batches[index]
        batchid = index

        if not currBatch.attribs.hasPositions:
            raise ValueError("found batch without positions")

        vertIndex = 0
        i = 0

        matrixTable =[]
        # -- there should NEVER be more than 20 matrices per packet imo...even 10 sound like a lot...
        isMatrixWeighted =[]
        # -- pos?
        multiMatrixTable = []
        # -- should be same count as matrixTable
        maxWeightIndices = 0

        matrixTable = []
        multiMatrixTable = []

        # --print (self.vtx.self.texCoords.count as string)

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
            updateMatrixTable(self.evp, self.drw, self.jnt, currPacket, multiMatrixTable, matrixTable, isMatrixWeighted)

            # end for index in currPacket.matrixTable do
            # --if no matrix index is given per vertex, 0 is the default.
            # --otherwise, mat is overwritten later.
            mat = matrixTable[0]  # corrected
            multiMat = multiMatrixTable[0]
            for primnum, currPrimitive in enumerate(currPacket.primitives):
                for m in range(len(currPrimitive.points)):
                    posIndex = currPrimitive.points[m].posIndex   # fixed
                    if currBatch.attribs.hasMatrixIndices:
                        mat = matrixTable[(currPrimitive.points[m].matrixIndex//3)]  # fixed
                        if currPrimitive.points[m].matrixIndex % 3:
                            MessageBox("WARNING: if (mod currPrimitive.points[m].matrixIndex 3) != 0 then " + str(currPrimitive.points[m].matrixIndex))
                        multiMat = multiMatrixTable[(currPrimitive.points[m].matrixIndex//3)]  # fixed

                    # if currBatch.attribs.hasNormals:  # XCX delete?
                    #    #if len(self.vtx.normals) > currPrimitive.points[m].normalIndex:
                    #    normal =mat*self.vtx.normals[currPrimitive.points[m].normalIndex]  # fixed
                    #    normal.normalize()
                    #    while len(self.normals) <= posIndex:
                    #        self.normals.append(None)
                    #    self.normals[posIndex] = (normal.x, -normal.z, normal.y)

                    while len(self.vertexMultiMatrixEntry) <= posIndex:
                        self.vertexMultiMatrixEntry.append(None)
                    self.vertexMultiMatrixEntry[posIndex] = multiMat
                    newPos = mat*(self.vtx.positions[posIndex])
                    while len(self.vertices) <= posIndex:
                        self.vertices.append(None)
                    # tempvert = Vector3()
                    # tempvert.setXYZ(newPos.x, newPos.y, newPos.z)
                    # tempvert = effP.MultiplyVector(tempvert)
                    # tempvert.ToMaxScriptPosFlip()  # -- flip order
                    self.vertices[posIndex] = [newPos.x, -newPos.z, newPos.y]

                # manage primitive type
                if currPrimitive.type == 0x98:
                    iterator = StripIterator(currPrimitive.points)
                    # GL_TRIANGLE_STRIP
                elif currPrimitive.type == 0xa0:
                    iterator = FanIterator(currPrimitive.points)
                    # GL_TRIANGLE_FAN
                else:
                    raise ValueError("unknown primitive type")
                for p1, p2, p3 in iterator:
                    posIndex1 = p1.posIndex
                    posIndex2 = p2.posIndex
                    posIndex3 = p3.posIndex

                    # XCX DEBUG (create debug vertex groups)
                    if self.DEBUGVG:
                        tempvg = self.DEBUGvgroups.get(str(batchid), None)
                        if not tempvg:
                            tempvg = []
                            self.DEBUGvgroups[str(batchid)] = tempvg
                        tempvg.append(posIndex1)
                        tempvg.append(posIndex2)
                        tempvg.append(posIndex3)
                        tempvg = self.DEBUGvgroups.get(str(batchid)+','+str(packnum), None)
                        if not tempvg:
                            tempvg = []
                            self.DEBUGvgroups[str(batchid)+','+str(packnum)] = tempvg
                        tempvg.append(posIndex1)
                        tempvg.append(posIndex2)
                        tempvg.append(posIndex3)
                        tempvg = self.DEBUGvgroups.get(str(batchid)+','+str(packnum)+','+str(primnum), None)
                        if not tempvg:
                            tempvg = []
                            self.DEBUGvgroups[str(batchid)+','+str(packnum)+','+str(primnum)] = tempvg
                        tempvg.append(posIndex1)
                        tempvg.append(posIndex2)
                        tempvg.append(posIndex3)

                    while len(self.faces) <= self.faceIndex:
                        self.faces.append(None)
                    if self.faces[self.faceIndex] is not None:
                        pass

                    self.faces[self.faceIndex] = (posIndex1, posIndex2, posIndex3)

                    # create texture-coordinates data for correct assignation (later)
                    for uv in range(8):
                        if len(self.tFaces) <= uv:
                            self.tFaces.append([])
                        if currBatch.attribs.hasTexCoords[uv]:
                            t1Index = p1.texCoordIndex[uv]  # fixed
                            t2Index = p2.texCoordIndex[uv]  # fixed
                            t3Index = p3.texCoordIndex[uv]  # fixed
                            while len(self.tFaces[uv]) <= self.faceIndex:
                                self.tFaces[uv].append([None, None, None])
                            self.tFaces[uv][self.faceIndex] = (t1Index, t2Index, t3Index)
                            # new UV method needs this
                            while len(self.tv_to_f_v[uv]) <= max(t1Index, t2Index, t3Index):
                                self.tv_to_f_v[uv].append([])
                            self.tv_to_f_v[uv][t1Index].append((self.faceIndex, posIndex1))
                            self.tv_to_f_v[uv][t2Index].append((self.faceIndex, posIndex2))
                            self.tv_to_f_v[uv][t3Index].append((self.faceIndex, posIndex3))

                    # create normal assignation data
                    if currBatch.attribs.hasNormals:
                        n1Index = p1.normalIndex  # fixed
                        n2Index = p2.normalIndex  # fixed
                        n3Index = p3.normalIndex  # fixed
                        while len(self.nFaces) <= self.faceIndex:  # XCX nFaces and tFaces not needed?
                            self.nFaces.append([None, None, None])
                        self.nFaces[self.faceIndex] = (n1Index, n2Index, n3Index)
                        # new UV method needs this
                        while len(self.nc_to_f_v) <= max(n1Index, n2Index, n3Index):
                            self.nc_to_f_v.append([])
                        self.nc_to_f_v[n1Index].append((self.faceIndex, posIndex1))
                        self.nc_to_f_v[n2Index].append((self.faceIndex, posIndex2))
                        self.nc_to_f_v[n3Index].append((self.faceIndex, posIndex3))

                    # materials
                    while len(self._materialIDS) <= self.faceIndex:
                        self._materialIDS.append(None)
                    self._materialIDS[self.faceIndex] = matIndex
                    #self._materialIDS[self.faceIndex] = self._currMaterial
                    # _currMaterialIndex is incremented "too soon"

                    # vertex colors
                    for vc in (0, 1):
                        while len(self.vcFaces[vc]) <= self.faceIndex:
                            self.vcFaces[vc].append(None)
                        if currBatch.attribs.hasColors[vc]:  # fixed
                            c1Index = p1.colorIndex[vc]  # fixed x2
                            c2Index = p2.colorIndex[vc]  # fixed x2
                            c3Index = p3.colorIndex[vc]  # fixed x2
                            while len(self.cv_to_f_v[vc]) <= max(c1Index, c2Index, c3Index):
                                self.cv_to_f_v[vc].append([])
                            self.cv_to_f_v[vc][c1Index].append((self.faceIndex, posIndex1))
                            self.cv_to_f_v[vc][c2Index].append((self.faceIndex, posIndex2))
                            self.cv_to_f_v[vc][c3Index].append((self.faceIndex, posIndex3))
                            self.vcFaces[vc][self.faceIndex] = [c1Index, c2Index, c3Index]
                        else:
                            self.vcFaces[vc][self.faceIndex] = None
                    self.faceIndex += 1

                # end if currPrimitive.type == 0x98
            # end for currPrimitive in currPacket.primitives
         # end for currPacket in currBatch.packets

    def CreateFrameNodes(self, sg, parentMatrix, parentFrameNode):
        """creates bone hierarchy (FrameNodes) and apply matrices(jnt1.frames used to compute jnt1.matrices)"""
        effP = parentMatrix.copy()
        fNode = parentFrameNode
        n = sg

        if n.type == 0x10:
            # --joint
            f = self.jnt.frames[n.index]  # fixed
            effP = parentMatrix*FrameMatrix(f)
            while len(self.jnt.matrices) <= n.index:
                self.jnt.matrices.append(None)
            self.jnt.matrices[n.index] = effP  # -- effP.Multiply(FrameMatrix(f)) # fixed

            fNode = FrameNode()
            fNode.f = f
            fNode.name = f.name

            fstartPoint = parentMatrix*f.t
            fNode.startPoint = fstartPoint.x, -fstartPoint.z, fstartPoint.y
            del fstartPoint
            fNode.parentFrameNode = parentFrameNode
            fNode.effP = effP
            # --fNode.name = self._bmdFileName + "_" + f.name	-- FIX: DO NOT ADD FILENAME PREFIX TO BONES
            parentFrameNode.children.append(fNode)
            b1 = True

        for com in sg.children:
            self.CreateFrameNodes(com, effP, fNode)

    def CreateCharacter(self, rootFrameNode):
        # XCX called?
        # XCX FUNC plz get here when role defined
        nodes = rootFrameNode.GetAllNodes()
        chr = bpy.data.armatures.new(self._bmdFileName + "_Character")
        #chr = assemblyMgr.assemble(nodes)
        #chr.assemblyBBoxDisplay = False
        #chr.iconSize = self._iconSize
        #chr.wirecolor = (colorMan.getColor(chr_color)) * 255

        groupHead = None
        for n in nodes:
            pass
            #if isGroupHead(n):
            #    groupHead = n

        for bone in self._bones:
            pass # bone.setSkinPose()
        # chr.displayRes = 1  # -- hide bones
        # assemblyMgr.Open(chr)
        return chr

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
                t = SceneGraph()
                t.type = n.type
                t.index = n.index
                sg.children.append(t)
            else:
                print("buildSceneGraph(): unexpected node type %d", n.type, file=sys.stderr)
            i += 1

        #//remove dummy node at root
        if len(sg.children) == 1:
            t = sg.children[0]
            sg = t  #//does it wotk without the temp value?
        else:
            sg.type = sg.index = -1
            print("buildSceneGraph(): Unexpected size %d", len(sg.children), file=sys.stderr)
        return 0

    def DrawScenegraph(self, sg, parentMatrix, onDown=True, matIndex=0):
        """create faces and assign UVs, Vcolors, materials"""

        effP = parentMatrix.copy()

        n = sg

        if n.type == 0x10:  # -joint
            self.jnt.matrices[n.index] = updateMatrix(self.jnt.frames[n.index], effP)  # XCX update matrix needed?
            effP = self.jnt.matrices[n.index]  # -- setup during CreateFrameNodes # corrected
            self.jnt.frames[n.index].incr_matrix = effP
        elif n.type == 0x11:  # build material

            matIndex=n.index

            # build material (old version)
            #matName = self._mat1.stringtable[n.index]  # correced

            if not self.use_nodes:
                mat = self._mat1.materials[self._mat1.indexToMatIndex[n.index]]  # corrected *2
                self._currMaterial = build_material(self, self._mat1, mat, self.tex,
                                                    self._images, self.ExtractImages)  # material build, first version
            else:
                mat = self._mat1V2.materials[self._mat1V2.indexToMatIndex[n.index]]
                self._currMaterial = create_material(mat)  # XCX XCX mat build second version


            onDown = mat.flag == 1
            if self._currMaterial is not None:  # mat.texStages[0] != 0xffff:  # do it if any texture has been made
                # XCX is that the good condition?
                if self.use_nodes:
                    self._currMaterial.name = self._mat1V2.stringtable[n.index]
                else:
                    self._currMaterial.name = self._mat1.stringtable[n.index]
                while self._currMaterialIndex >= len(self._subMaterials):  # create one more slot
                    self._subMaterials.append(None)
                self._subMaterials[self._currMaterialIndex] = self._currMaterial
                self._currMaterialIndex += 1

        elif n.type == 0x12 and onDown:  # - type = 18
            self.DrawBatch(n.index, effP, matIndex)  # fixed

        for com in sg.children:
            self.DrawScenegraph(com, effP, onDown, matIndex)  # -- note: i and j start at 1 instead of 0

        if n.type == 0x12 and not onDown:  # - type = 18
            self.DrawBatch(n.index, effP, matIndex)  # fixed

    def RotateAroundWorld(self, obj, rotation):  # XCX used?
        print(rotation, type(rotation))
        origParent = obj.parent
        d = bpy.data.new('UTEMP_PL', None)
        d.location = Vector((0,0,0))
        obj.parent = d
        d.rotation_euler = Euler(rotation, 'XYZ')
        act_bk = bpy.ops.active
        bpy.ops.active = d
        bpy.ops.object.transform_apply(rotation=True)
        bpy.ops.active = obj
        bpy.ops.object.transform_apply(rotation=True)
        bpy.ops.active = act_bk
        obj.parent = None
        bpy.data.objects.remove(d)
        # --delete d
        # --if (origParent != undefined) then
        # --	obj.parent = origParent

    def DrawScene(self):  # XCX create armature here
        print("DrawScene : ", time())

        m = Matrix()
        _frameMatrix = Matrix.Identity(4)
        rootFrameNode = FrameNode()
        identity = Matrix.Identity(4)

        sg = SceneGraph()  # prepare scenegraph
        self.buildSceneGraph(self.inf, sg)
        self.CreateFrameNodes(sg, identity, rootFrameNode)
        print("frame node created", time())
        # -- FIX: Force create bone option allows to generate bones independently of their count
        if len(rootFrameNode.children) == 1 and len(rootFrameNode.children[0].children) == 0 and \
                                                                        not self._forceCreateBones:
            self._createBones = False
        origWorldBonePos = None

        if self.use_nodes:
            self._mat1V2.convert(self.tex, self._texturePath + self._texturePrefix)
        # prepare material nodes

        if self._createBones:
            self._bones = rootFrameNode.CreateBones(self._boneThickness, "")
            if self._includeScaling:  # - scaling cases IK and number of bones issue
                rootFrameNode.FixBones(self._boneThickness)

            self._parentBoneIndexs = rootFrameNode.CreateParentBoneIndexs()
            # XCX get rid of this call (^^^^) and what goes with it.
            origWorldBonePos = self._bones[0].position  # fixed

            # -- easier than recalculating all bone transforms
            d = Vector()
            self._bones[0].parent.fset(d)  # fixed
            d.rotate(Euler((90, 0, 0), 'XZY'))
        i = Matrix.Identity(4)

        print("animations: ", time())
        self.DrawScenegraph(sg, i)
        modelMesh = self.BuildSingleMesh()

        if self._createBones and self._exportType != 'XFILE' and False:  # XCX this is suspected to be a pile of bullcrap
            chr = self.CreateCharacter(rootFrameNode)
            # --RotateAroundWorld  chr (EulerAngles 90 0 0)

            # -- Rotate Character assembly upwards and swap hierarchy for Point and Character
            chr.rotation_euler = Euler((90, 0, 0), 'XZY')
            self._bones[0].parent.fset(d)  # fixed
            d.parent.fset(chr)
        # --RotateAroundWorld modelMesh (EulerAngles 90 0 0) -- e.g. stage, object
        if self._createBones:  # XCX is this needed?
            try:
                dirCreated = os.mkdir(self._bmdDir + "\\Animations")
            except FileExistsError: pass
        bckFiles = []
        errMsg = ""
        # --self._createBones = True
        if self._createBones and self._loadAnimations:
            # fileProperties.addProperty  custom "exportAnimation" True
            _onlyExportAnimations = False
            if _onlyExportAnimations:  # XCX remove this?
                pass
                # done before
                """# -- remove mesh and create fake skinning mesh (required for panda export)
                del modelMesh
                fakeMesh = bpy.data.meshes.new('FAKE_TEST_MESH')
                fakeMesh.from_pydata([[10, 0, 0], [0, 0, 0], [0, 10, 0]], [], [[3,2,1]])
                fakeMesh.update()
                #max modify mode
                bpy.context.selection.append(fakeMesh)  # XCX
                subObjectLevel = 0
                newskin = Skin()
                addModifier(fakeMesh, newskin)
                mysk = fakeMesh.modifiers[Skin]  # XCX
                subobjectLevel = 1
                modPanel.setCurrentObject(mysk)  # XCX
                subobjectLevel = 1
                skinOps.addBone(mysk, getNodeByName("RootBone"), 0)
                # ClassOf fakeMesh # -- http://forums.cgsociety.org/archive/index.php/t-456395.html
                fakeMesh.update()
                subObjectLevel = 0 # XCX
                #deselect fakeMesh"""

            kwXPortAnimationName = ""  # XCX what is this anyway?
            animationCount = 1  # -- default pose at frame 1

            startFrame = 1
            refBoneRequiresDummyList = []
            errMsg = ""
            # -- remove dummy objects if not required
            for i in range(len(self._bones)):
                while len(refBoneRequiresDummyList) <= i:
                    refBoneRequiresDummyList.append(None)
                refBoneRequiresDummyList[i] = False
            for bckPath in self._bckPaths:
                bckFiles = getFiles(self._bmdDir + bckPath)
                for f in bckFiles:
                    bckFileName = getFilenameFile(f)
                    savePath = self._bmdDir + "Animations\\" + bckFileName + ".anm"

                    saveMaxAnimName = self._bmdDir + bckFileName + ".max"  # -- .chr?
                    b = Bck_in()
                    b.LoadBck(f)
                    if len(b.anims) != len(self._bones):
                        errMsg += bckFileName + "\n"
                    else:
                        endFrame = None
                        b.AnimateBoneFrames(startFrame, self._bones, 1,
                                            self._exportType, refBoneRequiresDummyList, self._includeScaling)

                        numberOfFrames = b.animationLength

                        if b.animationLength <= 0:
                            numberOfFrames= 1
                        endFrame = startFrame + b.animationLength

                        if self._exportType == 'XFILE' and True:
                            kwXPortAnimationName += bckFileName + "," + str(startFrame) + "," + str(numberOfFrames)+ ",1;"
                            startFrame = endFrame + 1
                            animationCount += 1
                        else:
                            # saveNodes(self._bones, savePath)
                            # --b.DeleteAllKeys self._bones
                            # --rootFrameNode.ResetControllers() -- removes animations?
                            # --b.resetNodeAnim self._bones[1]
                            # loadMaxFile(saveMaxName)  # -- TODO: should only need to reset keys / clear animations
                            self._bones = rootFrameNode.RemapBones()

                            # -- rootFrameNode.ResetControllers() -- removes animations?

            frameItems = rootFrameNode.ToArray()
            if len(frameItems) != len(self._bones):
                raise ValueError("number of frameItems ("+str(len(frameItems))+
                                 ") must match number of bones (" +str(len(self._bones))+ ")")
            # --messageBox ((frameItems.count as string) + ":" + (self._bones.count as string))
            for i in range(len(frameItems)):
                if not refBoneRequiresDummyList[i]:
                    # -- bone doesn't require helpers
                    frameItems[i].RemoveDummyHelper()
            #for item in frameItems do
            #	print item
            #
            #for item in refBoneRequiresDummyList do
            #	print item
            # --messageBox (refBoneRequiresDummyList as string)
            bpy.context.scene.frame_start = 0
            bpy.context.scene.frame_end = startFrame


            apply_animation(self._bones, self.arm_obj, self.jnt.frames)

    def ExtractImages(self, force=False):
                
        imageType = ".tga"

        bmdViewExe = self._bmdViewPathExe + "BmdView.exe"
        bmdPath = getFilenamePath(self._bmdFilePath) + getFilenameFile(self._bmdFilePath)
        try:
            os.mkdir(bmdPath)
        except FileExistsError:
            pass
        try:
            os.mkdir(self._texturePath)
        except FileExistsError:
            pass
        # -- if no tga files are found then extract the
        tgaFiles = getFiles(self._texturePath + "*.tga")
        ddsFiles = getFiles(self._texturePath + "*.dds")

        self._images = tgaFiles+ddsFiles

        # -- cannot use shellLaunch because it doesn't wait for a return value
        # -- don't use DOSCommand. Doesn't support spaces in full exe path. e.g. C:Program files\
        # -- if using version before 2008 then use DOSCommand and set BmdView.exe into a known path

        if (len(tgaFiles) == 0 and len(ddsFiles) == 0) or force:
            self.TryHiddenDOSCommand("BmdView.exe \"" + self._bmdFilePath+ "\" \"" +
                                 self._texturePath+ "\\\"", self._bmdViewPathExe)

        ddsFiles = getFiles(self._texturePath + "*.dds")
        # -- create tga file and delete dds file
        for f in getFiles(self._texturePath + "*.dds"):
            addforcedname(f, f[:-4]+'.tga')

        # -- TODO: need to update BmdView.exe to process all file formats like BmdView2
        errorMessage = "Error generating dds / tga image file(s).\
                       Use BmdView2 to export the missing tga file(s)\
                       then delete the *.ERROR file(s) and run the importer again"
        errorFiles = getFiles(self._texturePath + "*.ERROR")
        for f in errorFiles:
            errorMessage += f + "\n"
        if len(errorFiles) != 0:
            MessageBox(errorMessage)
            return False

        return True

    def CreateBTPDataFile(self):

        bckFiles = getFiles(self._bmdDir + "..\\..\\btp\\*.btp")
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
            if firstLoop :
                firstLoop = False
            else:
                print("#", file=fBTP)
                print("%", matName, file=fBTP)
        print("</Materials>\n", file=fBTP)
        print("\t<Animations>\n", file=fBTP)
        for bckFile in bckFiles:
            self.textureAnim = Btp()
            self.textureAnim.LoadBTP(bckFile)
            print("\t\t<Animation>\n", file=fBTP)
            print("\t\t\t<Name>%</Name>\n", getFilenameFile(bckFile), file=fBTP)
            firstLoop = True
            for anim in self.textureAnim.anims:
                print("\t\t\t<Material>\n", file=fBTP)
                print("\t\t\t\t<MaterialIndex>%</MaterialIndex>\n", anim.materialIndex, file=fBTP)
                # -- print("\t\t\t\t<Name>%</Name>\n", anim.materialName, file=fBTP)
                animaitonKeys = ""
                for key in anim.keyFrameIndexTable:
                    if firstLoop :
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
        self.DEBUGVG = dvg
        self.use_nodes = use_nodes
        if exportTextures:
            self._texturePrefix = ""  # XCX useless prefix (maxscript arctefact to pack textures?)
        else:
            self._texturePrefix = "_"
        self._bckPaths.append("..\\..\\bck\\*.bck")
        self._bckPaths.append("..\\..\\bcks\\*.bck")
        self._bckPaths.append("..\\..\\scrn\\*.bck")
        # --self._createBones = False
        self._includeScaling = includeScaling
        # --self._exportType=XFILE
        self._exportType = exportType
        self.imtype = imtype
        texhelper.MODE = imtype

        self._allowTextureMirror = allowTextureMirror
        self._forceCreateBones = forceCreateBones
        self._loadAnimations = loadAnimations
        self._boneThickness = boneThickness
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
