#! /usr/bin/python3
from .BinaryReader import BinaryReader
from .BinaryWriter import BinaryWriter
from .maxheader import MessageBox
from .pseudobones import getBoneByName, Pseudobone, cubic_interpolator
import mathutils
import bpy
import logging
log = logging.getLogger('bpy.ops.import_mesh.bmd.bck')
from math import nan, pi, isnan, ceil, isclose, floor


class BckKey:
    # <variable time>
    # -- float 
    # <variable value>
    # -- float 
    # <variable tangent>
    # -- float  //??
    def __init__(self, tm=0, vl=0.0, tg=0.0):  # GENERATED!
        self.time = tm
        self.value = vl
        self.tangent = tg

    def __eq__(self, other):
        return (self.time == other.time and
                isclose(self.value, other.value, rel_tol=1E-3) and
                isclose(self.tangent, other.tangent, rel_tol=1E-3))


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
        self.scalesX = []
        self.rotationsY = []
        self.rotationsZ = []
        self.scalesZ = []
        self.translationsZ = []
        self.translationsX = []
        self.rotationsX = []
        self.translationsY = []
        self.scalesY = []
        self.frames_scale = set()
        self.frames_rotation = set()
        self.frames_translation = set()
    # ------------------------------------

    def __eq__(self, other):
        return (self.scalesX == other.scalesX and
                self.scalesY == other.scalesY and
                self.scalesZ == other.scalesZ and
                self.rotationsX == other.rotationsX and
                self.rotationsY == other.rotationsY and
                self.rotationsZ == other.rotationsZ and
                self.translationsX == other.translationsX and
                self.translationsY == other.translationsY and
                self.translationsZ == other.translationsZ)


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

    def DumpData(self, bw):
        bw.writeString(self.tag)
        bw.writeDword(self.sizeOfSection)
        bw.writeByte(self.loopFlags)
        bw.writeByte(self.angleMultiplier)
        bw.writeWord(self.animationLength)
        bw.writeWord(self.numJoints)
        bw.writeWord(self.scaleCount)
        bw.writeWord(self.rotCount)
        bw.writeWord(self.transCount)
        bw.writeDword(self.offsetToJoints)
        bw.writeDword(self.offsetToScales)
        bw.writeDword(self.offsetToRots)
        bw.writeDword(self.offsetToTrans)


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

    def DumpData(self, bw):
        bw.writeShort(self.count)
        bw.writeShort(self.index)
        bw.writeShort(self.zero)


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

    def DumpData(self, bw):
     self.s.DumpData(bw)
     self.r.DumpData(bw)
     self.t.DumpData(bw)
  

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

    def DumpData(self, bw):
     self.x.DumpData(bw)
     self.y.DumpData(bw)
     self.z.DumpData(bw)


# -----------------------------------------------


def translate_animation(timeOffset, bone, anim, frameScale, major, minor, default):
    """this function and the next have to be run 9x to apply transformation: pos/rot/scale and x/y/z
    this function translates animation data from `anim`, and into `bone`"""
    # some name definitions
    KEYF = major + '_kf'
    TKEYF = major + '_tkf'
    major_2 = major.replace('position', 'translation')  # incoherent naming?
    ANIM_PART = (major_2 + 's' + minor.upper())

    for j in range(len(getattr(anim, ANIM_PART))):
        key = getattr(anim, ANIM_PART)[j]
        # at time ((rot.time * frameScale) + timeOffset)
        if int(key.time * frameScale + timeOffset) not in getattr(bone, KEYF).keys():
            getattr(anim, 'frames_'+major_2).add(int(key.time * frameScale + timeOffset))
            getattr(bone, KEYF)[int(key.time * frameScale + timeOffset)] = default.copy()
            getattr(bone, TKEYF)[int(key.time * frameScale + timeOffset)] = default.copy()
        setattr(getattr(bone, KEYF)[int(key.time * frameScale + timeOffset)], minor, key.value)
        setattr(getattr(bone, TKEYF)[int(key.time * frameScale + timeOffset)], minor, key.tangent)


def complete_animation(timeOffset, bone, anim, animationLength, major, minor, default):
    """this function extrapolates more animation data, into `bone`"""
    # some name definitions
    KEYF = major + '_kf'
    TKEYF = major + '_tkf'
    major_2 = major.replace('position', 'translation')  # incoherent naming?
    ANIM_PART = (major_2 + 's' + minor.upper())
    frames = list(getattr(anim, 'frames_'+major_2))
    frames.sort()
    i0 = 0  # previous frame
    i1 = 0  # next frame
    while isnan(getattr(getattr(bone, KEYF)[frames[i1]], minor)):  # set the correct next frame
        i1 += 1
        if i1 == len(frames):  # failure case
            for i in frames:
                setattr(getattr(bone, KEYF)[i], minor, getattr(getattr(bone, KEYF)[frames[0]], minor))
                setattr(getattr(bone, TKEYF)[i], minor, 0.)
            break
    for i in range(len(frames)):  # then process frames one by one
        if isnan(getattr(getattr(bone, KEYF)[frames[i]], minor)):
            temp = cubic_interpolator(frames[i0], getattr(getattr(bone, KEYF)[frames[i0]], minor),
                                      getattr(getattr(bone, TKEYF)[frames[i0]], minor),
                                      frames[i1], getattr(getattr(bone, KEYF)[frames[i1]], minor),
                                      getattr(getattr(bone, TKEYF)[frames[i1]], minor),
                                      frames[i])
            setattr(getattr(bone, KEYF)[frames[i]], minor, temp[0])
            setattr(getattr(bone, TKEYF)[frames[i]], minor, temp[1])
        else:  # reached a new computed frame:
            if i1 == len(frames):
                break  # no more frames to calculate
            i0 = i  # reset the previous and next frames
            while isnan(getattr(getattr(bone, KEYF)[frames[i1]], minor)) or i1 <= i0:
                i1 += 1
                if i1 == len(frames):  # failure case
                    for j in frames[i0:]:  # only assume remaining frames
                        setattr(getattr(bone, KEYF)[j], minor, getattr(getattr(bone, KEYF)[frames[i0]], minor))
                        setattr(getattr(bone, TKEYF)[j], minor, 0.)
                    break

    if timeOffset not in getattr(bone, KEYF).keys():
        getattr(bone, KEYF)[timeOffset] = default.copy()
        getattr(bone, TKEYF)[timeOffset] = default.copy()
    setattr(getattr(bone, KEYF)[timeOffset], minor, getattr(getattr(bone, KEYF)[frames[0]], minor))
    # getattr(anim, ANIM_PART)[0].value
    setattr(getattr(bone, TKEYF)[timeOffset], minor, 0)

    if animationLength > 0:
        endFrame = timeOffset + animationLength

        if endFrame not in getattr(bone, KEYF).keys():
            getattr(bone, KEYF)[endFrame] = default.copy()
            getattr(bone, TKEYF)[endFrame] = default.copy()
        setattr(getattr(bone, KEYF)[endFrame], minor, getattr(getattr(bone, KEYF)[frames[-1]], minor))
        # getattr(anim, ANIM_PART)[0].value
        setattr(getattr(bone, TKEYF)[endFrame], minor, 0)


class Bck_in:
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
            log.warning("readComp(): count is <= 0")
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

    def LoadAnk1(self, br, jointnum):
        i = 0
        ank1Offset = br.Position()

        # -- read header
        h = BckAnk1Header()
        h.LoadData(br)

        if h.numJoints != jointnum:
            return  # this file will not be used anyway

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

    def LoadBck(self, filePath, jointlen):
        br = BinaryReader()
        br.Open(filePath)  #, compressed_stream=True)
        # optimise, since it will likely not be completely read
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
                self.LoadAnk1(br, jointlen)
            else:
                # MessageBox("readBck(): Unsupported section " + tag)
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
        return self.Interpolate(keys[i].value, keys[i].tangent, keys[i].value, keys[i].tangent, time)

    # still nope.
    def AnimateJnt(self, jnt, deltaTime):

        # -- update time
        self.currAnimTime += deltaTime  # --*16 -- convert from seconds to ticks (dunno if this is right this way...TODO)
        self.currAnimTime = self.currAnimTime % self.animationLength  # -- loop?

        # -- update joints
        for i in range(len(jnt.frames)):
            jnt.frames[i].sx = self.getAnimValue(self.anims[i].scalesX, self.currAnimTime)
            jnt.frames[i].sy = self.getAnimValue(self.anims[i].scalesY, self.currAnimTime)
            jnt.frames[i].sz = self.getAnimValue(self.anims[i].scalesZ, self.currAnimTime)

            # --TODO: use quaternion interpolation for rotations? nope: it will screw the keyframes up.
            jnt.frames[i].rx = self.getAnimValue(self.anims[i].rotationsX, self.currAnimTime)
            jnt.frames[i].ry = self.getAnimValue(self.anims[i].rotationsY, self.currAnimTime)
            jnt.frames[i].rz = self.getAnimValue(self.anims[i].rotationsZ, self.currAnimTime)

            jnt.frames[i].t.x = self.getAnimValue(self.anims[i].translationsX, self.currAnimTime)
            jnt.frames[i].t.y = self.getAnimValue(self.anims[i].translationsY, self.currAnimTime)
            jnt.frames[i].t.z = self.getAnimValue(self.anims[i].translationsZ, self.currAnimTime)

    # TODO: erase dummy bone system
    def GetPositionBone(self, curBone):
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
    def AnimateBoneFrames(self, timeOffset, bones, frameScale, includeScaling):
        # --alert (bones.count as string)

        for i in range(len(bones)):
            bone = bones[i]
            anim = self.anims[i]

            # position correction LATER in the program
            if includeScaling:
                translate_animation(timeOffset, bone, anim, frameScale,
                          'scale', 'x', mathutils.Vector((nan, nan, nan)))
                translate_animation(timeOffset, bone, anim, frameScale,
                          'scale', 'y', mathutils.Vector((nan, nan, nan)))
                translate_animation(timeOffset, bone, anim, frameScale,
                          'scale', 'z', mathutils.Vector((nan, nan, nan)))
            translate_animation(timeOffset, bone, anim, frameScale,
                      'rotation', 'x', mathutils.Euler((nan, nan, nan), 'XYZ'))
            translate_animation(timeOffset, bone, anim, frameScale,
                      'rotation', 'y', mathutils.Euler((nan, nan, nan), 'XYZ'))
            translate_animation(timeOffset, bone, anim, frameScale,
                      'rotation', 'z', mathutils.Euler((nan, nan, nan), 'XYZ'))
            translate_animation(timeOffset, bone, anim, frameScale,
                      'position', 'x', mathutils.Vector((nan, nan, nan)))
            translate_animation(timeOffset, bone, anim, frameScale,
                      'position', 'y', mathutils.Vector((nan, nan, nan)))
            translate_animation(timeOffset, bone, anim, frameScale,
                      'position', 'z', mathutils.Vector((nan, nan, nan)))

            if includeScaling:
                complete_animation(timeOffset, bone, anim, self.animationLength,
                                    'scale', 'x', mathutils.Vector((nan, nan, nan)))
                complete_animation(timeOffset, bone, anim, self.animationLength,
                                    'scale', 'y', mathutils.Vector((nan, nan, nan)))
                complete_animation(timeOffset, bone, anim, self.animationLength,
                                    'scale', 'z', mathutils.Vector((nan, nan, nan)))
            complete_animation(timeOffset, bone, anim, self.animationLength,
                                'rotation', 'x', mathutils.Euler((nan, nan, nan), 'XYZ'))
            complete_animation(timeOffset, bone, anim, self.animationLength,
                                'rotation', 'y', mathutils.Euler((nan, nan, nan), 'XYZ'))
            complete_animation(timeOffset, bone, anim, self.animationLength,
                                'rotation', 'z', mathutils.Euler((nan, nan, nan), 'XYZ'))
            complete_animation(timeOffset, bone, anim, self.animationLength,
                                'position', 'x', mathutils.Vector((nan, nan, nan)))
            complete_animation(timeOffset, bone, anim, self.animationLength,
                                'position', 'y', mathutils.Vector((nan, nan, nan)))
            complete_animation(timeOffset, bone, anim, self.animationLength,
                                'position', 'z', mathutils.Vector((nan, nan, nan)))


class Bck_out:

    def __init__(self):
        self.maxframe=0

    def calcmultiplier(self, anims):
        ret = 1  # number of total full turns

    def dump_data(self, dst, src):
        index = BckAnimIndex()
        index.zero = 0
        index.count = len(src)
        if len(src) == 1:
            if src[0].time or src[0].tangent:  # if non-zero
                raise ValueError("static animation should be static")
            if src[0].value in dst:
                index.index = dst.index(src[0].value)
            else:
                dst.append(src[0].value)
                index.index = len(dst)-1

        else:
            index.index = len(dst)
            for com in src:
                dst.append(com.time)
                self.maxframe = max(self.maxframe, com.time)
                dst.append(com.value)
                dst.append(com.tangent)

        return index

    def calibrate_rotation(self, rots, scale):
        for j in range(len(rots)):  #
            rots[j].value = round(rots[j].value / scale)
            rots[j].tangent = round(rots[j].tangent / scale)

    def write_junk(self, bw, bcount):
        string = 'Padding '
        string = string * int(ceil(bcount/len(string)))
        bw.writeString(string[:bcount])

    def dump_ank1(self, anims, bw):

        Ank1Offset = bw.Position()
        h = BckAnk1Header()
        h.angleMultiplier = 1  # self.calcmultiplier(anims)
        rot_scale = (pow(2., h.angleMultiplier) * pi / 32768.)

        positions = []
        rotations = []
        scales = []
        joints = []


        for anim in anims:
            joint = BckAnimatedJoint()
            joints.append(joint)
            joint.x = BckAnimComponent()
            joint.y = BckAnimComponent()
            joint.z = BckAnimComponent()

            joint.x.s = self.dump_data(scales, anim.scalesX)
            joint.y.s = self.dump_data(scales, anim.scalesY)
            joint.z.s = self.dump_data(scales, anim.scalesZ)

            joint.x.t = self.dump_data(positions, anim.translationsX)
            joint.y.t = self.dump_data(positions, anim.translationsY)
            joint.z.t = self.dump_data(positions, anim.translationsZ)

            self.calibrate_rotation(anim.rotationsX, rot_scale)
            self.calibrate_rotation(anim.rotationsY, rot_scale)
            self.calibrate_rotation(anim.rotationsZ, rot_scale)
            joint.x.r = self.dump_data(rotations, anim.rotationsX)
            joint.y.r = self.dump_data(rotations, anim.rotationsY)
            joint.z.r = self.dump_data(rotations, anim.rotationsZ)

        h.numJoints = len(joints)
        h.scaleCount = len(scales)
        h.rotCount = len(rotations)
        h.transCount = len(positions)
        h.offsetToJoints = 64
        h.offsetToScales = ceil(h.numJoints*3*3*3*2/16)*16 + h.offsetToJoints
        h.offsetToRots = ceil(h.scaleCount*4/16)*16 + h.offsetToScales
        h.offsetToTrans = ceil(h.rotCount*2/16)*16 + h.offsetToRots
        h.animationLength = self.maxframe
        h.tag = 'ANK1'
        h.sizeOfSection = h.offsetToTrans + ceil(h.transCount*4/16)*16 +16
        h.loopFlags = 0  # 0: once, 2: loop

        h.DumpData(bw)
        self.write_junk(bw, h.offsetToJoints+Ank1Offset - bw.Position())
        for joint in joints:
            joint.DumpData(bw)
        self.write_junk(bw, h.offsetToScales+Ank1Offset - bw.Position())
        for val in scales:
            bw.WriteFloat(val)
        self.write_junk(bw, h.offsetToRots+Ank1Offset - bw.Position())
        for val in rotations:
            bw.writeShort(val)
        self.write_junk(bw, h.offsetToTrans+Ank1Offset - bw.Position())
        for val in positions:
            bw.WriteFloat(val)
        self.write_junk(bw, h.sizeOfSection+ Ank1Offset - bw.Position())

    def dump_bck(self, anims, filePath):
        bw = BinaryWriter()
        bw.Open(filePath)
        #bw.SeekSet(0x20)
        for _ in range(32):
            bw.writeByte(0x00)
        self.dump_ank1(anims, bw)
        bw.Close()


def create_static_animation(frames):
    anims=[]
    for fr in frames:
        anim = BckJointAnim()
        anims.append(anim)
        anim.scalesX.append(BckKey())
        anim.scalesY.append(BckKey())
        anim.scalesZ.append(BckKey())
        anim.rotationsX.append(BckKey())
        anim.rotationsY.append(BckKey())
        anim.rotationsZ.append(BckKey())
        anim.translationsX.append(BckKey())
        anim.translationsY.append(BckKey())
        anim.translationsZ.append(BckKey())

        anim.scalesX[0].value = fr.sx
        anim.scalesY[0].value = fr.sy
        anim.scalesZ[0].value = fr.sz
        anim.rotationsX[0].value = fr.rx
        anim.rotationsY[0].value = fr.ry
        anim.rotationsZ[0].value = fr.rz
        anim.translationsX[0].value = fr.t.x
        anim.translationsY[0].value = fr.t.y  # dont reflip translation values
        anim.translationsZ[0].value = fr.t.z
    return anims

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
