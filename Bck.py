#! /usr/bin/python3
from .BinaryReader import BinaryReader
from .BinaryWriter import BinaryWriter
from .pseudobones import getBoneByName
import mathutils
import bpy
import logging
log = logging.getLogger('bpy.ops.import_mesh.bmd.bck')
from math import nan, pi, isnan, isclose, ceil, radians, degrees
from enum import Enum


EPSILON = 1E-4


class LoopType(Enum):
    ONESHOT = 0
    ONESHOT_RESET = 1
    LOOP = 2
    YOYO_ONCE = 3
    YOYO_LOOP = 4


class BckKey:
    def __init__(self, tm=0, vl=0.0, tgL=0.0, tgR=0.0):
        self.time = tm
        self.value = vl
        self.tangentL = tgL
        self.tangentR = tgR

    def __lt__(self, other):
        return self.time < other.time

    def __eq__(self, other):
        return (self.time == other.time and
                isclose(self.value, other.value, rel_tol=1E-3) and
                isclose(self.tangentL, other.tangentL, rel_tol=1E-3) and
                isclose(self.tangentR, other.tangentR, rel_tol=1E-3))


class BckJointAnim:
    def __init__(self): 
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
        return (
            self.scalesX == other.scalesX and
            self.scalesY == other.scalesY and
            self.scalesZ == other.scalesZ and
            self.rotationsX == other.rotationsX and
            self.rotationsY == other.rotationsY and
            self.rotationsZ == other.rotationsZ and
            self.translationsX == other.translationsX and
            self.translationsY == other.translationsY and
            self.translationsZ == other.translationsZ
        )


class BckAnk1Header:

    def LoadData(self, br):                
      self.tag = br.ReadFixedLengthString(4)  # "ANK1"
      self.sizeOfSection = br.ReadDWORD()
      self.loopFlags = LoopType(br.GetByte())
      self.angleMultiplier = br.GetByte()  # multiply angles by 2**multiplier
      self.animationLength = br.ReadWORD()
      self.numJoints = br.ReadWORD()  # in time units?
      self.scaleCount = br.ReadWORD()
      self.rotCount = br.ReadWORD()
      self.transCount = br.ReadWORD()
      self.offsetToJoints = br.ReadDWORD()
      self.offsetToScales = br.ReadDWORD()
      self.offsetToRots = br.ReadDWORD()
      self.offsetToTrans = br.ReadDWORD()

    def DumpData(self, bw):
        bw.writeString(self.tag)
        bw.writeDword(self.sizeOfSection)
        bw.writeByte(self.loopFlags.value)
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


# -- TODO: the following two structs have really silly names, rename them

class BckAnimIndex:
    def LoadData(self, br):
        self.count = br.GetSHORT()
        self.index = br.GetSHORT()
        self.double_tangent = br.GetSHORT()  # note: are there other values than 0 or 1?
        if self.double_tangent not in (0,1):
            log.warning("BckAnimIndex: unknown value of `double_tangent`: {:d}", self.double_tangent)            

    def DumpData(self, bw):
        bw.writeShort(self.count)
        bw.writeShort(self.index)
        bw.writeShort(self.double_tangent)


class BckAnimComponent:
    def __init__(self):
        self.s= BckAnimIndex()  # scale
        self.r= BckAnimIndex()  # rotation
        self.t= BckAnimIndex()  # translation

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

    def __init__(self):
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


class Bck_in:
    def __init__(self):  # GENERATED!
        self.anims = []
        self.loopType = LoopType(0)

    def ConvRotation(self, rots, scale):
        for rot in rots:
            rot.value *= scale
            rot.tangentL *= scale
            rot.tangentR *= scale
        return rots

    def ReadComp(self, src, index):
        if index.count <= 0:
            log.warning("readComp(): count is <= 0")
            return [BckKey()]
        dst = [BckKey() for _ in range(index.count)]

        if index.count == 1:
            dst[0].time = 0
            dst[0].value = src[index.index]
            dst[0].tangentL = 0
            dst[0].tangentR = 0
        elif index.double_tangent == 0:
            for j in range(index.count):
                dst[j].time = src[(index.index + 3*j)]
                dst[j].value = src[(index.index + 3*j + 1)]
                dst[j].tangent_L = src[(index.index + 3*j + 2)]
                dst[j].tangent_R = src[(index.index + 3*j + 2)]
        elif index.double_tangent == 1:
            for j in range(index.count):
                while len(dst) <= j:
                    dst.append(None)
                dst[j] = BckKey()
                dst[j].time = src[(index.index + 4 * j)]
                dst[j].value = src[(index.index + 4 * j + 1)]
                dst[j].tangent_L = src[(index.index + 4 * j + 2)]
                dst[j].tangent_R = src[(index.index + 4 * j + 3)]
        else:
            log.error("readComp(): unknown `double_tangent` value %d. This animation wil not be loaded", index.double_tangent)
            dst = [BckKey()]
        return dst

    def LoadAnk1(self, br, jointnum):
        i = 0
        ank1Offset = br.Position()

        # read header
        h = BckAnk1Header()
        h.LoadData(br)

        if h.numJoints != jointnum:
            # if the number of bones in the animation do not match the number of bones in the model, reject the animation
            return

        self.loopType = h.loopFlags
           
        self.currAnimTime = 0.0
        self.animationLength = h.animationLength

        # read scale floats:
        br.SeekSet(ank1Offset + h.offsetToScales)
        scales = [br.GetFloat() for _ in range(h.scaleCount)]

        # read rotation s16s:
        br.SeekSet(ank1Offset + h.offsetToRots)
        rotations = [br.GetSHORT() for _ in range(h.rotCount)]

        # read translation floats:
        br.SeekSet(ank1Offset + h.offsetToTrans)
        translations = [br.GetFloat() for _ in range(h.transCount)]

        # read joints
        rotScale = (pow(2., h.angleMultiplier) * pi / 32768.)  # result in RADIANS  per increment (in a short)
        br.SeekSet(ank1Offset + h.offsetToJoints)
        self.anims = [BckJointAnim() for _ in range(h.numJoints)]
        # bck.self.anims.resize(h.numJoints);

        for i in range(h.numJoints):
            joint = BckAnimatedJoint()
            joint.LoadData(br)

            # -- IMPORTANT: scale values are absolute and not related to the parent
            # -- e.g Bone A (scale=200%), Bone B (Scale=200%), Bone C (Scale=100%). Bone A is the parent of Bone B and Bone B is the parent of Bone C
            # --  need to remove the parent scaling. e.g Bone C shouldn't change in size but in 3DS max it will equal 400% (2 * 2 * 1 * 100)
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
                log.warning("Bck file at {:s}: corrupt size of section. Is this really a bck file?", filePath)
                size = 8  #  prevent endless loop on corrupt data

            br.SeekSet(pos)

            if tag == "ANK1":
                self.LoadAnk1(br, jointlen)
            else:
                raise ValueError("Bck file at "+filePath+": Unsupported section " + tag)
            br.SeekSet(pos)
            i += 1
        br.Close()

    # TODO: erase dummy bone system
    def GetPositionBone(self, curBone):
        dummyBone = getBoneByName(curBone.name.fget() + "_dummy")
        if dummyBone is None:
            return curBone
        else:
            return dummyBone

    def AnimateBoneFrames(self, timeOffset, bones, frameScale, includeScaling):
        for i in range(len(bones)):
            bone = bones[i]
            anim = self.anims[i]
            bone.frames.feed_anim(anim, includeScaling, frameScale, timeOffset)


class Bck_out:

    def __init__(self):
        self.maxframe=0
        self.anims = []

    def calcmultiplier(self, anims):
        ret = 1  # number of total full turns

    def dump_action(self, action, pose):
        self.loopType = LoopType[getattr(action, "bck_loop_type", 0)]
        self.maxframe = int(action.frame_range[1] - action.frame_range[0])
        
        z_to_y_mtx = mathutils.Matrix.Rotation(radians(-90.), 4, mathutils.Vector((1., 0., 0.)))
        
        for b in pose.bones:
            print(b.name)
            
            parent_mtx = mathutils.Matrix.Identity(4)
            
            if b.bone.parent is not None:
                parent_mtx = b.bone.parent.matrix_local
                
            local_matrix = z_to_y_mtx @ parent_mtx.inverted() @ b.bone.matrix_local @ z_to_y_mtx.inverted()
            
            joint_anim = BckJointAnim()
            fcurve_path = f'pose.bones["{ b.name }"]'
            
            trans_fcurves = [fcu for fcu in action.fcurves if fcu.data_path.startswith(fcurve_path + ".location")]
            rot_fcurves = [fcu for fcu in action.fcurves if fcu.data_path.startswith(fcurve_path + ".rotation_euler")]
            scale_fcurves = [fcu for fcu in action.fcurves if fcu.data_path.startswith(fcurve_path + ".scale")]

            for f in range(self.maxframe + 1):
              self.process_translation_track(trans_fcurves, f, joint_anim, local_matrix)
              self.process_rotation_track(rot_fcurves, f, joint_anim, local_matrix)
              self.process_scale_track(scale_fcurves, f, joint_anim, local_matrix)
                    
            self.anims.append(joint_anim)
    
    def get_key_value(self, curve, frame):
        keyframe = next((k for k in curve.keyframe_points if k.co[0] == frame), None)
        
        if keyframe is not None:
            return (keyframe.co, keyframe.handle_left, keyframe.handle_right)
            
        return (None, None, None)
    
    def get_track_keyframe(self, x_curve, y_curve, z_curve, frame):
        (x_co, x_handle_left, x_handle_right) = self.get_key_value(x_curve, frame)
        (y_co, y_handle_left, y_handle_right) = self.get_key_value(y_curve, frame)
        (z_co, z_handle_left, z_handle_right) = self.get_key_value(z_curve, frame)
        
        if x_co is not None and y_co is not None and z_co is not None:
            keyframe_value = (x_co[1], y_co[1], z_co[1])

            if abs(x_co[0]-x_handle_left[0])<1E-2:
                x_tangent_left = 0  # note: we do not support "infinite" tangents at keyframes
            else:
                x_tangent_left = (x_co[1] - x_handle_left[1])/(x_co[0] - x_handle_left[0])
            if abs(x_co[0] - x_handle_right[0])<1E-2:
                x_tangent_right = 0  # note: we do not support "infinite" tangents at keyframes
            else:
                x_tangent_right = (x_handle_right[1] - x_co[1])/(x_handle_left[0] - x_co[0])

            if abs(y_co[0] - y_handle_left[0])<1E-2:
                y_tangent_left = 0  # note: we do not support "infinite" tangents at keyframes
            else:
                y_tangent_left = (y_co[1] - y_handle_left[1])/(y_co[0] - y_handle_left[0])
            if abs(y_co[0] - y_handle_right[0])<1E-2:
                y_tangent_right = 0  # note: we do not support "infinite" tangents at keyframes
            else:
                y_tangent_right = (y_handle_right[1] - y_co[1])/(y_handle_left[0] - y_co[0])

            if abs(z_co[0] - z_handle_left[0])<1E-2:
                z_tangent_left = 0  # note: we do not support "infinite" tangents at keyframes
            else:
                z_tangent_left = (z_co[1] - z_handle_left[1])/(z_co[0] - z_handle_left[0])
            if abs(z_co[0] - z_handle_right[0])<1E-2:
                z_tangent_right = 0  # note: we do not support "infinite" tangents at keyframes
            else:
                z_tangent_right = (z_handle_right[1] - z_co[1])/(z_handle_left[0] - z_co[0])
            tangent_left = (x_tangent_left, y_tangent_left, z_tangent_left)
            tangent_right = (x_tangent_right, y_tangent_right, z_tangent_right)
        else:
            keyframe_value = None
            tangent_left = None
            tangent_right = None
        
        return (keyframe_value, tangent_left, tangent_right)
    
    def process_translation_track(self, curves, frame, anim, local_matrix):
        x_track = None
        y_track = None
        z_track = None
        
        for f in curves:
            if f.array_index == 0:
                x_track = f
            elif f.array_index == 1:
                y_track = f
            elif f.array_index == 2:
                z_track = f
            else:
                print(f'Unknown fcurve array index "{ f.array_index }"!')
                return
        
        value, handle_left, handle_right = self.get_track_keyframe(x_track, y_track, z_track, frame)
        if value is None:
            return
        
        trans_vec = local_matrix @ mathutils.Vector((value[0], value[2], value[1] * -1.))
        x_bck_key = BckKey()
        x_bck_key.time = frame
        x_bck_key.tangentL = handle_left[0]
        x_bck_key.tangentR = handle_right[0]
        x_bck_key.value = trans_vec[0]
        anim.translationsX.append(x_bck_key)
        
        y_bck_key = BckKey()
        y_bck_key.time = frame
        y_bck_key.tangentL = handle_left[1]
        y_bck_key.tangentR = handle_right[1]
        y_bck_key.value = trans_vec[1]
        anim.translationsY.append(y_bck_key)
        
        z_bck_key = BckKey()
        z_bck_key.time = frame
        z_bck_key.tangentL = handle_left[2]
        z_bck_key.tangentR = handle_right[2]
        z_bck_key.value = trans_vec[2]
        anim.translationsZ.append(z_bck_key)
        
        # Keeping one of the original loops for reference
        #for k in x_track.keyframe_points:
        #    bck_key = BckKey()
        #    
        #    bck_key.time = k.co[0]
        #    bck_key.tangentL = (k.handle_left[1] * EPSILON) + k.co[1]
        #    bck_key.tangentR = (k.handle_right[1] * EPSILON) + k.co[1]
        #    
        #    vec = mathutils.Vector((k.co[1], 0., 0.))
        #    vec = local_matrix @ vec
        #    
        #    bck_key.value = vec[0]
        #    anim.translationsX.append(bck_key)

    def correct_rotation(self, value):
        if isclose(value, pi, rel_tol=0.001):
            value -= 2.0 * pi
        elif isclose(value, -1.0 * pi, rel_tol=0.001):
            value += 2.0 * pi
            
        return value
    
    def process_rotation_track(self, curves, frame, anim, local_matrix):
        x_track = None
        y_track = None
        z_track = None
        
        for f in curves:
            if f.array_index == 0:
                x_track = f
            elif f.array_index == 1:
                y_track = f
            elif f.array_index == 2:
                z_track = f
            else:
                print(f'Unknown fcurve array index "{ f.array_index }"!')
                return
        
        value, handle_left, handle_right = self.get_track_keyframe(x_track, y_track, z_track, frame)
        if value is None:
            return
        
        rot_euler = mathutils.Euler((value[0], value[2], value[1] * -1.), 'XYZ')
        rot_euler.rotate(local_matrix.to_quaternion())
        print(rot_euler)
        
        x_bck_key = BckKey()
        x_bck_key.time = frame
        x_bck_key.tangentL = handle_left[0]
        x_bck_key.tangentR = handle_right[0]
        x_bck_key.value = self.correct_rotation(rot_euler[0])
        anim.rotationsX.append(x_bck_key)
        
        y_bck_key = BckKey()
        y_bck_key.time = frame
        y_bck_key.tangentL = handle_left[1]
        y_bck_key.tangentR = handle_right[1]
        y_bck_key.value = self.correct_rotation(rot_euler[1])
        anim.rotationsY.append(y_bck_key)
        
        z_bck_key = BckKey()
        z_bck_key.time = frame
        z_bck_key.tangentL = handle_left[2]
        z_bck_key.tangentR = handle_right[2]
        z_bck_key.value = self.correct_rotation(rot_euler[2])
        anim.rotationsZ.append(z_bck_key)
        
        # Keeping one of the original loops for reference
        #for k in x_track.keyframe_points:
        #    bck_key = BckKey()
        #    
        #    bck_key.time = k.co[0]
        #    bck_key.tangentL = (k.handle_left[1] * EPSILON) + k.co[1]
        #    bck_key.tangentR = (k.handle_right[1] * EPSILON) + k.co[1]
        #    
        #    euler = mathutils.Euler((k.co[1], 0., 0.), 'XYZ')
        #    euler.rotate(local_matrix.to_quaternion())
        #    
        #    print(f'x rot: { euler[0]} ')
        #    bck_key.value = euler[0]
        #    anim.rotationsX.append(bck_key)
        
    def process_scale_track(self, curves, frame, anim, local_matrix):
        x_track = None
        y_track = None
        z_track = None
        
        for f in curves:
            if f.array_index == 0:
                x_track = f
            elif f.array_index == 1:
                y_track = f
            elif f.array_index == 2:
                z_track = f
            else:
                print(f'Unknown fcurve array index "{ f.array_index }"!')
                return
        
        value, handle_left, handle_right = self.get_track_keyframe(x_track, y_track, z_track, frame)
        if value is None:
            return
        
        scale_vec = mathutils.Vector((value[0], value[2], value[1]))
        
        x_bck_key = BckKey()
        x_bck_key.time = frame
        x_bck_key.tangentL = handle_left[0]
        x_bck_key.tangentR = handle_right[0]
        x_bck_key.value = scale_vec[0]
        anim.scalesX.append(x_bck_key)
        
        y_bck_key = BckKey()
        y_bck_key.time = frame
        y_bck_key.tangentL = handle_left[1]
        y_bck_key.tangentR = handle_right[1]
        y_bck_key.value = scale_vec[1]
        anim.scalesY.append(y_bck_key)
        
        z_bck_key = BckKey()
        z_bck_key.time = frame
        z_bck_key.tangentL = handle_left[2]
        z_bck_key.tangentR = handle_right[2]
        z_bck_key.value = scale_vec[2]
        anim.scalesZ.append(z_bck_key)
                
        #for k in x_track.keyframe_points:
        #    bck_key = BckKey()
        #    
        #    bck_key.time = k.co[0]
        #    bck_key.tangentL = (k.handle_left[1] * EPSILON) + k.co[1]
        #    bck_key.tangentR = (k.handle_right[1] * EPSILON) + k.co[1]
        #    
        #    vec = mathutils.Vector((k.co[1], 0., 0.))
        #    
        #    bck_key.value = 1. #vec[0]
        #    anim.scalesX.append(bck_key)

    def dump_data(self, dst, src):
        index = BckAnimIndex()
        index.double_tangent = 1
        index.count = len(src)
        if len(src) == 1:
            #if src[0].time or src[0].tangentL or src[0].tangentR:  # if non-zero
            #    raise ValueError("static animation should be static")
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
                dst.append(com.tangentL)
                dst.append(com.tangentR)  # TODO simplify for identiqual tangents

        return index

    def calibrate_rotation(self, rots, scale):
        for j in range(len(rots)):  #
            rots[j].value = round(rots[j].value / scale)
            rots[j].tangentL = round(rots[j].tangentL / scale)
            rots[j].tangentR = round(rots[j].tangentR / scale)

    def dump_ank1(self, bw):

        Ank1Offset = bw.Position()
        h = BckAnk1Header()
        h.angleMultiplier = 1  # self.calcmultiplier(anims)
        rot_scale = (pow(2., h.angleMultiplier) * (pi / 32768.))

        positions = []
        rotations = []
        scales = []
        joints = []


        for anim in self.anims:
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
        h.animationLength = int(self.maxframe)
        h.tag = 'ANK1'
        h.sizeOfSection = h.offsetToTrans + ceil(h.transCount*4/16)*16 +16
        h.loopFlags = self.loopType

        h.DumpData(bw)
        bw.writePadding(h.offsetToJoints+Ank1Offset - bw.Position())
        for joint in joints:
            joint.DumpData(bw)
        bw.writePadding(h.offsetToScales+Ank1Offset - bw.Position())
        for val in scales:
            bw.writeFloat(val)
        bw.writePadding(h.offsetToRots+Ank1Offset - bw.Position())
        for val in rotations:
            bw.writeShort(val)
        bw.writePadding(h.offsetToTrans+Ank1Offset - bw.Position())
        for val in positions:
            bw.writeFloat(val)
        bw.writePadding(h.sizeOfSection+ Ank1Offset - bw.Position())

    def dump_bck(self, filePath):
        bw = BinaryWriter()
        bw.Open(filePath)
        
        # File version info
        bw.writeString("J3D1bck1")
        
        # Placeholder for file size
        bw.writeDword(0x00)
        
        # Number of sections, only 1 here (ANK1)
        bw.writeDword(0x01)
        
        blemd_watermark = "BleMD"
        # The next 0xC bytes of the header are not used, so we can put a watermark here.
        bw.writeString(blemd_watermark)
        for _ in range(0x0C - len(blemd_watermark)):
            bw.writeByte(0xFF)
        
        # The last 4 bytes of the header CAN be used for sound effects, but that's not supported right now.
        bw.writeDword(0xFFFFFFFF)
        
        self.dump_ank1(bw)
        
        file_size = bw.Position()
        
        # Set file size field
        bw.SeekSet(0x08)
        bw.writeDword(file_size)
        
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
