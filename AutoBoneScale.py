#! /usr/bin/python3
# -- parent scale has no effect on child bone (prevents skewing)
# -- can move child bone without auto scaling parent bone (face animation)
# -- should only scale when the parent bone only has one child?
import bpy

def FixBones(parentBone):
    for child in parentBone.children:
        if parentBone.children.count == 1 :                        
            d = bpy.data.objects.new(child.name +"_dummy", None)
            d.transform = parentBone.transform # -- not rotation
            d.position = child.position # -- end points should match parent direction? Watch out for multi child bones e.g. back -> 2 shoulders (back shouldn't scale)
            # -- in coordsys world (d.position.x = child.position.x) -- only move along x axis?
            d.parent = parentBone
            child.parent = d
            paramWire.connect(parentBone.transform.controller[Scale], d.transform.controller[Scale], "1/Scale")

        # --freeze d
        # --hide d
        FixBones(child)

    """# --FixBones Bone01
#
#print $Dummy01.transform
#
#$Dummy01.transform = $Bone01.transform -- not rotation
#--$Dummy01.rotation = $Bone01.rotation
#$Dummy01.position = $Bone02.position
#$Dummy01.parent = $Bone01
#$Bone02.parent = $Dummy01
#paramWire.connect $Bone01.transform.controller[#Scale] $Dummy01.transform.controller[#Scale] "1/Scale"
#"""