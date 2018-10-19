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
import logging
log = logging.getLogger('bpy.ops.import_mesh.bmd.main')

if LOADED:
    for module in (BinaryReader, BinaryWriter, Mat44, Inf1, Vtx1, Shp1, Jnt1, Evp1, Drw1,
                   Bck, Mat3, Tex1, Mdl3, Btp, MaxH, TexH, MatH, PBones):
        reload(module)

else:
    from . import (
        BinaryReader, BinaryWriter,
        Matrix44 as Mat44,
        Inf1, Vtx1, Shp1, Jnt1, Evp1, Drw1, Bck, Tex1, Btp, Mdl3, Mat3,
        # materialV2OLD as M2O,
        maxheader as MaxH,
        texhelper as TexH,
        materialhelper as MatH,
        pseudobones as PBones
    )

del LOADED


class Prog_params:
    def __init__(self, filename, boneThickness, allowTextureMirror, forceCreateBones, loadAnimations, animationType,
                 packTextures, includeScaling, imtype, dvg, use_nodes=False, validate_mesh=False):
        self.filename = filename
        self.boneThickness = boneThickness
        self.allowTextureMirror = allowTextureMirror
        self.forceCreateBones = forceCreateBones
        self.loadAnimations = loadAnimations
        self.animationType = animationType
        self.packTextures = packTextures
        self.includeScaling = includeScaling
        self.imtype = imtype
        self.DEBUGVG = dvg
        self.use_nodes = use_nodes
        self.validate_mesh = validate_mesh
        # secondary parameters (computed later on)
        self.createBones = True


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
    # <variable _allowTextureMirror>
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
        self.faceIndex = 0
        self._materialIDS = []
        self.vertexMultiMatrixEntry = []
        self._allowTextureMirror = False
        self.normals = []
        self._subMaterials = []

    def SetBmdViewExePath(self, value):
        if not OSPath.exists(value + "BmdView.exe"):
            log.fatal(self._bmdViewPathExe + "BmdView.exe not found. Place the BmdView.exe file"
                                                   "(included in the zip file) next to this one.")
            self._bmdViewPathExe = None
            raise ValueError("Cannot find image extractor executable. Please place it next to this file.")

        self._bmdViewPathExe = value

    def TryHiddenDOSCommand(self, exefile, args, startpath):
                
        # --print "###################"
        # --print cmd
        # --print startpath
        try:
            MaxH.HiddenDOSCommand(exefile, args, startpath=startpath)
        except MaxH.subprocess.CalledProcessError as err:
            log.error('subprocess error: %s. Expect missing/glitchy textures', err)

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
            active_uv = modelMesh.uv_textures[0]
        except Exception as err:
            pass  # it will be fixed later anyways

        with MaxH.active_object(modelObject):
            if not active_uv:
                bpy.ops.paint.add_simple_uvs()
                active_uv = modelMesh.uv_textures[0]

            modelMesh.update()

            if self.model.hasColors[0]:
                # if len(self.vtx.colors) and len(self.vtx.colors[0]):  # has colors?
                try:
                    alpha_image = MatH.add_vcolor(modelMesh, self.model, 0)
                except Exception as err:
                    log.error('Vertex color layer 0 failed (error is %s)', err)
                    raise
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
                        # create ALL bones before starting referencing them
                    for bone in self._bones:
                        realbone = arm.edit_bones[bone.name.fget()]
                        if isinstance(bone.parent.fget(), PBones.Pseudobone):
                            realbone.parent = arm.edit_bones[bone.parent.fget().name.fget()]
                        realbone.head.xyz = bone.position.xzy
                        realbone.tail.xyz = bone.endpoint.xzy
                        realbone.head.y *= -1
                        realbone.tail.y *= -1
                        realbone.align_roll(bone.get_z())  # get_z translates into blender coodrinates by itself
                        modelObject.vertex_groups.new(bone.name.fget())

                    if len(self.vertexMultiMatrixEntry) != len(self.model.vertices):
                        log.error("Faulty multimatrix skin interpolation")
                        raise ValueError("E")
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
                        vg = modelObject.vertex_groups.new(com)
                        vg.add(self.DEBUGvgroups[com], 1, 'REPLACE')

                    bpy.context.scene.update()
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
            modelMesh.show_edge_sharp = True
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

    def DismantleSingleMesh(self, modelObject):

        # ## first, create the PseudoBone armature
        if (modelObject.parent is not None) and isinstance(modelObject.parent.data, bpy.types.Armature):
            try:
                arm_obj = modelObject.parent
                arm = arm_obj.data

                with MaxH.active_object(arm_obj):
                    bpy.ops.object.mode_set(mode='EDIT')
                    bones = {}  # {realbone: Pbone}
                    self._bones = [None] * len(arm.edit_bones)
                    for i, realbone in enumerate(arm.edit_bones):
                        self._bones[i] = PBones.Pseudobone(None, realbone.name, None,
                                                   Vector((0,0,0)), Vector((0,1,0)))

                        bones[realbone] = (self._bones[i])  # indexing needed to create the multimatrices

                    rootbones = []  # we need to have a single root bone in the BMD file: it might need to be added
                    for realbone in arm.edit_bones:
                        bone = bones[realbone]
                        if realbone.parent.fget() is not None:
                            bone.parent.fset(bones[realbone.parent])
                        else:
                            rootbones.append(bone)
                        bone.position = realbone.head.copy()
                        bone.endpoint = realbone.tail.copy()
                        bone.matrix = PBones.BtoN * realbone.matrix * PBones.NtoB
                        # XCX is there a matter of scale in this BS as well? (I don't think so, but tests needed.)

                        bone.position.xyz = bone.position.xzy  # get the vectors in bmd space, not blender space
                        bone.position.z *= -1
                        bone.endpoint.xyz = bone.endpoint.xzy
                        bone.endpoint.z *= -1

                    # check if there is a single root:
                    if len(rootbones) > 1:
                        rootBone = PBones.Pseudobone(None, '__root__', None, Vector((0,0,0)), Vector((0,0,0)) )
                        self._bones.insert(0, rootBone)
                        for fakeroot in rootbones:
                            fakeroot.parent.fset(rootBone)
                            fakeroot.matrix = Matrix.Identity(4)
                    else:
                        rootBone = rootbones[0]

                    # new build (incomplete!) scenegraph and reorder bones
                    self._bones = []
                    rootSG = Inf1.SceneGraph()
                    rootSG.type = 0x10
                    self.BuildScenegraph(rootSG, rootBone)
                    # [self._bones has been rebuilt]
                    
                    bpy.ops.object.mode_set(mode='OBJECT')

                self.params.createBones = True

            except Exception as err:
                log.critical('Animation bones not created. cannot export further. Crashing...')
                raise

        # ## then create the easily-accessible representation

        self.model = ModelRepresentation()
        self.model.vertices = [Vector((vert.co.x, vert.co.z, -vert.co.y))
                                   for vert in modelObject.data.vertices]
        self.model.loops = []

        maxuv = min(len(modelObject.data.uv_layers), 8)
        maxvc = min(len(modelObject.data.vertex_colors), 2)

        for b_loop in modelObject.data.loops:
            p_loop = LoopRepresentation()
            self.model.loops.append(p_loop)
            p_loop.vertex = b_loop.vertex_index
            p_loop.normal = Vector(b_loop.normal.xzy)
            p_loop.normal.z *= -1
            for uv in range(maxuv):
                p_loop.UVs[uv] = modelObject.data.uv_layers[uv].data[b_loop.index].uv
                p_loop.UVs[uv].y = 1-p_loop.UVs[uv].y  # XCX: needs more consistency : wasn't it a tuple?
            for vc in range(maxvc):
                p_loop.VColors[vc] = modelObject.data.vertex_colors[vc].data[b_loop.index].color

        self.model.hasNormals = True
        for uv in range(maxuv):
            self.model.hasTexCoords[uv] = True
        for vc in range(maxvc):
            self.model.hasColors[vc] = True

        for poly in modelObject.data.polygons:
            face = FaceRepresentation()
            self.model.faces.append(face)
            face.material = poly.material_index
            face.loop_start = poly.loop_start

        # continue bone business after building model
        if self.params.createBones:
            self.vertexMultiMatrixEntry = []
            for i, vert in enumerate(modelObject.data.vertices):
                mm = Evp1.MultiMatrix()
                self.vertexMultiMatrixEntry.append(mm)

                for group in vert.groups:
                    # XCX is groups ordered? if so, optimize is_near.
                    if group.weight > 0.0001:
                        mm.indices.append(group.group)
                        mm.weights.append(group.weight)

            # mm disambiguation and reference making
            self.unique_MMs = []  
            vertexMMIndices = [-1] * len(self.vertexMultiMatrixEntry)
            
            for i in range(len(self.vertexMultiMatrixEntry)):
                for ri, reference in enumerate(self.unique_MMs):
                    if Mat44.is_near(self.vertexMultiMatrixEntry[i], reference):
                        self.vertexMultiMatrixEntry[i] = reference
                        vertexMMIndices[i] = ri
                        break
                else:  # no break detected : unique yet
                    vertexMMIndices[i] = len(self.unique_MMs)
                    self.unique_MMs.append(self.vertexMultiMatrixEntry[i])

            for mm in self.unique_MMs:
                if len(mm.indices) > 1:
                    self.model.hasMatrixIndices = True
            
            # reference making
            for loop in self.model.loops:
                loop.mm = vertexMMIndices[loop.vertex]
        
            self.AnalyseBones(rootSG, rootBone.matrix, rootBone)  # build the joints.
            batches = self.splitInBatches()
        else:
            raise ValueError("need to figure out what to do for armatureless meshes. extract data.")  # XCX
    
    def splitInBatches(self):
        singleboneBatches = {}  # {(bone number, material): batch}
        groupedBones = []  # list of sets of bones (ints)
        secondpassFaces = []
        model = self.model
        
        # first pass: split the single-boned faces per bone,
        # and create groups for the others
        for i in range(len(self.model.faces)):
            l1, l2, l3 = model.getLoops(i)
            mat = model.faces[i].material
            if l1.mm == l2.mm == l3.mm and \
                    len(self.unique_MMs[l1.mm].weights) == 1:
                boneIndex = self.unique_MMs[l1.mm].indices[0]
                if not singleboneBatches.get(boneIndex, None):
                    singleboneBatches[boneIndex, mat] = []
                singleboneBatches[boneIndex, mat].append(i)
            
            else:
                for group in groupedBones:
                    if (l1.mm, mat) in group:
                        group.add((l2.mm, mat))
                        group.add((l3.mm, mat))
                        break
                    elif (l2.mm, mat) in group:
                        group.add((l1.mm, mat))
                        group.add((l3.mm, mat))
                        break
                    elif (l3.mm, mat) in group:
                        group.add((l1.mm, mat))
                        group.add((l2.mm, mat))
                        break
                else:  # no break reached: need to create new group
                    group = set()
                    group.add((l1.mm, mat))
                    group.add((l2.mm, mat))
                    group.add((l3.mm, mat))
                    groupedBones.append(group)
        
        # pass 1.5: make sure the groups make sense (fuse them when needed)
        i=0  # indices pointing to the groups
        j=0
        while i < len(groupedBones)-1:  # -1 because we need a second group to compare to
            j = i+1  # second group
            while j<len(groupedBones):
                for x in groupedBones[j]:
                    if x in groupedBones[i]:
                        groupedBones[i] = groupedBones[i].union(groupedBones[j])
                        break
                else:  # no break: groups are really different
                    j += 1
            # last group reached for j: compare from a new iSize
            i += 1
        
        # groups are now solid per bone.
        # pass 2: assign the multi-bone faces, and split per material
        multiboneBatches = {group:None for group in groupedBones}
        for face in secondpassFaces:
            l1 = model.getLoop(face, 0)
            mat = model.faces[face].material
            for group in groupedBones:
                if (l1, mat) in group:
                    #if not multiboneBatches.get(group, None):
                    #    multiboneBatches[group] = []
                    
                    multiboneBatches[group].append(face)
        return singleboneBatches, multiboneBatches
      
    def insertSBBatches(self, sg, SBBatches):
    
        # function assumes that the SG node used for the call is a bone SG node
        # warning : `SBBatches` here is {bone: [(mat, batch),...]}, not {(bone, mat): batch},
        # `MBBatches` is ????
        # and `batch` is an int, not a list of faces
        # the batches need to be indexed beforehand
        assert sg.type == 0x10
        
        # pass 1 : add the single-boned batches, add (too much) material SG nodes,
        # and add flags onto the bone SG nodes to be able to clean those material batches
        for bone in SBBatches.keys():
            if bone == sg.index:
                # simple case one material for this bone's batch
                if len(SBBatches[bone]) == 1:
                    # use a material SG node to apply to all of its children
                    mat, batch = SBBatches[bone][0]
                    matsg = Inf1.SceneGraph()
                    matsg.type = 0x11
                    matsg.index = mat
                    matsg.children = sg.children
                    sg.children = [matsg]
                    # then add batch to children, and optimize remaining dict
                    batchSG = Inf1.SceneGraph()
                    batchSG.type = 0x12
                    batchSG.index = batch
                    matsg.children.append(batchSG)
                    sg.material = mat
                    
                # if there are multiple materials: there is the need for multiple
                # material SG nodes as children: do this smartly for a better cleanup
                else:
                    # this block's complexity is absurd but that's okay because
                    # a batch won't have more than 5 children
                    for child in sg.children:
                        self.insertSBBatches(child, SBBatches)
                    original_children = sg.children
                    sg.children = []
                    sg.material = []  # list of materials
                    for mat, batch in SBBatches:
                        sg.material.append(mat)
                        matsg = Inf1.SceneGraph()
                        matsg.index = mat
                        matsg.type = 0x11
                        batchSG = Inf1.SceneGraph()
                        batchSG.type = 0x12
                        batchSG.index = batch
                        matsg.children.append(batchSG)
                        
                        # add the correct children nodes
                        i = 0
                        while i<len(original_children):
                            child = original_children[i]
                            if child.material == mat:
                                matsg.children.append(child)
                                del original_children[i]
                            else:
                                i+=1
                        sg.children.append(matsg)
                    # but there might still be some of the bone children left
                    # XCX optimize for "multi-material bone nodes" too
                    sg.children += original_children
            # found the right bone in the SBBatches
            del SBBatches[bone]
            break
        # last case: this bone doesn't have a dedicated batch:
        # this is where the sg.material cache really shines.
        else:
            sg.material = sg.children[0].material
        
        # pass 2: clean the material nodes
        
        def remove_mat(sg, mat):
            # look into the sg node's children and erase any material node
            # from the tree, while keeping its children
            i = 0
            while i < len(sg.children):
                child = sg.children[i]
                if child.type == 0x11 and child.index==mat:
                    sg.children += child.children
                    del sg.children[i]
                    break
                    
        for child in sg.children:
            if child.type == 0x11:
                for grandchild in child.children:
                    remove_mat(grandchild, child)
        
    def LoadModel(self, filePath):
        """loads mesh data from file"""

        log.debug("Load : ")
        # -- load model
        br = BinaryReader.BinaryReader()
        br.Open(filePath)

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
        self._mat1O = M2O.Mat3()
        self.tex = Tex1.Tex1()
        self.mdl = Mdl3.Mdl3()

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
                self._mat1O.LoadData(br)
            elif strTag == "TEX1":
                self.tex.LoadData(br)
            elif strTag == "MDL3":
                self.mdl.LoadData(br)
            else:
                log.warning('Tag (%s) not recognized. Resulting mesh could be weird', strTag)
            br.SeekSet(streamPos)

        # self.tex.LoadData(br)  # why the heck would it be loaded twice?!
        br.Close()

    def DumpModel(self, filePath):
        """loads mesh data from file"""

        log.debug("Dumping model...")
        # -- load model
        bw = BinaryWriter.BinaryWriter()
        bw.Open(filePath)
        # self._bmdFilePath = filePath
        # self._bmdDir = MaxH.getFilenamePath(self._bmdFilePath)
        # self._bmdFileName = MaxH.getFilenameFile(self._bmdFilePath)
        # self._bmdDir += self._bmdFileName + "\\"
        # try:
        #    os.mkdir(self._bmdDir)
        # except FileExistsError:
        #    pass
        # self._texturePath = self._bmdDir + "Textures"

        # XCX what is the file header?

        bw.SeekSet(0x20)


        self.inf = Inf1.Inf1()
        self.vtx = Vtx1.Vtx1()
        self.shp = Shp1.Shp1()
        self.jnt = Jnt1.Jnt1()
        self.evp = Evp1.Evp1()
        self.drw = Drw1.Drw1()
        self._mat1 = Mat3.Mat3()
        self.tex = Tex1.Tex1()
        self.mdl = Mdl3.Mdl3()

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
            elif strTag == "TEX1":
                self.tex.LoadData(br)
            elif strTag == "MDL3":
                self.mdl.LoadData(br)
            br.SeekSet(streamPos)

        # self.tex.LoadData(br)
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
                    newPos = mat*(self.vtx.positions[posIndex])
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
                    raise ValueError("unknown primitive type")
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
            effP = parentMatrix * f.getFrameMatrix()
            f.matrix = effP

            fstartPoint = parentMatrix * f.t

            orientation = (Mat44.rotation_part(parentMatrix) *  # use rotation part of parent matrix
                          Euler((f.rx, f.ry, f.rz), 'XYZ').to_matrix().to_4x4() *  # apply local rotation
                          Vector((0, self.params.boneThickness, 0)))
            # computing correct bone orientation (first in BMD coords, then convert later)

            bone = PBones.Pseudobone(parentBone, f, effP,
                                     fstartPoint,
                                     fstartPoint + orientation)

            bone.scale = (f.sx, f.sy, f.sz)

            # mTransform = Euler((f.rx, f.ry, f.rz), 'XYZ').to_matrix().to_4x4() * parentMatrix
            # (this was wrong anyway)

            # bone.rotation_euler = mTransform.to_euler("XYZ")
            bone.width = bone.height = self.params.boneThickness

            # bone.inverted_static_mtx = effP.inverted()

        for com in sg.children:
            self.CreateBones(com, effP, bone)

        if parentBone is None:
            return bone

    def AnalyseBones(self, sg, parentMatrix, parentBone):
        """creates bone hierarchy (FrameNodes) and apply matrices(jnt1.frames used to compute jnt1.matrices)"""
        bone = parentBone
        n = sg

        if n.type == 0x10:
            # --joint
            if len(self.jnt.frames) < n.index:
                self.jnt.frames += [None] * (n.index - len(self.jnt.frames))
            f = self.jnt.frames[n.index] = Jnt1.JntFrame()

            f.matrix = bone.matrix

            localMtx = parentMatrix.inverted() * bone.matrix

            f.t, rot, sc = localMtx.decompose()

            f.rx, f.ry, f.rz = rot.xyz

            f.sx, f.sy, f.sz = sc.xyz

        for com in sg.children:
            self.AnalyseBones(com, bone.matrix, bone)

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
                    self._currMaterial = mat.material[0]
                    matIndex = mat.material[1]
                else:
                    if not self.params.use_nodes:
                        self._currMaterial = MatH.build_material(self, self._mat1, mat, self.tex)
                    else:
                        try:
                            self._currMaterial = MatH.build_material_v2(matIndex, self._mat1, self.tex,
                                                                        self._texturePath, '.' + self.params.imtype.lower())
                        except Exception as err:
                            log.error(
                                'node (GLSL) materials went wrong. Falling back to incomplete materials. (error is %s)',
                                err)
                            self._currMaterial = MatH.build_material(self, self._mat1, mat, self.tex)
                    mat.material = (self._currMaterial, matIndex)

            except Exception as err:
                log.error('Material not built correctly (error is %s)', err)
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
                if self.params.use_nodes:
                    self._currMaterial.name = self._mat1.stringtable[n.index]
                else:
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
            raise

        if self.params.createBones:
            self._bones = rootBone.tree_to_array()

            origWorldBonePos = self._bones[0].position  # fixed

            # -- easier than recalculating all bone transforms
            d = Vector()
            self._bones[0].parent.fset(d)  # fixed
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
            bckFiles += MaxH.getFiles(self._bmdDir + bckPath)
        for f in bckFiles:
            bckFileName = MaxH.getFilenameFile(f)
            b = Bck.Bck_in()
            try:
                b.LoadBck(f, len(self._bones))
            except Exception as err:
                log.warning('an animation file was corrupted. (error is %s)', err)
                continue

            if not len(b.anims):
                # file loader already knows that it won't fit
                errMsg += bckFileName + "\n"
            else:
                if self.params.animationType == 'SEPARATE':
                    try:
                        b.AnimateBoneFrames(0, self._bones, 1, self.params.includeScaling)
                        action = PBones.apply_animation(self._bones, self.arm_obj, self.jnt.frames, bckFileName)
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

        self._images = MaxH.getFiles(self._texturePath + "\\*" + imageExt)

        if len(self._images) == 0 or force:
            self.TryHiddenDOSCommand("BmdView",
                                     [self._bmdFilePath, self._texturePath, self.params.imtype],
                                     self._bmdViewPathExe)

        # TODO: need to update BmdView.exe to process all file formats like BmdView2
        errorMessage = "Error generating dds / tga image file(s).\
                       Use BmdView2 to export the missing tga file(s)\
                       then delete the *.ERROR file(s) and run the importer again"
        errorFiles = MaxH.getFiles(self._texturePath + "\\*.ERROR")
        for f in errorFiles:
            errorMessage += f + "\n"  # report file
            MaxH.newfile(f[:-6] + imageExt)  # and avoid crashes in the future
        if len(errorFiles) != 0:
            log.error(errorMessage)
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

    def Import(self, filename, use_nodes, imtype, packTextures, allowTextureMirror, loadAnimations, includeScaling,
               forceCreateBones, boneThickness, dvg, val_msh=False):
        self.params = Prog_params(filename, boneThickness, allowTextureMirror, forceCreateBones,
                                  loadAnimations != 'DONT', loadAnimations,
                                  packTextures,  includeScaling, imtype, dvg, use_nodes, val_msh)

        self._bckPaths.append("..\\..\\bck\\*.bck")
        self._bckPaths.append("..\\..\\bcks\\*.bck")
        self._bckPaths.append("..\\..\\scrn\\*.bck")

        TexH.MODE = self.params.packTextures
        TexH.textures_reset()  # avoid use of potentially deleted data

        #if filename = 'P:\ath\to\file.bmd',
        self._bmdFilePath = filename
        # this is 'P:\ath\to\file' and '.bmd' (the second string is useful because it can also be 'bdl'
        temp_path, temp_ext = OSPath.splitext(filename)
        # this is 'P:\ath\to\file_bmd\'
        self._bmdDir = temp_path+ '_' + temp_ext[1:] + "\\"  # generates dir name from file name?
        # P:\ath\to'
        self._bmdPath = OSPath.split(temp_path)[0]
        # file(.bmd?)
        self._bmdFileName = MaxH.getFilenameFile(filename)
        # P:\ath\to\file_bmd\Textures
        self._texturePath = self._bmdDir + "Textures"
        
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
            log.warning('couldn\'t export BTP animations into xml files. Model should beave normally nevertheless')

    def __del__(self):
        if self._bones:
            self._bones[0].pre_delete()  # fixes momory leak
        # object.__del__(self)
