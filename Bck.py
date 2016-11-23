#! /usr/bin/python3
from .BinaryReader import BinaryReader
from .maxheader import MessageBox
from .Vector3 import Vector3
from .pseudobones import getBoneByName, Pseudobone
import mathutils
import bpy
from math import nan, pi


class BckKey:
    # <variable time>
    # -- float 
    # <variable value>
    # -- float 
    # <variable tangent>
    # -- float  //??
    def __init__(self):  # GENERATED!
        self.time = 0
        self.value = 0
        self.tangent = 0


class BckJointAnim:
    # <variable scalesX>
    # -- std::vector<Key>
    # <variable scalesY>
    # -- std::vector<Key>
    # <variable scalesZ>
    # -- std::vector<Key>
    # <variable rotationsX>
    # -- std::vector<Key>
    # <variable rotationsY>
    # -- std::vector<Key>
    # <variable rotationsZ>
    # -- std::vector<Key>
    # <variable translationsX>
    # -- std::vector<Key>
    # <variable translationsY>
    # -- std::vector<Key>
    # <variable translationsZ>
    # -- std::vector<Key>
    def __init__(self):  # GENERATED!
        self.scalesX= []
        self.rotationsY= []
        self.rotationsZ= []
        self.scalesZ= []
        self.translationsZ= []
        self.translationsX= []
        self.rotationsX= []
        self.translationsY= []
        self.scalesY= []
    # ------------------------------------


class BckAnk1Header:
    """# <variable tag>
    # -- char[4] 'ANK1'
    # <variable sizeOfSection>
    # -- u32 
    # -- 0 - play once, 2 - loop
    # <variable loopFlags>
    # -- u8 
    # <variable angleMultiplier>
    # -- u8 all angles have to multiplied by pow(2, angleMultiplyer)
    # <variable animationLength>
    # -- u16 in time units
    # <variable numJoints>
    # -- u16 that many animated joints at offsetToJoints
    # <variable scaleCount>
    # --u16  that many floats at offsetToScales
    # <variable rotCount>
    # -- u16 that many s16s at offsetToRots
    # <variable transCount>
    # -- u16 that many floats at offsetToTrans
    # <variable offsetToJoints>
    # -- u32 
    # <variable offsetToScales>
    # -- u32 
    # <variable offsetToRots>
    # -- u32 
    # <variable offsetToTrans>
    # -- u32 
    # <function>"""

    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
                
      self.tag = br.ReadFixedLengthString(4)
      self.sizeOfSection = br.ReadDWORD()
      self.loopFlags = br.GetByte()
      self.angleMultiplier = br.GetByte()
      self.animationLength = br.ReadWORD()
      self.numJoints = br.ReadWORD()
      self.scaleCount = br.ReadWORD()
      self.rotCount = br.ReadWORD()
      self.transCount = br.ReadWORD()
      self.offsetToJoints = br.ReadDWORD()
      self.offsetToScales = br.ReadDWORD()
      self.offsetToRots = br.ReadDWORD()
      self.offsetToTrans = br.ReadDWORD()
    # -- TODO: the following two structs have really silly names, rename them


class BckAnimIndex:
    # <variable count>
    # -- u16 
    # <variable index>
    # -- u16 
    # <variable zero>
    # -- u16 always 0?? -> no (biawatermill01.bck) TODO: find out what it means
    # <function>

    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
                
     self.count = br.GetSHORT()        
     self.index = br.GetSHORT()
     self.zero = br.GetSHORT()
  

class BckAnimComponent:
    # <variable s>
    # -- AnimIndex scale
    # <variable r>
    # -- AnimIndex rotation
    # <variable t>
    # -- AnimIndex translation
    # <function>

    def __init__(self):  # GENERATED!
        self.s= BckAnimIndex()
        self.r= BckAnimIndex()
        self.t= BckAnimIndex()

    def LoadData(self, br):
     self.s.LoadData(br)
     self.r.LoadData(br)
     self.t.LoadData(br)
  

class BckAnimatedJoint:
    # --if count > 1, count*3 floats/shorts stored at index (time, value, unk [interpolation info, e.g. tangent??])?
    # --for shorts, time is a "real" short, no fixedpoint
    # <variable x>
    # -- AnimComponent 
    # <variable y>
    # -- AnimComponent 
    # <variable z>
    # -- AnimComponent 
    # <function>

    def __init__(self):  # GENERATED!
        self.z= BckAnimComponent()
        self.y= BckAnimComponent()
        self.x= BckAnimComponent()

    def LoadData(self, br):
     self.x.LoadData(br)
     self.y.LoadData(br)
     self.z.LoadData(br)


# -----------------------------------------------


class Bck:
    """# <variable anims>
    # -- std::vector<JointAnim>
    # <variable animationLength>
    # -- int
    # <variable currAnimTime>
    # -- float
    # -- ConvRotation(vector<Key>& rots, float scale)
    # <function>

    # -- void readComp(vector<Key>& dst, const vector<T>& src, const bck::AnimIndex& index)
    # <function>

    # <function>

    # <function>

    # <function>

    # <function>

    # -- the caller has to ensure that jnt1.frames and bck.anims contain
    # --the same number of elements
    # <function>

    # -- IMPORTANT: scale values are absolute and not related to the parent
    # -- e.g Bone A (scale=200%), Bone B (Scale=200%), Bone C (Scale=100%). Bone A is the parent of Bone B and Bone B is the parent of Bone C
    # --  need to remove the parent scaling. e.g Bone C shouldn't change in size but in 3DS max it will equal 400% (2 * 2 * 1 * 100)
    # <function>

    # -- CalcScale anims[i].scalesX parentBoneIndexs 8
    # <function>

    # -- only calc on first parent. ignore boneIndex
    # <function>

    # -- gets total x scale (excluding self)
    # -- bck file stores the absolute scale at that point and should ignore all parent bone scaling
    # -- e.g. bone a (200%) -> bone b (200%) -> bone C (200%).
    # -- bone a (1 * 2 * 100), bone b ((1 / 2 (bone a scale)) * 2 * 100 = 50 %), bone c (1/2 * 1/2 * 100 = 25%)
    # -- however, the parent bone is already scaled based on all items before it so only the parents scale is required. e.g. bone c (1/2 * 100 = 50) because bone b is already at 50%, total scale = 50%*50%=25%
    # -- WARNING: skewed bones?
    # <function>

    # <function>

    # <function>

    # <function>

    # <function>

    # -- could use timeOffset to load all animations one after another
    # -- parentBoneIndexs array of ints. e.g. parentBoneIndexs[2] = 1 (2nd bones parent is the first bone)
    # <function>

    # -- deltaTime in ticks
    # <function>

    # -- from stdplugs/stdscripts/CharacterPluginObject.ms
    # <function>

    # -- from stdplugs/stdscripts/CharacterPluginObject.ms
    # <function>

    # <function>"""

    def __init__(self):  # GENERATED!
        self.anims = []

    def ConvRotation(self, rots, scale):
        for j in range(len(rots)):  # XCX!
            rots[j].value *= scale
            rots[j].tangent *= scale
        return rots

    def ReadComp(self, src, index):
        dst = []
        # -- dst.resize(index.count);

        # -- violated by biawatermill01.bck

        if index.zero != 0:
            pass
            # -- throw "bck: zero field %d instead of zero" -- ignore for now?
            # --TODO: biawatermill01.bck doesn't work, so the "zero"
            # --value is obviously something important
        if index.count <= 0:
            print("Warning: readComp(): count is <= 0")
        elif index.count == 1:
            dst.append(None)
            dst[0] = BckKey()  # fixed 4 lines
            dst[0].time = 0
            dst[0].value = src[index.index]
            dst[0].tangent = 0
        else:
            for j in range(index.count):  # (int j = 0; j < index.count; ++j)
                while len(dst) <= j:
                    dst.append(None)
                dst[j] = BckKey()
                dst[j].time = src[(index.index + 3*j)]
                dst[j].value = src[(index.index + 3*j + 1)]
                dst[j].tangent = src[(index.index + 3*j + 2)]
        return dst

    def LoadAnk1(self, br):
        i = 0
        ank1Offset = br.Position()

        # -- read header
        h = BckAnk1Header()
        h.LoadData(br)
        self.currAnimTime = 0.0
        self.animationLength = h.animationLength

        # -- read scale floats:
        br.SeekSet(ank1Offset + h.offsetToScales)
        scales = [br.GetFloat() for _ in range(h.scaleCount)]

        # -- read rotation s16s:
        br.SeekSet(ank1Offset + h.offsetToRots)
        rotations = [br.GetSHORT() for _ in range(h.rotCount)]

        # -- read translation floats:
        br.SeekSet(ank1Offset + h.offsetToTrans)
        translations = [br.GetFloat() for _ in range(h.transCount)]

        # -- read joints
        rotScale = (pow(2., h.angleMultiplier) * pi / 32768.)  # result in RADIANS  per increment (in a short)
        br.SeekSet(ank1Offset + h.offsetToJoints)
        self.anims = []
        # -- bck.self.anims.resize(h.numJoints);

        for i in range(h.numJoints):
            joint = BckAnimatedJoint()
            joint.LoadData(br)
            while len(self.anims) <= i:
                self.anims.append(None)
            self.anims[i] = BckJointAnim()
            self.anims[i].scalesX = self.ReadComp(scales, joint.x.s)
            self.anims[i].scalesY = self.ReadComp(scales, joint.y.s)
            self.anims[i].scalesZ = self.ReadComp(scales, joint.z.s)

            self.anims[i].rotationsX = self.ReadComp(rotations, joint.x.r)
            self.anims[i].rotationsZ = self.ReadComp(rotations, joint.z.r)
            self.anims[i].rotationsY = self.ReadComp(rotations, joint.y.r)
            self.anims[i].rotationsX = self.ConvRotation(self.anims[i].rotationsX, rotScale)
            self.anims[i].rotationsY = self.ConvRotation(self.anims[i].rotationsY, rotScale)
            self.anims[i].rotationsZ = self.ConvRotation(self.anims[i].rotationsZ, rotScale)

            self.anims[i].translationsX = self.ReadComp(translations, joint.x.t)
            self.anims[i].translationsY = self.ReadComp(translations, joint.y.t)
            self.anims[i].translationsZ = self.ReadComp(translations, joint.z.t)

    def LoadBck(self, filePath):
        br = BinaryReader()
        br.Open(filePath)
        br.SeekSet(0x20)
        size = 0
        i = 0
        while i < 1:
            br.SeekCur(size)
            pos = br.Position()
            tag = br.ReadFixedLengthString(4)
            size = br.ReadDWORD()

            if size < 8:
                size = 8  # -- prevent endless loop on corrupt data

            br.SeekSet(pos)

            if tag == "ANK1":
                self.LoadAnk1(br)
            else:
                MessageBox("readBck(): Unsupported section " + tag)
                raise ValueError("readBck(): Unsupported section " + tag)
            br.SeekSet(pos)
            i += 1
        br.Close()

    # no use here
    def Interpolate(self, v1, d1, v2, d2, t): # -- t in [0,1]
        # linear imterpolation:
        # return v1+t*(v1-v1)

        # --cubic interpolation:
        # -- float values
        a = 2*(v1 - v2) + d1 + d2
        b = -3 * v1 + 3 * v2 - 2 * d1 - d2
        c = d1
        d = v1
        # --TODO: yoshi_walk.bck has strange-looking legs...not sure if
        # --the following line is to blame, though
        return ((a*t + b)*t + c) *t + d

    # no use neither
    def getAnimValue(self, keys, t):
        if keys.count == 0:
                return 0.0
        if keys.count == 1:
                return keys[0].value
        # --messageBox (keys as string)
        # -- throw "E"
        i = 0

        while keys[i].time < t:
            i += 1
        # XCX
        time = (t - keys[i].time) /(keys[i].time- keys[i].time)         # -- scale to [0, 1]
        #return mathutils.interpolate(keys[i- 1].value,keys[i- 1].tangent,keys[i].value,keys[i].tangent,time)
        return self.Interpolate(keys[i].value,keys[i].tangent,keys[i].value,keys[i].tangent,time)

    # still nope.
    def AnimateJnt(self, jnt, deltaTime):

        # -- update time
        self.currAnimTime += deltaTime  # --*16 -- convert from seconds to ticks (dunno if this is right this way...TODO)
        self.currAnimTime = self.currAnimTime % self.animationLength # -- loop?

        # -- update joints
        for i in range(len(jnt.frames)):
            jnt.frames[i].sx = self.getAnimValue(self.anims[i].scalesX, self.currAnimTime)
            jnt.frames[i].sy = self.getAnimValue(self.anims[i].scalesY, self.currAnimTime)
            jnt.frames[i].sz = self.getAnimValue(self.anims[i].scalesZ, self.currAnimTime)

            # --TODO: use quaternion interpolation for rotations?
            jnt.frames[i].rx = self.getAnimValue(self.anims[i].rotationsX, self.currAnimTime)
            jnt.frames[i].ry = self.getAnimValue(self.anims[i].rotationsY, self.currAnimTime)
            jnt.frames[i].rz = self.getAnimValue(self.anims[i].rotationsZ, self.currAnimTime)

            jnt.frames[i].t.x = self.getAnimValue(self.anims[i].translationsX, self.currAnimTime)
            jnt.frames[i].t.y = self.getAnimValue(self.anims[i].translationsY, self.currAnimTime)
            jnt.frames[i].t.z = self.getAnimValue(self.anims[i].translationsZ, self.currAnimTime)

    # TODO: erase dummy bone system
    def GetPositionBone(self, curBone):
        # XCX
        dummyBone = getBoneByName(curBone.name.fget() + "_dummy")

        if dummyBone is None:
            return curBone

        else:
            return dummyBone

    # function which only has docs in it. Whut?!
    def ValidateScale(self, curBone, scaleValue):

        """# --if (scaleValue != 1 and curBone.children.count > 1) then
        # --	throw (curBone.name + " unable to scale ( " +(scaleValue as string)+" ) bones with more than one child bone")"""

    # GOT it!
    def AnimateBoneFrames(self, timeOffset, bones, frameScale, rootBoneOffset, exportType, refBoneRequiresDummyList, includeScaling):
        if exportType == 'CHARACTER' and self.animationLength > 0:
            timeOffset = 0  # XCX difference ONE

        # --alert (bones.count as string)
        rootBoneOffset = [0, 0, 0]

        for i in range(len(bones)):
            bone = bones[i]
            anim = self.anims[i]

            # -- animated bones require scaling helper
            if (len(anim.scalesX) > 1 or len(anim.scalesY) > 1 or len(anim.scalesZ) > 1):
                refBoneRequiresDummyList[i] = True  # -- bone.name

            if (len(anim.translationsX) > 1 or len(anim.translationsY) > 1 or len(anim.translationsZ) > 1):
                pass  #bone.boneEnable = False  # -- allow moving bone without affecting parent bone # XCX

                # --messageBox (anim.scalesX as string) -- only one value if position not animated. value = 0
                # --messageBox (anim.translationsY as string) -- only one value if scale not animated. value = 1

            # XCX: what if a bone has initial scale?
            # position correction LATER in the program
            for j in range(len(anim.rotationsX)):
                rot = anim.rotationsX[j]
                # at time ((rot.time * frameScale) + timeOffset)
                if int(rot.time * frameScale + timeOffset) not in bone.rotation_kf.keys():
                    bone.rotation_kf[int(rot.time * frameScale + timeOffset)] = mathutils.Euler((nan,nan,nan), 'XYZ')
                bone.rotation_kf[int(rot.time * frameScale + timeOffset)].x = rot.value

            for j in range(len(anim.rotationsY)):
                rot = anim.rotationsY[j]
                # at time ((rot.time * frameScale) + timeOffset)
                if int(rot.time * frameScale + timeOffset) not in bone.rotation_kf.keys():
                    bone.rotation_kf[int(rot.time * frameScale + timeOffset)] = mathutils.Euler((nan,nan,nan), 'XYZ')
                bone.rotation_kf[int(rot.time * frameScale + timeOffset)].y = rot.value

            for j in range(len(anim.rotationsZ)):
                rot = anim.rotationsZ[j]
                # at time ((rot.time * frameScale) + timeOffset)
                if int(rot.time * frameScale + timeOffset) not in bone.rotation_kf.keys():
                    bone.rotation_kf[int(rot.time * frameScale + timeOffset)] = mathutils.Euler((nan,nan,nan), 'XYZ')
                bone.rotation_kf[int(rot.time * frameScale + timeOffset)].z = rot.value

            for j in range(len(anim.translationsX)):
                t = anim.translationsX[j]
                # at time ((t.time * frameScale) + timeOffset)
                if int(t.time * frameScale + timeOffset) not in self.GetPositionBone(bone).position_kf.keys():
                    self.GetPositionBone(bone).position_kf[int(t.time * frameScale + timeOffset)] = mathutils.Vector((nan,nan,nan))
                self.GetPositionBone(bone).position_kf[int(t.time * frameScale + timeOffset)].x\
                    = t.value - rootBoneOffset[0]

            for j in range(len(anim.translationsY)):
                t = anim.translationsY[j]
                # at time ((t.time * frameScale) + timeOffset)
                if int(t.time * frameScale + timeOffset) not in self.GetPositionBone(bone).position_kf.keys():
                    self.GetPositionBone(bone).position_kf[int(t.time * frameScale + timeOffset)] = mathutils.Vector((nan,nan,nan))
                self.GetPositionBone(bone).position_kf[int(t.time * frameScale + timeOffset)].y\
                    = t.value - rootBoneOffset[1]

            for j in range(len(anim.translationsZ)):
                t = anim.translationsZ[j]
                # at time ((t.time * frameScale) + timeOffset)
                if int(t.time * frameScale + timeOffset) not in self.GetPositionBone(bone).position_kf.keys():
                    self.GetPositionBone(bone).position_kf[int(t.time * frameScale + timeOffset)] = mathutils.Vector((nan,nan,nan))
                self.GetPositionBone(bone).position_kf[int(t.time * frameScale + timeOffset)].z\
                    = t.value - rootBoneOffset[2]

            if includeScaling:
                for j in range(len(anim.scalesX)):
                    s = anim.scalesX[j]
                    # at time ((s.time * frameScale) + timeOffset)
                    self.ValidateScale(bone, s.value)
                    # in coordsys local
                    if int(s.time * frameScale + timeOffset) not in bone.scale_kf.keys():
                        bone.scale_kf[int(s.time * frameScale + timeOffset)] = mathutils.Vector((nan,nan,nan))
                    bone.scale_kf[int(s.time * frameScale + timeOffset)].x = s.value  # * 100 3dsmax has a percent scale
                    #)

                for j in range(len(anim.scalesY)):
                    s = anim.scalesY[j]
                    #at time ((s.time * frameScale) + timeOffset)
                    self.ValidateScale(bone, s.value)
                    #in coordsys local
                    if int(s.time * frameScale + timeOffset) not in bone.scale_kf.keys():
                        bone.scale_kf[int(s.time * frameScale + timeOffset)] = mathutils.Vector((nan,nan,nan))
                    bone.scale_kf[int(s.time * frameScale + timeOffset)].y = s.value  # * 100
                for j in range(len(anim.scalesZ)):
                    s = anim.scalesZ[j]
                    #at time ((s.time * frameScale) + timeOffset)
                    #in coordsys local
                    #(
                    self.ValidateScale(bone, s.value)
                    #in coordsys local
                    if int(s.time * frameScale + timeOffset) not in bone.scale_kf.keys():
                        bone.scale_kf[int(s.time * frameScale + timeOffset)] = mathutils.Vector((nan,nan,nan))
                    bone.scale_kf[int(s.time * frameScale + timeOffset)].z = s.value  # * 100
                    #))
            self.rootBoneOffset = [0, 0, 0]  # -- only the root bone has an offset. bones[1]
        # for i = 1 to bones.count do

        # -- IMPORTANT: set all transforms for the first and last frame. prevents errors when frames loaded on after another animation
        for i in range(len(bones)):
            bone = bones[i]
            anim = self.anims[i]
            if timeOffset + 1 not in bone.rotation_kf.keys():
                        bone.rotation_kf[timeOffset + 1] = mathutils.Euler((nan, nan, nan), 'XYZ')
            bone.rotation_kf[timeOffset + 1].x = (anim.rotationsX[0]).value  # --
            bone.rotation_kf[timeOffset + 1].y = (anim.rotationsY[0]).value  # --+ delta
            bone.rotation_kf[timeOffset + 1].z = (anim.rotationsZ[0]).value  # --+delta
            posBone = self.GetPositionBone(bone)
            if timeOffset + 1 not in posBone.position_kf.keys():
                posBone.position_kf[timeOffset + 1] = mathutils.Vector((nan, nan, nan))
            posBone.position_kf[timeOffset + 1].x = (anim.translationsX[0]).value
            posBone.position_kf[timeOffset + 1].y = (anim.translationsY[0]).value
            posBone.position_kf[timeOffset + 1].z = (anim.translationsZ[0]).value
    
            if (includeScaling):
                if timeOffset + 1 not in posBone.scale_kf.keys():
                    bone.scale_kf[timeOffset + 1] = mathutils.Vector((nan, nan, nan))
                bone.scale_kf[timeOffset + 1].x = ((anim.scalesX[0]).value)
                bone.scale_kf[timeOffset + 1].y = ((anim.scalesY[0]).value)
                bone.scale_kf[timeOffset + 1].z = ((anim.scalesZ[0]).value)
        if self.animationLength > 0:
            endFrame = timeOffset + self.animationLength

            for i in range(len(bones)):
                bone = bones[i]
                anim = self.anims[i]

                #addNewKey bone.rotation.controller endFrame
                #addNewKey bone.position.controller endFrame
                #addNewKey bone.scale.controller endFrame
                # -- only seems to create a new keyframe if the value changes (+ 0.0000000000000001)
                delta = 0.0000001
                # at time (endFrame) (
                if endFrame not in bone.rotation_kf.keys():
                    bone.rotation_kf[endFrame] = mathutils.Euler((nan, nan, nan), 'XYZ')
                bone.rotation_kf[endFrame].x = (anim.rotationsX[-1]).value  # --
                bone.rotation_kf[endFrame].y = (anim.rotationsY[-1]).value  # --+ delta
                bone.rotation_kf[endFrame].z = (anim.rotationsZ[-1]).value  # --+delta
                posBone = self.GetPositionBone(bone)
                if endFrame not in posBone.position_kf.keys():
                    posBone.position_kf[endFrame] = mathutils.Vector((nan, nan, nan))
                posBone.position_kf[endFrame].x = (anim.translationsX[-1]).value
                posBone.position_kf[endFrame].y = (anim.translationsY[-1]).value
                posBone.position_kf[endFrame].z = (anim.translationsZ[-1]).value

                if (includeScaling):
                    if endFrame not in posBone.scale_kf.keys():
                        bone.scale_kf[endFrame] = mathutils.Vector((nan, nan, nan))
                    bone.scale_kf[endFrame].x = ((anim.scalesX[-1]).value)
                    bone.scale_kf[endFrame].y = ((anim.scalesY[-1]).value)
                    bone.scale_kf[endFrame].z = ((anim.scalesZ[-1]).value)
                    # )

                # )
            # for i = 1 to bones.count do
            # -- if (self.animationLength > 0) then*/
        if exportType == 'CHARACTER' and self.animationLength > 0:
            bpy.context.scene.frame_start = 0
            if self.animationLength > 0:
                bpy.context.scene.frame_end = self.animationLength * frameScale
                #animationRange = interval (0, (self.animationLength * frameScale))
            else:  #animationRange = interval (0, 1)
                bpy.context.scene.frame_end = 1
                # -- animate on XCX turn keyframe mode off


"""

    def GetParentBoneScale(self, currBone, frameTime):

        parentScale = Vector3()
        parentScale.setXYZ(1, 1, 1)
        # at(time(frameTime))

        parentBone = currBone.parent
        while parentBone is not None:

            parentScale.x *= (parentBone.scale.controller.x_scale / 100)
            parentScale.y *= (parentBone.scale.controller.y_scale / 100)
            parentScale.z *= (parentBone.scale.controller.z_scale / 100)

            parentBone = parentBone.parent
        # --return 1
        return parentScale

    def _CalcParentScale(self, boneIndex, keys, parentBoneIndexs, frame):

    # -- if (keys.count == 0) then
    # --    return 1.0 -- identity

        if boneIndex <= 0  :
            return 1 # -- identity

        val = self.getAnimValue(keys, frame) # -- absolute value

        if val < 0.1  :
                raise ValueError ("E")

        if val > 10 :
                raise ValueError ("Max")
        val = 1 / val

        if parentBoneIndexs[boneIndex] > 0 :
            return self._CalcParentScale(parentBoneIndexs[boneIndex], keys, parentBoneIndexs, frame) * val

        else:
            return val

    def CalcParentScale(self, boneIndex, keys, parentBoneIndexs, frame):
        return 1  #  XCX ?????????
        # -- if (boneIndex <= 0 ) then
        # --	return 1 -- identity

        val = self.GetAnimValue(keys, frame)  # -- absolute value

        if val < 0.0000001:
                raise ValueError("E")

        if val > 100000 :
                raise ValueError ("Max")
        val = 1 / val
        return val

        # --return _CalcParentScale parentBoneIndexs[boneIndex] keys parentBoneIndexs frame

    def CalcParentXScale(self, anims, parentBoneIndex, parentBoneIndexs, frame):

        # --	return 1

        if parentBoneIndexs[parentBoneIndex] <= 0  :# -- root bone
            return 1 # -- identity
        # --return  (getAnimValue self.anims[parentBoneIndex].scalesX frame)
        val = 1 / self.getAnimValue(self.anims[parentBoneIndex].scalesX, frame)         # -- absolute value
        return val
        # --return (CalcParentXScale self.anims parentBoneIndexs[parentBoneIndex] parentBoneIndexs frame) * val

    def CalcParentYScale(self, anims, parentBoneIndex, parentBoneIndexs, frame):

        # --return 1

        if parentBoneIndexs[parentBoneIndex] <= 0:  # -- root bone
            return 1  # -- identity
        # --return  (getAnimValue self.anims[parentBoneIndex].scalesY frame)
        val = 1 / self.getAnimValue(self.anims[parentBoneIndex].scalesY, frame)         # -- absolute value
        return val
        # --return (CalcParentYScale self.anims parentBoneIndexs[parentBoneIndex] parentBoneIndexs frame) * val

    def CalcParentZScale(self, anims, parentBoneIndex, parentBoneIndexs, frame):
        # --return 1
        if parentBoneIndexs[parentBoneIndex] <= 0  :  # -- root bone
            return 1 # -- identity
        # --return  (getAnimValue self.anims[parentBoneIndex].scalesZ frame)
        val = 1 / self.getAnimValue(self.anims[parentBoneIndex].scalesZ, frame)         # -- absolute value
        return val
        # --return (CalcParentZScale self.anims parentBoneIndexs[parentBoneIndex] parentBoneIndexs frame) * val

    def AnimateBones(self, bones, deltaTime):
                
        # -- update time
        self.currAnimTime += deltaTime  # -- *16 -- convert from seconds to ticks (dunno if this is right this way...TODO)
        self.currAnimTime = self.currAnimTime % self.animationLength  # -- loop?

        # -- update joints

        for i in range(len(bones)):
            bone = bones[i]

            # --TODO: use quaternion interpolation for rotations?
            rx = self.getAnimValue(self.anims[i].rotationsX, 0) #currAnimTime)
            ry = self.getAnimValue(self.anims[i].rotationsY, 0) #currAnimTime)
            rz = self.getAnimValue(self.anims[i].rotationsZ, 0) #currAnimTime)
            bone.rotation.controller.x_rotation = rx
            bone.rotation.controller.y_rotation = ry
            bone.rotation.controller.z_rotation = rz

            tx = self.getAnimValue(self.anims[i].translationsX, 0)#currAnimTime)
            ty = self.getAnimValue(self.anims[i].translationsY, 0)#currAnimTime)
            tz = self.getAnimValue(self.anims[i].translationsZ, 0)#currAnimTime)
            bone.position.controller.x_position = tx
            bone.position.controller.y_position = ty
            bone.position.controller.z_position = tz

            sx = self.getAnimValue(self.anims[i].scalesX, 0)# currAnimTime
            sy = self.getAnimValue(self.anims[i].scalesY, 0)# currAnimTime
            sz = self.getAnimValue(self.anims[i].scalesZ, 0)# currAnimTime
            bone.scale.controller.x_scale = sx * 100
            bone.scale.controller.y_scale = sy * 100
            bone.scale.controller.z_scale = sz * 100

    def resetAnim(self, fromAnim):
                

        if fromAnim.controller is not None :
            pass
            # deleteKeys fromAnim.controller allKeys

        # -- delete self.anims from custom attributes

        for k in range(len(custAttributes(fromAnim))) :
            ca = custattributes.get(fromAnim, k)
            if ca is not None:
                saNames = getSubAnimNames(ca)
                for s in range(len(saNames.count)):
                    if ca[s].controller is not None:
                        pass  # XCXs everywhere!
                        #deleteKeys(ca[s].controller, allKeys)

        for j in range(1 , fromAnim.numSubs+ 1):
            self.resetAnim(fromAnim[j])

    def resetNodeAnim(self, node):
                
        self.resetAnim(node.controller)
        self.resetAnim(node.baseObject)
        for m in node.modifiers:
            self.resetAnim(m)

    def DeleteAllKeys(self, bones):

        if self.animationLength > 0:
            # -- move all the keys back by one frame (extra frame was required to prevent export / import bug)
            for i in range(len(bones)):
                b = bones[i]
                #selectKeys(b.rotation.controller,  interval(1, (animationLength+5)))
                #moveKeys(b.rotation.controller (-animationLength+1), selection)
                #deleteKeys(b.rotation.controller, selection)

                #selectKeys(b.position.controller, interval(1, animationLength+5))
                #moveKeys(b.position.controller, -animationLength+1, selection)
                #deleteKeys(b.position.controller, selection)

                #selectKeys(b.scale.controller, interval(1, animationLength+5))
                #moveKeys(b.scale.controller, -animationLength+1, selection)
                #deleteKeys(b.scale.controller, selection)

                # --moveKeys  b -animationLength"""



        


