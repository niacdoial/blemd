# -*- coding: utf-8 -*-
class BModel_out:
    """a implementation-in-progress alternative to BModel, for bmd export instead of import"""
    def DismantleSingleMesh(self, modelObject):

        # ## first, create the PseudoBone armature
        if (modelObject.parent is not None) and isinstance(modelObject.parent.data, bpy.types.Armature):
            try:
                arm_obj = modelObject.parent
                arm = arm_obj.data

                with common.active_object(arm_obj):
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
                    
    def DumpModel(self, filePath):
        """loads mesh data from file"""

        log.debug("Dumping model...")
        # -- load model
        bw = BinaryWriter.BinaryWriter()
        bw.Open(filePath)
        # self._bmdFilePath = filePath
        # self._bmdDir = common.getFilenamePath(self._bmdFilePath)
        # self._bmdFileName = common.getFilenameFile(self._bmdFilePath)
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