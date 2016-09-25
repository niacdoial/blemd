#! /usr/bin/python3
import mathutils
import bpy
from .pseudobones import vect_normalize, Pseudobone, getBoneByName
from .Matrix44 import *
from .maxheader import MessageBox


class FrameNode:
    """# <variable name>
    # <variable startPoint>
    # -- end point = first child
    # <variable children>
    # -- FrameNode
    # <variable parentFrameNode>
    # <variable effP>
    # <variable f>
    # <variable _bone>
    # <variable _eulerController>
    # -- used for animations
    # <variable _dummyHelper>
    # --_dummyHelperRequired = false,
    # <function>

    # -- required for character assembly
    # <function>

    # <function>

    # -- parent scale has no effect on child bone (prevents skewing)
    # -- can move child bone without auto scaling parent bone (face animation)
    # -- should only scale when the parent bone only has one child?
    # <function>

    # -- private
    # <function>

    # -- used for testing
    # <function>

    # -- private
    # <function>

    # -- private: NYI
    # <function>

    # <function>

    # <function>

    # <function>

    # <function>

    # -- returns new bones array
    # <function>

    # <function>

    # -- used on hold, fetch. Bone references lost.
    # <function>

    # <function>"""

    def __init__(self):  # GENERATED!
        self.children = []
        self.startPoint = mathutils.Vector((0,0,0))
        self.name = ''
        self.f = None
        self._bone = None
        self.parentFrameNode = None
        self._dummyHelper = None

    def RemoveDummyHelper(self):
        if (self._bone is not None) and (self._dummyHelper is not None) :                        
            self._bone.parent.fset(self._dummyHelper.parent.fget())
            self._dummyHelper = None

    def _GetAllNodes(self, nodes):
        if self._bone is not None:
            nodes.append(self._bone) 
            
            if self._dummyHelper is not None :
                nodes.append(self._dummyHelper) # -- required
        for child in self.children:
           child._GetAllNodes(nodes)

    def GetAllNodes(self):
                
        retNodes = []        
        self._GetAllNodes(retNodes)        
        return retNodes

    def FixBones(self, boneThickness):
        """
                    #
            #		local parent = self_bone
            #		
            #		if (parent is not None) then
            #		(
            #			local x = XForm()
            #			addModifier parent x 
            #			x.gizmo.scale = [1, 1, 1] -- Gizmo
            #			parent.boneScaleType = None -- don't squash bones
            #		)
            #		for childFrame in self.children do
            #		(
            #			local child = childFrame.self_bone
            #			-- IMPORTANT: only use local scale on XForm object
            #			-- Works with IK
            #			-- NOTE: only updates position on x scale. e.g. body / arms: arms don't move outward when chest scaled on y axis
            #			if (parent is not None) then
            #			(
            #				local d = distance child.pos  parent.pos
            #				paramWire.connect parent.modifiers[XForm].Gizmo.controller[Scale] child.pos.controller[X_Position] ((d as string) + " * (Scale.x)")
            #			)
            #			childFrame.FixBones boneThickness
            #		)        
    
        # --local parentBone = self_bone"""
        
        for child in self.children:
            if self._bone is not None:
                childBone = child._bone

                d = Pseudobone(mathutils.Vector((0,0,0)),
                               mathutils.Vector((1,0,0)),
                               mathutils.Vector((0,0,1)))
                d.name.fset(childBone.name.fget() + "_dummy")

                
                d.rotation_euler = self._bone.rotation_euler # -- not rotation
                d.scale = self._bone.scale
                d.position = childBone.position  # -- end points should match parent direction? Watch out for multi child bones e.g. back -> 2 shoulders (back shouldn't scale)
                d.endpoint = childBone.position + mathutils.Vector((0,0,boneThickness))
                d.recalculate_transform()
                
                # -- in coordsys world (d.position.x = child.position.x) -- only move along x axis?
                d.parent.fset(self._bone)
                childBone.parent.fset(d)
                # --in coordsys parent (child.position = [0,0,0] ) -- using dummy position instead
                # self.paramWire.connect(self._bone.transform.controller[self.Scale], d.transform.controller[self.Scale], "1/Scale")
                # freeze(d)# -- don't hide or .x export won't work
                # --hide d
                child._dummyHelper = d
            # --)
            child.FixBones(boneThickness)

    def _PrintTree(self, depth):
        if self.name is not None:
            print(depth + self.name)

        for child in self.children:
            child._printTree(depth + '--')

    def PrintTree(self):
        self._PrintTree("")

    def _CreateBones(self, parentBone, boneThickness, createdBonesTable, postfixName, parentTransform):
        bone = None

        if self.parentFrameNode is not None:
               
            if len(self.children) > 0:
                self.endPoint = self.children[0].startPoint  # fixed

            else:
                # -- create an end point bone (same direction as parent bone with a length of boneThickness)
                start = self.startPoint
                
                if parentBone is not None :  #-- THIS FIXES IMPORT OF MODELS WITH ONE BONE
                    dir = vect_normalize(parentBone.position - mathutils.Vector(start))
                else:
                    dir = [0, 0, 0]
                dir *= (-1 * boneThickness)
                dir += mathutils.Vector(self.startPoint)
                self.endPoint = [dir.x, dir.y, dir.z]
                # --endPoint = [dir.x, -dir.z, dir.y] -- using orig cords

            if parentBone is None:
                self.endPoint = [self.startPoint[0], self.startPoint[1] + boneThickness, self.startPoint[2]]
            # --self.startPoint = [0,0,0]
            # --endPoint = [10, 0, 0]
            
            bone = Pseudobone(mathutils.Vector(self.startPoint), mathutils.Vector(self.endPoint),
                              mathutils.Vector((0,0,1)).rotate(parentTransform.to_euler()))
            # --	self.freeze bone -- don't hide or .x export won't work
            self._bone = bone
            
            # --self_bone.boneFreezeLength=self.false -- prevent scale errors on animations. e.g. talking animations scale head?
            # --self_bone.boneAutoAlign=self.false

            mt = mathutils.Matrix.Translation(mathutils.Vector((self.f.t.x, self.f.t.y, self.f.t.z)))
            mx = mathutils.Matrix.Rotation(self.f.rx, 4, 'X')
            my = mathutils.Matrix.Rotation(self.f.ry, 4, 'Y')
            mz = mathutils.Matrix.Rotation(self.f.rz, 4, 'Z')

            if parentBone is not None:
                mTransform = (mx * my * mz * mt) * parentTransform
                
                bone.transform = mTransform
                bone.update_r_t()
                bone.parent.fset(parentBone)
                bone.name.fset(self.name + postfixName)

            else:
                mTransform = (mx * my * mz * mt)
                bone.transform = mTransform
                bone.update_r_t()
                bone.name.fset('root' + postfixName)


            bone.width = boneThickness
            bone.height = boneThickness
            createdBonesTable.append(bone)
        else:
            mTransform = parentTransform
            self.name = 'root'
        for child in self.children:
            child._CreateBones(bone, boneThickness, createdBonesTable, postfixName,  mTransform)

    def _FixBoneLength(self):

        for childBone in self.children:
            if (self._bone is not None) and (self._bone.parent.fget() is not None):
                mt = mathutils.Matrix.Translation(mathutils.Vector((self.f.t.x, self.f.t.y, self.f.t.z)))
                mx = mathutils.Matrix.Rotation(self.f.rx, 4, 'X')
                my = mathutils.Matrix.Rotation(self.f.ry, 4, 'Y')
                mz = mathutils.Matrix.Rotation(self.f.rz, 4, 'Z')
                
                parentVec = vect_normalize((self._bone.position)*self._bone.transform.inverted() -
                                           (self._bone.parent.fget().position)*self._bone.parent.fget().transform.inverted())
            
                mTransform = (mx * my * mz * mt)
                
                boneVec2 = vect_normalize((vect_normalize(self._bone.dir)) * mTransform)
                
                print(str(parentVec) + ":" + str(boneVec2))

            childBone._FixBoneLength()

    def _ToArray(self, items):

        for child in self.children:
           items.append(child)
           child._ToArray(items)

    def ToArray(self):
        items = []
        self._ToArray(items)
        return items

    def _CreateParentBoneIndexs(self, items, itemIndex, parentIndex, depth):

        items.append(parentIndex)
        
        parentIndex = itemIndex[0]  # fixed
        # --if (name is not None) then -- self.first item is None
        # --	print (depth + name + ":" + (parentIndex as string) + ":" + (itemIndex[1] as string))
        
        itemIndex[0] = itemIndex[0] + 1  # fixed *2
        
        for child in self.children:
            child._CreateParentBoneIndexs(items, itemIndex, parentIndex, depth + "--")

    def CreateParentBoneIndexs(self):
                
        items = []
        itemIndex = [0]
        # -- only contains one value. Pass by reself.ference?
        self._CreateParentBoneIndexs(items, itemIndex, 0, "--")
        
        del items[0]  # -- self.first item not used  # fixed
        return items

    def CreateBones(self, boneThickness, postfixName):
                
        # with animate off
        #(
        if postfixName == None :
            postfixName = ""
        createdBonesTable = []

        mTransform = mathutils.Matrix.Identity(4)

        self._CreateBones(None, boneThickness, createdBonesTable, postfixName, mTransform)
        #)
        return createdBonesTable

    def _RemapBones(self, boneSet):
                
        self._bone = getBoneByName(self.name)
        
        if self._bone is not None:
            self._dummyHelper = getBoneByName(self._bone.name +"_dummy")
        
        boneSet.append(self._bone)
        
        for child in self.children  :
           child._RemapBones(boneSet)

    def RemapBones(self):
        boneSet = []
        for child in self.children:
            child._RemapBones(boneSet)
        return boneSet

    def ResetControllers(self):
        if self._bone is not None:
            if self._bone.parent.fget() is not None:
                m = mathutils.Euler((), 'XYZ')
                #					m.x_rotation = self.f.rx
                #					m.y_rotation = self.f.ry
                #					m.z_rotation = self.f.rz
                #
                self._bone.scale = mathutils.Vector((0,0,0))                 # -- resets animations

                self._eulerController = m
                self._bone.rotation = m

                pos = mathutils.Vector((0,0,0))
                                    #pos.x_position = self.f.t.x
                #					pos.y_position = self.f.t.y
                #					pos.z_position = self.f.t.z

                self._bone.position.controller = pos
        for child in self.children:
            child.ResetControllers()