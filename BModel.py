#! /usr/bin/python3    from Math import *
from .BinaryReader import *
from .Vector3 import *
from .Matrix44 import *
from .Inf1 import *
from .Vtx1 import *
from .Shp1 import *
from .Jnt1 import *
from .Evp1 import *
from .Drw1 import *
from .Bck import *
from .Mat3 import *
from .Tex1 import *
from .StringHelper import *
from .FrameNode import *
# from .ReassignRoot import *
from .Btp import *
from os import path as OSPath
from .maxheader import *
import math
from .texhelper import newtex, getTexImage, showTextureMap, getTexSlot, newUVlayer, addforcedname
import mathutils
from .materialhelper import add_vcolor, add_material


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

    # -- HiddenDOSCommand cmd startpath:scriptPath
    # -- already defined in maxscript 2008
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

    # -- TODO: use matrix math instead
    #
    #fn RotateAroundWorld obj rotation =
    #(
    #	
    #	 origParent =  obj.parent
    #	 d = dummy()
    #	obj.parent = d
    #	rotate d  rotation
    #	--delete d
    #	--if (origParent != undefined) then
    #	--	obj.parent = origParent
    #	
    #),
    #    # <function>

    # <function>

    # <function>

    # <function>"""

    def __init__(self):  # GENERATED!
        self.vtx = None
        self.DEBUGvgroups={}
        self._bmdFilePath = ""
        self._runExtractTexturesCmd= True
        self._currMaterialIndex= 1  # XCX??
        self.tverts= [[],[],[],[],[],[],[],[]]
        self.tv_to_v_f = [[],[],[],[],[],[],[],[]]  # texVerts to vertices_faces
        self._createBones= True
        self._exportType='XFILE'
        self._boneThickness= 10
        self.vertices= []
        self._bones= []
        self._bckPaths= []
        self._reverseFaces= True
        self._loadAnimations= True
        self.faceIndex = 0
        self._materialIDS= []
        self._includeScaling= False
        self._parentBoneIndexs= []
        self.tFaces= [[],[],[],[],[],[],[],[]]
        self.faces= []
        self.vertexMultiMatrixEntry= []
        self._allowTextureMirror= False
        self.normals = []
        self.vcFaces = []
        self._forceCreateBones= False
        self._subMaterials = []
        self._iconSize = 100

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
        except:
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
            rev.append(inputArray[i-1]) # corrected!
            i -= 1
        # -- inputArray = rev doesn't work
        return rev

    def BuildSingleMesh(self):
        # -----------------------------------------------------------------
        # -- mesh
        if self._reverseFaces:
            self.faces = self.ReverseArray(self.faces)
            self._materialIDS = self.ReverseArray(self._materialIDS)
            for uv in range(8):
                self.tFaces[uv] = self.ReverseArray(self.tFaces[uv])
            self.vcFaces = self.ReverseArray(self.vcFaces)

        # -- TODO: should never have undefined materials
        for i in range(len(self._materialIDS)):
            if self._materialIDS[i] is None:
                self._materialIDS[i] = -1  # -- not found index

        # -- FIX: Fill missing material IDs

        if len(self._materialIDS) > 0:
            for i in range(len(self._materialIDS), len(self.faces)):
                self._materialIDS.append(-1)
        else:
            self._materialIDS = [-1] * len(self.faces)

        modelMesh = bpy.data.meshes.new(getFilenameFile(self._bmdFilePath))
        modelMesh.from_pydata(self.vertices, [], self.faces)
        modelMesh.update()
        modelObject = bpy.data.objects.new(getFilenameFile(self._bmdFilePath), modelMesh)
        bpy.context.scene.objects.link(modelObject)
        bm_to_pm = []  # index shifter: enter bmd mat index, get blender mat index
        for i in range(len(self._subMaterials)):
            bm_to_pm.append(add_material(modelObject, self._subMaterials[i]))
        for num, com in enumerate(self._materialIDS):  # assign materials to faces
            modelMesh.polygons[num].material_index = bm_to_pm[com -1]
        #for com in self._materialIDS:
        #    add_material(modelObject, com)


        #ClassOf modelMesh

        # -- tvert self.faces
        # --Set self.texcoord self.faces

        if len(self._materialIDS) > 0:  # - FIX: Do not set texcoord faces when there are no textures on model.
            pass
            # buildTVFaces(modelMesh, False) # XCX

        for uv in range(8):
            if len(self.tverts[uv]) and len(self.tFaces[uv]):
                newUVlayer(modelMesh, self.tverts[uv], self.tFaces[uv], self.faces, self.tv_to_v_f[uv])

        # -- set self.normals [no effect?]

        if len(self.normals) != len(self.vertices):
            pass
            # --messageBox "Invalid self.normals?"	-- FIX: IGNORE INVALID NORMALS TO ALLOW IMPORT SOME MODELS
            # --raise ValueError("Invalid self.normals?"

        for i in range(len(self.vertices)):
            if self.normals[i] is not None:
                modelMesh.vertices[i].normal = mathutils.Vector(self.normals[i])
        modelMesh.update()  # XCX

        if len(self.vtx.colors) and len(self.vtx.colors[0]):  #- has colors? fixed.
            add_vcolor(modelMesh, self.vtx.colors[0])
            if len(self.vtx.colors) > 1 and len(self.vtx.colors[1]):  # fixed
                add_vcolor(modelMesh, self.vtx.colors[1])  # fixed

        # update(modelMesh) # XCX

        # -----------------------------------------------------------------
        # -- skin

        if self._createBones:
            # update modelMesh
            # max modify mode
            act_bk = bpy.context.active_object
            bpy.context.scene.objects.active = modelObject
            mod = modelObject.modifiers.new('Armature', type='ARMATURE')
            arm = bpy.data.armatures.new(modelObject.name+'_bones')
            self.arm_obj = arm_obj = bpy.data.objects.new(modelObject.name+'_armature', arm)
            bpy.context.scene.objects.link(arm_obj)
            modelObject.parent = arm_obj
            mod.object = arm_obj
            bpy.context.scene.update()

            bpy.context.scene.objects.active = arm_obj
            bpy.ops.object.mode_set(mode='EDIT')
            for bone in self._bones:
                arm.edit_bones.new(bone.name.fget())
                if isinstance(bone.parent.fget(), Pseudobone):
                    if bone.parent.fget().name.fget() not in [temp.name.fget() for temp in self._bones]:
                        tempbone = arm.edit_bones.new(bone.parent.fget().name.fget())
                        tempbone.parent = arm.edit_bones[bone.parent.fget().parent.fget().name.fget()]
                        tempbone.head = mathutils.Vector(bone.parent.fget().position)
                        tempbone.tail = mathutils.Vector(bone.parent.fget().endpoint)
            for bone in self._bones:
                realbone = arm.edit_bones[bone.name.fget()]
                if isinstance(bone.parent.fget(), Pseudobone):
                    realbone.parent = arm.edit_bones[bone.parent.fget().name.fget()]
                realbone.head = mathutils.Vector(bone.position)  #mathutils.Vector((0,0,0))
                realbone.tail = mathutils.Vector(bone.endpoint)  #mathutils.Vector((0,0,1))
                modelObject.vertex_groups.new(bone.name.fget())
                # skinOps.addBone(mysk, bone, 0) # XCX DONE?
            bpy.context.scene.update()
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.scene.objects.active = act_bk

            if len(self.vertexMultiMatrixEntry) != len(self.vertices):
                MessageBox("Invalid skin")
                raise ValueError("E")

            for i in range(len(self.vertices)):
                for num, vg_id in enumerate(self.vertexMultiMatrixEntry[i].indices):
                    modelObject.vertex_groups[vg_id-1].add([i], self.vertexMultiMatrixEntry[i].weights[num], 'REPLACE')
                # -- Don't use setVertexWeights. Has issues with existing bone weights (mainly root bone)
                #skinOps.ReplaceVertexWeights(mysk,  i, vertexMultiMatrixEntry[i].indices,
                #                             vertexMultiMatrixEntry[i].weights)  # XCX
            for com in self.DEBUGvgroups.keys():  # DEBUG vertex groups to fix UVs
                vg = modelObject.vertex_groups.new(com)
                vg.add(self.DEBUGvgroups[com], 1, 'REPLACE')
            modelMesh.update()


        # -- freeze model by default
        # --freeze  modelMesh	-- DO NOT FREEZE MODEL BY DEFAULT

        return modelMesh

    def LoadModel(self, filePath):
                
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
        strTag = "" # -- 4 characters
        iTell = 0

        self.inf = Inf1()
        self.vtx = Vtx1()
        self.shp = Shp1()
        self.jnt = Jnt1()
        self.evp = Evp1()
        self.drw = Drw1()
        self._mat1 = Mat3()
        self.tex = Tex1()

        while strTag != "TEX1":  #- not br.EOF() --
            br.SeekCur(iSize)
            streamPos = br.Position()
            strTag = br.ReadFixedLengthString(4)
            iSize = br.ReadDWORD()

            # -- print (strTag + ":" + (streamPos as string))

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
            elif strTag == "TEX1":
                self.tex.LoadData(br)
            else:
                raise ValueError(strTag+' tag not recognized')
            br.SeekSet(streamPos)

        self.tex.LoadData(br)
        br.Close()

    def DrawVerts(self):
        # delete $* # XCX
        for vec in self.vtx.positions:
            # p = bpy.types.MeshVertex(pos=[vec.x, vec.y, vec.z], cross=on, Box=off)
            print(vec)

    def Mad(self, r, m, f):
        for j in range(3):
            for k in range(4):
                r.m[j][k] += f * m.m[j][k]
        return r

    def LocalMatrix(self, i):
        #- returns Matrix44f
        # --s =  Matrix44f()
        # --s.LoadScale self.jnt.frames[i].sx self.jnt.frames[i].sy self.jnt.frames[i].sz

        # --TODO: I don't  know which of these two return values are the right ones
        # --(if it's the first, then what is scale used for at all?)

        # --looks wrong in certain circumstances...
        return self.jnt.matrices[i]  # -- this looks better with vf_064l.bdl (from zelda)
        # return bm.jnt1.matrices[i]*s   # -- this looks a bit better with mario's bottle_in animation

    def DrawBatch(self, index, def_):
        currBatch = self.shp.batches[index]
        batchid = index

        if not currBatch.attribs.hasPositions :
            raise ValueError("found batch without positions")


        # --firstTextCoordIndex = 1

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

        for uv in range(8):
            if self.vtx.texCoords[uv] is not None:
                while len(self.tverts) <= uv:
                    self.tverts.append([])
                for i_temp in range(len(self.vtx.texCoords[uv])):
                    tvert = self.vtx.texCoords[uv][i_temp]
                    while len(self.tverts[uv]) <= i_temp:
                        self.tverts[uv].append(None)
                    self.tverts[uv][i_temp] = [tvert.s, -tvert.t+1, 0]  # -- flip uv v element

        for packnum, currPacket in enumerate(currBatch.packets):
            for n in range(len(currPacket.matrixTable)):
                index = currPacket.matrixTable[n]
                if index != 0xffff:  # -- //this means keep old entry
                    if self.drw.isWeighted[index]:  # corrected
                        # --TODO: the EVP1 data should probably be used here,
                        # --figure out how this works (most files look ok
                        # --without this, but models/ji.bdl is for example
                        # --broken this way)
                        # --matrixTable[n] = def_;

                        # --the following _does_ the right thing...it looks
                        # --ok for all files, but i don't understand why :-P
                        # --(and this code is slow as hell, so TODO: fix this)

                        # --NO idea if this is right this way...
                        m = Matrix44()
                        m.LoadZero()

                        mm = self.evp.weightedIndices[self.drw.data[index]]  # -- get MultiMatrix # corrected
                        singleMultiMatrixEntry = MultiMatrix()

                        for r in range(len(mm.weights)):
                            singleMultiMatrixEntry.weights[r] = mm.weights[r]
                            singleMultiMatrixEntry.indices[r] = mm.indices[r]  # corrected (r]+1) # -- (drw.data[mm.indices[r]+ 1] + 1) -- bone index
                            #--  sm1 = evp.matrices[mm.indices[r]] -- const Matrix44f
                            #--  messageBox (mm.indices as string)
                            #--if (mm.indices[r] != 0) then
                            #-- (
                            sm1 = self.evp.matrices[mm.indices[r]]  # corrected(r]+1) # -- const Matrix44f
                            sm2 = self.LocalMatrix(mm.indices[r])  # corrected (r]+1)
                            sm3 = sm2.Multiply(sm1)
                            #
                            #   sm1 = evp.matrices[mm.indices[r]] -- const Matrix44f
                            #sm2 = LocalMatrix mm.indices[r]
                            #sm3 = sm2.Multiply sm1*/
                            #)
                            #else
                            #--	sm3 = (LocalMatrix mm.indices[r] )

                            self.Mad(m, sm3, mm.weights[r])

                        multiMatrixTable[n] = singleMultiMatrixEntry
                        m.m[3][3] = 1  # fixed
                        matrixTable[n] = m
                        isMatrixWeighted[n] = True
                    else:
                        while len(matrixTable) <= n:
                            matrixTable.append(None)
                        while len(isMatrixWeighted) <= n:
                            isMatrixWeighted.append(None)
                        matrixTable[n] = self.jnt.matrices[self.drw.data[index]]  # corrected x2
                        isMatrixWeighted[n] = False

                        singleMultiMatrixEntry = MultiMatrix()
                        singleMultiMatrixEntry.weights = [1]
                        singleMultiMatrixEntry.indices = [self.drw.data[index]]  #corrected x2  # -- bone index

                        while len(multiMatrixTable) <= n:
                            multiMatrixTable.append(None)
                        multiMatrixTable[n] = singleMultiMatrixEntry
                        # -- end if drw.isWeighted[index] then

                # -- end if index != 0xffff then -- //this means keep old entry
            # end for index in currPacket.matrixTable do
            # --if no matrix index is given per vertex, 0 is the default.
            # --otherwise, mat is overwritten later.
            mat = matrixTable[0]  # corrected
            multiMat = multiMatrixTable[0]
            for primnum, currPrimitive in enumerate(currPacket.primitives):
                for m in range(len(currPrimitive.points)):
                    posIndex = currPrimitive.points[m].posIndex   # fixed
                    # -- TODO: texcoords 1-7, color1 #XCX
                    if currBatch.attribs.hasMatrixIndices:
                        mat = matrixTable[(currPrimitive.points[m].matrixIndex//3)]  # fixed
                        if currPrimitive.points[m].matrixIndex % 3:
                            MessageBox("WARNING: if (mod currPrimitive.points[m].matrixIndex 3) != 0 then " + str(currPrimitive.points[m].matrixIndex))
                        multiMat = multiMatrixTable[(currPrimitive.points[m].matrixIndex//3)]  # fixed

                    if currBatch.attribs.hasNormals:
                        #if len(self.vtx.normals) > currPrimitive.points[m].normalIndex:
                        normal =self.vtx.normals[(currPrimitive.points[m].normalIndex)]  # fixed
                        #else:
                        #    normal = Vector3()
                        #    normal.setXYZ(0,0,-1) # easy to spot errors afterwards
                        while len(self.normals) <= posIndex:
                            self.normals.append(None)
                        self.normals[posIndex] = normal.ToMaxScriptPos()

                    while len(self.vertexMultiMatrixEntry) <= posIndex:
                        self.vertexMultiMatrixEntry.append(None)
                    self.vertexMultiMatrixEntry[posIndex] = multiMat
                    newPos = mat.MultiplyVector(self.vtx.positions[posIndex])
                    while len(self.vertices) <= posIndex:
                        self.vertices.append(None)
                    self.vertices[posIndex] = [newPos.x, -newPos.z, newPos.y] # -- flip order
                if currPrimitive.type == 0x98:  # - strip
                    for m in range(len(currPrimitive.points)-2):
                        posIndex1 = currPrimitive.points[m].posIndex  # fixed
                        posIndex2 = currPrimitive.points[m + 1].posIndex  # fixed
                        posIndex3 = currPrimitive.points[m + 2].posIndex  # fixed

                        # XCX DEBUG (create debug V groups)
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
                        if m % 2 == 0:  # -- even
                            self.faces[self.faceIndex] = [posIndex1, posIndex2, posIndex3]
                        else:
                            self.faces[self.faceIndex] = [posIndex3, posIndex2, posIndex1] # -- reverse

                        for uv in range(8):
                            if len(self.tFaces) <= uv:
                                self.tFaces.append([])
                            if currBatch.attribs.hasTexCoords[uv]:
                                t1Index = currPrimitive.points[m].texCoordIndex[uv]  # fixed
                                t2Index = currPrimitive.points[m + 1].texCoordIndex[uv]  # fixed
                                t3Index = currPrimitive.points[m + 2].texCoordIndex[uv]  # fixed
                                while len(self.tFaces[uv]) <= self.faceIndex:
                                    self.tFaces[uv].append(None)
                                if m % 2 == 0:  # -- even
                                    self.tFaces[uv][self.faceIndex] = [t1Index , t2Index , t3Index ]
                                else:
                                    self.tFaces[uv][self.faceIndex] = [t3Index , t2Index , t1Index ] # -- reverse
                                # XCX new UV method
                                while len(self.tv_to_v_f[uv]) <= max(t1Index, t2Index, t3Index):
                                    self.tv_to_v_f[uv].append(None)
                                self.tv_to_v_f[uv][t1Index] = (posIndex1, self.faceIndex)
                                self.tv_to_v_f[uv][t2Index] = (posIndex2, self.faceIndex)
                                self.tv_to_v_f[uv][t3Index] = (posIndex3, self.faceIndex)
                                while len(self._materialIDS) <= self.faceIndex:
                                    self._materialIDS.append(None)
                                self._materialIDS[self.faceIndex] = self._currMaterialIndex

                        # -- vertex colors
                        while len(self.vcFaces) <= self.faceIndex:
                            self.vcFaces.append(None)
                        if currBatch.attribs.hasColors[0]:  # fixed
                            c1Index = currPrimitive.points[m].colorIndex[0]  # fixed x2
                            c2Index = currPrimitive.points[m + 1].colorIndex[0]  # fixed x2
                            c3Index = currPrimitive.points[m + 2].colorIndex[0]  # fixed x2

                            if m % 2 == 0:  # -- even
                                self.vcFaces[self.faceIndex] = [c1Index, c2Index , c3Index ]
                            else:
                                self.vcFaces[self.faceIndex] = [c3Index, c2Index , c1Index ] # -- reverse
                        else:
                            self.vcFaces[self.faceIndex] = None
                        self.faceIndex += 1
                # -- GL_TRIANGLE_STRIP:

                elif currPrimitive.type == 0xa0:
                    MessageBox("NYI: fan")
                # -- GL_TRIANGLE_FAN
                else:
                    MessageBox("unknown primitive type")
                # -- end if currPrimitive.type == 0x98 then -- strip
            # -- end for currPrimitive in currPacket.primitives do
         # -- end for currPacket in currBatch.packets do

    def FrameMatrix(self, f):
        t = Matrix44()
        rx = Matrix44()
        ry = Matrix44()
        rz = Matrix44()
        s = Matrix44()

        t.LoadTranslateLM(f.t.x, f.t.y, f.t.z)
        rx.LoadRotateXLM((f.rx / 360.) * 2 *math.pi)
        ry.LoadRotateYLM((f.ry / 360.) * 2 *math.pi)
        rz.LoadRotateZLM((f.rz / 360.) * 2 *math.pi)
  
        res = Matrix44()
        res.LoadIdentity()
        res = t.Multiply(rz.Multiply(ry.Multiply(rx)))
        return res

    def CreateFrameNodes(self, j, d, parentMatrix, parentFrameNode):
        b1 = False
        effP = parentMatrix
        i = j
        fNode = parentFrameNode

        while i < len(self.inf.scenegraph):
                        
            n = self.inf.scenegraph[i]  # fixed
            if n.type != 1 and b1:
                b1 = False
                effP = parentMatrix   # -- prevents fixed chain
                fNode = parentFrameNode

            if n.type == 0x10:
                # --joint
                f = self.jnt.frames[n.index]  # -- arrays start at index 1 in maxscript # fixed
                effP = effP.Multiply(self.FrameMatrix(f))
                while len(self.jnt.matrices) <= n.index:
                    self.jnt.matrices.append(None)
                self.jnt.matrices[n.index] = effP  # -- effP.Multiply(FrameMatrix(f)) # fixed

                fNode = FrameNode()
                fNode.f = f
                fNode.name = f.name

                fNode.startPoint = (parentMatrix.MultiplyVector(f.t)).ToMaxScriptPos()
                fNode.parentFrameNode = parentFrameNode
                fNode.effP = effP
                # --fNode.name = self._bmdFileName + "_" + f.name	-- FIX: DO NOT ADD FILENAME PREFIX TO BONES
                parentFrameNode.children.append(fNode)
                b1 = True
            elif n.type == 1:
                i += self.CreateFrameNodes(i+1, d+1, effP, fNode) # -- note: i and j start at 1 instead of 0
            elif n.type == 2:
                return i - j + 1 # -- note: i and j start at 1 instead of 0
            i += 1
        return-1

    def CreateCharacter(self, rootFrameNode):
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
            bone.setSkinPose()
        chr.displayRes = 1  # -- hide bones
        #assemblyMgr.Open(chr)
        return chr

    def DrawScenegraph(self, j, call_depth, parentMatrix):

        b1 = False
        effP = parentMatrix  # --.Copy()
        i = j
        while i < len(self.inf.scenegraph):
            n = self.inf.scenegraph[i]
            # --print (n.type as string)
            if n.type != 1 and b1:
                b1 = False
                effP = parentMatrix  # --.Copy() -- prevents fixed chain

            if n.type == 0x10:  # -joint
                effP = self.jnt.matrices[n.index]  # -- setup during CreateBones # corrected
                b1 = True
            elif n.type == 0x11:
                matName = self._mat1.stringtable[n.index]  # correced
                mat = self._mat1.materials[self._mat1.indexToMatIndex[n.index]]  # corrected *2
                stage = mat.texStages[0]  # corrected
                self.textureName = ""
                if stage != 0xffff:
                    v2 = self._mat1.texStageIndexToTextureIndex[stage]  # -- undefined if stage = 0xffff
                else:
                    v2 = None

                if stage != 0xffff:
                    # -- v2 used latter. value is undefined if stage == 0xffff
                    self.textureName = self.tex.stringtable[v2]

                    # --self.textureName = matName
                    fileName = self._texturePath + self._texturePrefix + self.textureName + ".tga"
                    bmpFound = OSPath.exists(fileName) or OSPath.exists(fileName[:-4]+'.dds')  # two image types!

                    # -- messageBox fileName
                    self._currMaterial = bpy.data.materials.new("temp_name_whatsoever")  #name will be erased afterwards, in a subcall
                    newtex(fileName, 'DIFFUSE', self._currMaterial)
                    img = getTexImage(self._currMaterial, fileName)

                    # --gc()
                    bmp = None
                    hasAlpha = False
                    if bmpFound:
                        alp = 0
                        for p in range(0, len(img.pixels), 4):  # pixels stored as individual channels
                            if img.pixels[p+3] != 1:  # only get alpha
                                alp = img.pixels[p+3]
                                hasAlpha = True
                                break
                    else:
                        # -- make it easier to see invalid self.textures
                        self._currMaterial.diffuse_color = mathutils.Color((1,0,0))

                    if hasAlpha:
                        #self._currMaterial.twoSided = True # -- anything with alpha is always two sided?
                        newtex(fileName, 'ALPHA', self._currMaterial)

                    showTextureMap(self._currMaterial)  # -- display self.texture in view
                    self._currMaterial.name = matName

                    while self._currMaterialIndex >= len(self._subMaterials):  # create one more slot
                        self._subMaterials.append(None)
                    self._subMaterials[self._currMaterialIndex] = self._currMaterial

                    # -- display in material editor?
                    # -- meditMaterials[self.self._currMaterialIndex + 1] = self._currMaterial
                    self._currMaterialIndex += 1

                    # -- messageBox (matName + (self.tex.self.texHeaders[v2].wrapS as string) + "+" + (self.tex.self.texHeaders[v2].wrapT as string))
                    # -- NOTE: check ash.bmd for case when wrapS=2 and wrap=2. u_offset = 0.5 and V_offset = -0.5 [note negative on v]

                    if bmpFound:
                        if self.tex.texHeaders[v2].wrapS == 0:#- clamp to edge? Needs testing. Cannot use .U_Mirror = False and .U_Tile = False. If WrapS == 0 then has Alpha?
                            pass
                        elif self.tex.texHeaders[v2].wrapS == 1:  #- repeat (default)
                            pass
                        elif self.tex.texHeaders[v2].wrapS == 2:
                            self._currMaterial.name += "_U" # -- add suffix to let the modeler know where mirror should be used
                            if self._allowTextureMirror:
                                getTexSlot(self._currMaterial, fileName).scale[0] = -1
                                # self._currMaterial.diffusemap.coords.U_Tile = False
                                #self._currMaterial.diffusemap.coords.U_offset = 0.5
                                #self._currMaterial.diffusemap.coords.U_Tiling = 0.5
                        else:
                            raise ValueError("Unknown wrapS "+ str(self.tex.texHeaders[v2].wrapS))
                        if self.tex.texHeaders[v2].wrapT == 0:  # - clamp to edge? Needs testing
                            pass
                        elif self.tex.texHeaders[v2].wrapT == 1 :  #- repeat (default)
                            pass
                            #					self._currMaterial.diffusemap.coords.V_Mirror = False
                            #					self._currMaterial.diffusemap.coords.V_Tile = True
                            #
                            #					if (hasAlpha) then
                            #					(
                            #						self._currMaterial.opacityMap.coords.V_Mirror = False
                            #						self._currMaterial.opacityMap.coords.V_Tile = True
                            #					)
                        elif self.tex.texHeaders[v2].wrapT == 2:
                            self._currMaterial.name += "_V" # -- add suffix to let the modeler know where mirror should be used
                            if self._allowTextureMirror:
                                getTexSlot(self._currMaterial, fileName).scale[1] = -1
                                # self._currMaterial.diffusemap.coords.V_Tile = False
                                # self._currMaterial.diffusemap.coords.V_offset = 0.5
                                # self._currMaterial.diffusemap.coords.V_Tiling = 0.5
                        else:
                            raise ValueError("Unknown wrapT " + str(self.tex.texHeaders[v2].wrapS))
            elif n.type == 0x12:  # - type = 18
                self.DrawBatch(n.index, effP)  # fixed
            elif n.type == 1:
                i += self.DrawScenegraph(i + 1, call_depth + 1, effP) # -- note: i and j start at 1 instead of 0
            elif n.type == 2:
                return i- j + 1 # -- note: i and j start at 1 instead of 0
            i += 1
        return -1

    def RotateAroundWorld(self, obj, rotation):
        print(rotation, type(rotation))
        origParent = obj.parent
        d = bpy.data.new('UTEMP_PL', None)
        d.location = mathutils.Vector((0,0,0))
        obj.parent = d
        d.rotation_euler = mathutils.Euler(rotation, 'XYZ')
        act_bk = bpy.ops.active
        bpy.ops.active = d
        bpy.ops.object.transform_apply(rotation = True)
        bpy.ops.active = obj
        bpy.ops.object.transform_apply(rotation = True)
        bpy.ops.active = act_bk
        obj.parent = None
        bpy.data.objects.remove(d)
        # --delete d
        # --if (origParent != undefined) then
        # --	obj.parent = origParent

    def DrawScene(self):  # XCX create armature here
        # delete $* XCX
        m = Matrix44()
        _frameMatrix = m.GetIdentity()
        rootFrameNode = FrameNode()
        identity = m.GetIdentity()
        self.CreateFrameNodes(0, 0, identity, rootFrameNode)
        # -- FIX: Force create bone option allows to generate bones independently of their count
        if len(rootFrameNode.children) == 1 and len(rootFrameNode.children[0].children) == 0:  # fixed
            self._createBones = False
        origWorldBonePos = None
        if self._createBones:
            self._bones = rootFrameNode.CreateBones(self._boneThickness, "")
            if self._includeScaling:  # - scaling cases IK and number of bones issue
                rootFrameNode.FixBones(self._boneThickness)

            self._parentBoneIndexs = rootFrameNode.CreateParentBoneIndexs()
            origWorldBonePos = self._bones[0].position  # fixed

            # -- easier than recalculating all bone transforms
            d = mathutils.Vector()
            self._bones[0].parent.fset(d)  # fixed
            d.rotate(mathutils.Euler((90, 0, 0), 'XYZ'))
        i = m.GetIdentity()

        # -----------------------------------
        # -- reverse items
                    # XCX?
                #	revList = #()
                #	i = self.inf.scenegraph.count
                #	while (i > 0) do
                #	(
                #		append revList (self.inf.scenegraph[i])
                #		i -= 1
                #	)
                #	self.inf.scenegraph = revList
        # -----------------------------------

        self.DrawScenegraph(0, 0, i)
        modelMesh = self.BuildSingleMesh()

        chr = None
        characterPos = None
        if self._createBones and self._exportType != 'XFILE':
            chr = self.CreateCharacter(rootFrameNode)
            # --RotateAroundWorld  chr (EulerAngles 90 0 0)

            # -- Rotate Character assembly upwards and swap hierarchy for Point and Character
            chr.rotation_euler = mathutils.Euler((90, 0, 0), 'XYZ')
            self._bones[0].parent.fset(d)  # fixed
            d.parent.fset(chr)
        # --RotateAroundWorld modelMesh (EulerAngles 90 0 0) -- e.g. stage, object
        if self._createBones:  # XCX is this needed?
            try:
                dirCreated = os.mkdir(self._bmdDir + "\\Animations")
            except FileExistsError: pass
        bckFiles = []
        #saveMaxName = self._bmdDir + self._bmdFileName + ".max" # -- .chr?
        errMsg = ""
        # max tool zoomextents all  # XCX
        for bone in self._bones:
            pass# XCX what is the rest position?
            #bone.setSkinPose()
        #fileProperties.addProperty  custom "exportAnimation" False
        # --self._createBones = True
        if self._createBones and self._loadAnimations:
            # fileProperties.addProperty  custom "exportAnimation" True
            _onlyExportAnimations = False
            if _onlyExportAnimations:
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

            kwXPortAnimationName = ""
            animationCount = 1  # -- default pose at frame 1
            if self._exportType != 'XFILE':
                pass  # XCX
                #saveMaxFile(saveMaxName)
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
                    b = Bck()
                    b.LoadBck(f)
                    if len(b.anims) != len(self._bones):
                        errMsg += bckFileName + "\n"
                    else:
                        endFrame = None
                        b.AnimateBoneFrames(startFrame, self._bones, 1,
                                            [origWorldBonePos.x, origWorldBonePos.y, origWorldBonePos.z],
                                            self._exportType, refBoneRequiresDummyList, self._includeScaling)

                        numberOfFrames = b.animationLength

                        if b.animationLength <= 0:
                            numberOfFrames= 1
                        endFrame = startFrame + b.animationLength

                        if self._exportType == 'XFILE':
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

            if self._exportType == 'XFILE':   # XCX
                kwXPortAnimationName = str(animationCount) + ";"+ kwXPortAnimationName
                # --messageBox kwXPortAnimationName
                # fileProperties.addProperty(custom, "allAnimations", kwXPortAnimationName)
                bpy.context.scene.frame_start = 0
                bpy.context.scene.frame_end = startFrame
                # --messageBox (self._bmdDir + self._bmdFileName + ".x" )

            # XCX XCX pose bones here!
            for com in self._bones:
                name = com.name.fget()
                posebone = self.arm_obj.pose.bones[name]
                bpy.context.scene.frame_current = 0
                posebone.keyframe_insert('location')
                posebone.keyframe_insert('rotation_euler')
                posebone.keyframe_insert('scale')
                for frame in set(com.position_kf.keys()).union(
                             set(com.rotation_kf.keys())).union(
                             set(com.scale_kf.keys())):
                    bpy.context.scene.frame_current = frame

                    if frame in com.position_kf.keys():
                        vct = com.position_kf[frame]
                        if vct.x != math.nan:
                            posebone.keyframe_insert('location')
                            posebone.location[0] = vct.x
                        if vct.y != math.nan:
                            posebone.keyframe_insert('location')
                            posebone.location[1] = vct.y
                        if vct.z != math.nan:
                            posebone.keyframe_insert('location')
                            posebone.location[2] = vct.z
                    if frame in com.rotation_kf.keys():
                        vct = com.rotation_kf[frame]
                        if vct.x != math.nan:
                            posebone.keyframe_insert('rotation_euler')
                            posebone.rotation_euler[0] = vct.x
                        if vct.y != math.nan:
                            posebone.keyframe_insert('rotation_euler')
                            posebone.rotation_euler[1] = vct.y
                        if vct.z != math.nan:
                            posebone.keyframe_insert('rotation_euler')
                            posebone.rotation_euler[2] = vct.z
                    if frame in com.scale_kf.keys():
                        vct = com.scale_kf[frame]
                        if vct.x != math.nan:
                            posebone.keyframe_insert('scale')
                            posebone.scale[0] = vct.x
                        if vct.y != math.nan:
                            posebone.keyframe_insert('scale')
                            posebone.scale[1] = vct.y
                        if vct.z != math.nan:
                            posebone.keyframe_insert('scale')
                            posebone.scale[2] = vct.z

        #if self._exportType=='XFILE':
            #exportFile (self._bmdDir + self._bmdFileName + ".x", noPrompt) # -- selectedOnly:True
            # saveMaxFile saveMaxName # XCX

        #else:
            #loadMaxFile saveMaxName  # XCX
            #animationRange = interval(0, 100) # -- not required

    def ExtractImages(self):
                
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

        # -- cannot use shellLaunch because it doesn't wait for a return value
        # -- don't use DOSCommand. Doesn't support spaces in full exe path. e.g. C:Program files\
        # -- if using version before 2008 then use DOSCommand and set BmdView.exe into a known path

        if len(tgaFiles) == 0 and len(ddsFiles) == 0:
            self.TryHiddenDOSCommand("BmdView.exe \"" + self._bmdFilePath+ "\" \"" +
                                 self._texturePath+ "\\\"", self._bmdViewPathExe)
        #classof(tgaFiles)  #XCX
        ddsFiles = getFiles(self._texturePath + "*.dds")
        # -- create tga file and delete dds file
        for f in getFiles(self._texturePath + "*.dds"):
            addforcedname(f, f[:-4]+'.tga')
            #img = openBitMap(f)  # XCX
            #saveFileName = self._texturePath + getFilenameFile(f) + ".tga"
            #destImg = copy(img)
            #destImg.filename = saveFileName
            #save(destImg) # -- cannot save img directly (requires copy to remove dds format)
            #os.remove(f)
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

    def Import(self, filename, boneThickness, allowTextureMirror, forceCreateBones, loadAnimations, exportTextures, exportType, includeScaling):
        if exportTextures:
            self._texturePrefix = ""
        else:
            self._texturePrefix = "_"
        self._bckPaths.append("..\\..\\bck\\*.bck")
        self._bckPaths.append("..\\..\\bcks\\*.bck")
        self._bckPaths.append("..\\..\\scrn\\*.bck")
        # --self._createBones = False
        self._includeScaling = includeScaling
        # --self._exportType=XFILE
        self._exportType = exportType

        self._allowTextureMirror = allowTextureMirror
        self._forceCreateBones = forceCreateBones
        self._loadAnimations = loadAnimations
        self._boneThickness = boneThickness
        print(filename)
        self.LoadModel(filename)

        bmdPath = "".join(OSPath.split(self._bmdFilePath)) + "\\"  # generates dir name from file name?
        try:
            os.mkdir(bmdPath)
        except FileExistsError:
            pass
        try:
            os.mkdir(self._texturePath)
        except FileExistsError:
            pass

        if (not exportTextures) or (exportTextures and self.ExtractImages()):
            self.DrawScene()
        self.CreateBTPDataFile()