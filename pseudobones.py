from mathutils import Vector, Euler, Matrix
import bpy
import math
import re
from .common import dict_get_set
from . import common
from .Matrix44 import rotation_part
# import weakref
import logging
log = logging.getLogger('bpy.ops.import_mesh.bmd.pseudobones')

NtoB = Matrix([[1,0,0,0],
               [0,0,-1,0],
               [0,1,0,0],
               [0,0,0,1]])
BtoN = Matrix([[1,0,0,0],
               [0,0,1,0],
               [0,-1,0,0],
               [0,0,0,1]])


def product(lamb, vct):
    ret = vct.copy()
    ret.x *= lamb
    ret.y *= lamb
    ret.z *= lamb
    return ret


def sum2(vct1, vct2):
    ret = vct1.copy()
    ret.x += vct2.x
    ret.y += vct2.y
    ret.z += vct2.z
    return ret


def subtract2(vct1, vct2):
    ret = vct1.copy()
    ret.x -= vct2.x
    ret.y -= vct2.y
    ret.z -= vct2.z
    return ret


def vect_normalize(vect):
    length = math.sqrt(vect.x**2 + vect.y**2 + vect.z**2)
    if length < .01:
        log.error('Vector to be normalized is near zero. Returning (0,0,1) to avoid crashes')
        return Vector((0,0,1))
    tempv = vect
    tempv.x /= length
    tempv.y /= length
    tempv.z /= length
    return tempv


def cubic_interpolator(t1, y1, d1, t2, y2, d2, t):
    if -0.001 < t2-t1 < 0.001:
        log.warning('cannot interpolate between almost identiqual times')
        return (y1+y2) / 2,  0
    tn = (t-t1)/(t2-t1)  # normalized time coordinate
    d1 *= (t2-t1)  # adapted derivatives for the normalized time interval
    d2 *= (t2-t1)

    # temporary values
    # for the value
    ya = (2*tn**3 - 3*tn**2 + 1)*y1
    yb = (tn**3 - 2*tn**2 + tn)*d1
    yc = (-2*tn**3 + 3*tn**2)*y2
    yd = (tn**3 - tn**2)*d2

    # and the tangent (will have to be corrected since d(a(b))=d(b)*d(a)(b))
    da = (6*tn**2 - 6*tn) * y1
    db = (3*tn**2 - 4*tn + 1) * d1
    dc = (-6*tn**2 + 6*tn) * y2
    dd = (3*tn**2 - 2*tn) * d2

    y = ya+yb+yc+yd
    d = (da+db+dc+dd)/(t2-t1)

    return y, d, d


###
# the goal here is to get the matrix adapted to blender animation
# (from  default pose to correct pose)
# in blender, the matrix chain looks like
# this (each contains translation and rotation):
# origin_s*origin_d*bone_1_s*bone_1_d*....*bone_n_s*bone_n_d

def get_dynamic_mtx(p_bone, frame):
    if frame not in p_bone.computed_d_matrices.keys():
        local_mtx_y, local_mtx_ydL, local_mtx_ydR = p_bone.frames.get_mtx(frame)
        inv_static_mtx = p_bone.jnt_frame.getFrameMatrix().inverted()
        p_bone.computed_d_matrices[frame] = (inv_static_mtx @ local_mtx_y,
                                             inv_static_mtx @ local_mtx_ydL,
                                             inv_static_mtx @ local_mtx_ydR)
    return p_bone.computed_d_matrices[frame]


def get_pos_vct(p_bone, frame):
    EPSILON = 1E-4
    y, ydL, ydR = get_dynamic_mtx(p_bone, frame)
    y = y.to_translation()
    ydL = ydL.to_translation()
    ydR = ydR.to_translation()
    # yd = get_dynamic_mtx(p_bone, frame+EPSILON).position()
    dL = (ydL-y)/EPSILON
    dR = (ydR-y)/EPSILON
    return y, dL, dR


def get_rot_vct(p_bone, frame):
    EPSILON = 1E-4
    y, ydL, ydR = get_dynamic_mtx(p_bone, frame)
    y = y.to_euler('XYZ')
    ydL = ydL.to_euler('XYZ')
    ydR = ydR.to_euler('XYZ')
    # yd = get_dynamic_mtx(p_bone, frame+EPSILON).rotation()
    dL = product(1/EPSILON, subtract2(ydL, y))
    dR = product(1/EPSILON, subtract2(ydR, y))
    return y, dL, dR


def get_sc_vct(p_bone, frame):

    y, dL, dR = p_bone.frames.get_sc(frame)

    y.x /= p_bone.jnt_frame.sx
    y.y /= p_bone.jnt_frame.sy
    y.z /= p_bone.jnt_frame.sz

    dL.x /= p_bone.jnt_frame.sx
    dL.y /= p_bone.jnt_frame.sy
    dL.z /= p_bone.jnt_frame.sz

    dR.x /= p_bone.jnt_frame.sx
    dR.y /= p_bone.jnt_frame.sy
    dR.z /= p_bone.jnt_frame.sz

    return y, dL, dR


instances = {}


class KeyFrames:
    def __init__(self):
        self.times = {}
        self.positions = [{}, {}, {}]
        self.rotations = [{}, {}, {}]
        self.scales = [{}, {}, {}]

    def feed_anim(self, anim, include_sc=True, fr_sc=1, fr_of=0):
        for key in anim.translationsX:
            frame_time = int(fr_sc*key.time+fr_of)
            self.positions[0][frame_time] = (key.value, key.tangentL, key.tangentR)
            dict_get_set(self.times, frame_time, [False, False, False])[0] = True
        for key in anim.translationsY:
            frame_time = int(fr_sc*key.time+fr_of)
            self.positions[1][frame_time] = (key.value, key.tangentL, key.tangentR)
            dict_get_set(self.times, frame_time, [False, False, False])[0] = True
        for key in anim.translationsZ:
            frame_time = int(fr_sc*key.time+fr_of)
            self.positions[2][frame_time] = (key.value, key.tangentL, key.tangentR)
            dict_get_set(self.times, frame_time, [False, False, False])[0] = True

        for key in anim.rotationsX:
            frame_time = int(fr_sc*key.time+fr_of)
            self.rotations[0][frame_time] = (key.value, key.tangentL, key.tangentR)
            dict_get_set(self.times, frame_time, [False, False, False])[1] = True
        for key in anim.rotationsY:
            frame_time = int(fr_sc*key.time+fr_of)
            self.rotations[1][frame_time] = (key.value, key.tangentL, key.tangentR)
            dict_get_set(self.times, frame_time, [False, False, False])[1] = True
        for key in anim.rotationsZ:
            frame_time = int(fr_sc*key.time+fr_of)
            self.rotations[2][frame_time] = (key.value, key.tangentL, key.tangentR)
            dict_get_set(self.times, frame_time, [False, False, False])[1] = True
        if include_sc:
            for key in anim.scalesX:
                frame_time = int(fr_sc*key.time+fr_of)
                self.scales[0][frame_time] = (key.value, key.tangentL, key.tangentR)
                dict_get_set(self.times, frame_time, [False, False, False])[2] = True
            for key in anim.scalesY:
                frame_time = int(fr_sc*key.time+fr_of)
                self.scales[1][frame_time] = (key.value, key.tangentL, key.tangentR)
                dict_get_set(self.times, frame_time, [False, False, False])[2] = True
            for key in anim.scalesZ:
                frame_time = int(fr_sc*key.time+fr_of)
                self.scales[2][frame_time] = (key.value, key.tangentL, key.tangentR)
                dict_get_set(self.times, frame_time, [False, False, False])[2] = True

        # add last frame on everything (to avoid crashes), but not register them as 'real'

        anim_length = max(self.times.keys())
        for coordinate in (0,1,2):
            max_time = max(self.positions[coordinate].keys())
            if max_time < anim_length:
                self.positions[coordinate][anim_length] = self.positions[coordinate][max_time]
            max_time = max(self.rotations[coordinate].keys())
            if max_time < anim_length:
                self.rotations[coordinate][anim_length] = self.rotations[coordinate][max_time]
            max_time = max(self.scales[coordinate].keys())
            if max_time < anim_length:
                self.scales[coordinate][anim_length] = self.scales[coordinate][max_time]


    def _get_vt(self, data, time):
        if time in data.keys():
            return data[time]
        elif len(data.keys()) == 1:
            return next(iter(data.values()))
        prev_t = -math.inf
        next_t = +math.inf
        for frame_t in data.keys():
            if prev_t < frame_t < time:
                prev_t = frame_t
            elif time < frame_t < next_t:
                next_t = frame_t

        return cubic_interpolator(prev_t, data[prev_t][0], data[prev_t][2],
                                  next_t, data[next_t][0], data[next_t][1], time)

    def get_pos(self, time):
        temp_x = self._get_vt(self.positions[0], time)
        temp_y = self._get_vt(self.positions[1], time)
        temp_z = self._get_vt(self.positions[2], time)
        return (Vector((temp_x[0], temp_y[0], temp_z[0])),
                Vector((temp_x[1], temp_y[1], temp_z[1])),
                Vector((temp_x[2], temp_y[2], temp_z[2])))

    def get_rot(self, time):
        temp_x = self._get_vt(self.rotations[0], time)
        temp_y = self._get_vt(self.rotations[1], time)
        temp_z = self._get_vt(self.rotations[2], time)
        return (Euler((temp_x[0], temp_y[0], temp_z[0]), 'XYZ'),
                Euler((temp_x[1], temp_y[1], temp_z[1]), 'XYZ'),
                Euler((temp_x[2], temp_y[2], temp_z[2]), 'XYZ'))

    def get_sc(self, time):
        temp_x = self._get_vt(self.scales[0], time)
        temp_y = self._get_vt(self.scales[1], time)
        temp_z = self._get_vt(self.scales[2], time)
        return (Vector((temp_x[0], temp_y[0], temp_z[0])),
                Vector((temp_x[1], temp_y[1], temp_z[1])),
                Vector((temp_x[2], temp_y[2], temp_z[2])))

    def get_mtx(self, time):
        EPSILON = 1E-4
        vct_y, vct_dL, vct_dR = self.get_pos(time)
        rot_y, rot_dL, rot_dR = self.get_rot(time)
        vct_ydL = sum2(vct_y, product(EPSILON, vct_dL))
        rot_ydL = sum2(rot_y, product(EPSILON, rot_dL))
        vct_ydR = sum2(vct_y, product(EPSILON, vct_dR))
        rot_ydR = sum2(rot_y, product(EPSILON, rot_dR))
        return ( (Matrix.Translation(vct_y) @ rot_y.to_matrix().to_4x4()),
                 (Matrix.Translation(vct_ydL) @ rot_ydL.to_matrix().to_4x4()),
                 (Matrix.Translation(vct_ydR) @ rot_ydR.to_matrix().to_4x4()) )


class Pseudobone:
    def __init__(self, parentBone, frame, matrix, startpoint, endpoint):

        self._name = None
        ori = endpoint - startpoint
        self.endpoint = endpoint
        self.length = math.sqrt(ori.x**2 + ori.y**2 + ori.z**2)
        self.orientation = vect_normalize(ori)
        self.scale = Vector((1, 1, 1))
        self.jnt_frame = None
        # self.rotation_euler = Euler((0, 0, 0), 'XYZ')
        self.position = startpoint
        self.frames = KeyFrames()
        # self.inverted_static_mtx = None
        self.computed_d_matrices = {}
        self.computed_t_matrices = {}
        # self.scale_kf = {}  # keyframes (values)
        # self.scale_tkf = {}  # keyframes (tangents)
        # self.rotation_kf = {}
        # self.rotation_tkf = {}
        # self.position_kf = {}
        # self.position_tkf = {}
        # self.transform = mathutils.Matrix.Identity(4)  # what to do with that? it will be ultimately useless.

        self._parent = None
        self.children = []

        #  property business --------------------------------
        def _getname():
            return self._name
        def _setname(val):
            global instances
            if self._name is not None:
                del instances[self._name]
            if val is None and val in instances.keys():
                raise ValueError('name taken')
            self._name = val
            instances[val] = self
        def _delname():
            self.name = None
        self.name = property(_getname, _setname, _delname)

        def _getparent():
            return self._parent
        def _setparent(val):
            if isinstance(self.parent.fget(), Pseudobone) and (self in self.parent.fget().children):
                self.parent.fget().children.remove(self)
            self._parent = val
            if val is None or isinstance(val, Vector):
                return
            val.children.append(self)
        self.parent = property(_getparent, _setparent)

        def _setinchildren(holder, val):
            list.append(holder.children, val)
            val._parent = holder
        # self.children_append = (lambda self2, x: _setinchildren(self, x))

        if isinstance(frame, str):
            self.name.fset(frame)
        else:
            self.jnt_frame = frame
            self.name.fset(frame.name)
        self.parent.fset(parentBone)
        self.matrix = matrix

    # defines self.name, self.parent, self.children_append.

    def pre_delete(self):
        # call before losing variable to avoid memory leak
        self.parent.fset(None)
        for com in self.children:
            com.pre_delete()

    def _tree_to_array(self, dest):
        """inner function. do not call."""
        dest.append(self)
        for com in self.children:
            com._tree_to_array(dest)

    def tree_to_array(self):
        """returns a list of all bones"""
        ret = []
        self._tree_to_array(ret)
        return ret

    def reset(self):
        self.frames = KeyFrames()
        self.computed_d_matrices = {}
        self.computed_t_matrices = {}

    def get_z(self):
        if common.GLOBALS.no_rot_conversion:
            return rotation_part(self.matrix) @ Vector((0,0,1))
        else:
            return NtoB@rotation_part(self.matrix)@BtoN @ Vector((0,0,1))



def getBoneByName(name):
    global instances
    try:
        return instances[name]
    except KeyError:
        return None


def getvct(one, distance, tgt):
    """get the right keyframe handle vector"""  # XCX use me!
    # method one:
    return Vector((one, one*tgt))

finder = re.compile(r'''pose\.bones\[['"](\w*)['"]\]\.(\w*)''')
#used to determine what curves belong to what bones


def apply_animation(bones, arm_obj, jntframes, name=None):
    """apply keyframes from pseudobones to real, armature bones"""
    if name:
        arm_obj.animation_data.action = bpy.data.actions.new(name + '_action')
    else:
        arm_obj.animation_data.action = bpy.data.actions.new(arm_obj.name+'_action')

    # warning: here, the `name` var changes meaning

    for com in bones:
        name = com.name.fget()
        arm_obj.data.bones[name].use_inherit_scale = False  # scale can be applied
        posebone = arm_obj.pose.bones[name]
        if common.GLOBALS.no_rot_conversion:
            posebone.rotation_mode = "XYZ"
        else:    
            posebone.rotation_mode = "XZY"  # remember, coords are flipped
        # this keyframe is needed, overwritten anyways
        # also it is always at 1 because this function is called once per action
        posebone.keyframe_insert('location', frame=0)
        posebone.keyframe_insert('rotation_euler', frame=0)
        posebone.keyframe_insert('scale', frame=0)
    fcurves = arm_obj.animation_data.action.fcurves
    data = {}

    for curve in fcurves:
        # create data in dicts ({bonename:{datatype:[0,1,2]...}...})
        try:
            bonename, datatype = finder.match(curve.data_path).groups()
        except TypeError:  # cannit unpack None: this fsurve is not interesting
            continue
        bonedict = common.dict_get_set(data, bonename, {})
        datadict = common.dict_get_set(bonedict, datatype, [None, None, None])
        datadict[curve.array_index] = curve

    # create keyframes, with tengents
    for com in bones:
        name = com.name.fget()
        bonedict = data[name]
        posebone = arm_obj.pose.bones[name]
        posebone.keyframe_insert('location', frame=0)
        posebone.keyframe_insert('rotation_euler', frame=0)
        posebone.keyframe_insert('scale', frame=0)
        every_frame = list(com.frames.times.keys())
        every_frame.sort()
        refpos = com.jnt_frame
        if type(com.parent.fget()) is not Pseudobone:
            com.rotmatrix = Matrix.Identity(4)
            com.parentrot = Matrix.Identity(4)
        else:
            com.rotmatrix = com.parent.fget().rotmatrix
            com.parentrot = com.parent.fget().rotmatrix
        tempmat = Euler((refpos.rx, refpos.ry, refpos.rz), 'XYZ').to_matrix().to_4x4()
        com.rotmatrix @= tempmat
        cancel_ref_rot = tempmat.inverted()
        for frame in every_frame:
            # flip y and z when asked for
            if com.frames.times[frame][0]:
                vct, tgL, tgR = get_pos_vct(com, frame)
                if not common.GLOBALS.no_rot_conversion:
                    tgL.z, tgL.y = tgL.y, -tgL.z
                    tgR.z, tgR.y = tgR.y, -tgR.z
                    vct.z, vct.y = vct.y, -vct.z
                if not math.isnan(vct.x):
                    posebone.location[0] = vct.x
                    co = bonedict['location'][0].keyframe_points[-1].co
                    bonedict['location'][0].keyframe_points[-1].handle_left = co+Vector((-1, -tgL.x))
                    bonedict['location'][0].keyframe_points[-1].handle_right = co+Vector((1, tgR.x))
                    posebone.keyframe_insert('location', index=0, frame=frame)
                    # fixed: add frame to keyframes AFTER setting the right value to it. so conter-intuitive.
                if not math.isnan(vct.y):
                    posebone.location[1] = vct.y
                    co = bonedict['location'][1].keyframe_points[-1].co
                    bonedict['location'][1].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.y))
                    bonedict['location'][1].keyframe_points[-1].handle_right = co + Vector((1, tgR.y))
                    posebone.keyframe_insert('location', index=1, frame=frame)
                if not math.isnan(vct.z):
                    posebone.location[2] = vct.z
                    co = bonedict['location'][2].keyframe_points[-1].co
                    bonedict['location'][2].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.z))
                    bonedict['location'][2].keyframe_points[-1].handle_right = co + Vector((1, tgR.z))
                    posebone.keyframe_insert('location', index=2, frame=frame)

            if com.frames.times[frame][1]:
                vct, tgL, tgR = get_rot_vct(com, frame)
                if not common.GLOBALS.no_rot_conversion:
                    tgL.z, tgL.y = tgL.y, -tgL.z
                    tgR.z, tgR.y = tgR.y, -tgR.z
                    vct.z, vct.y = vct.y, -vct.z
                if not math.isnan(vct.x):
                    posebone.rotation_euler[0] = vct.x
                    co = bonedict['rotation_euler'][0].keyframe_points[-1].co
                    bonedict['rotation_euler'][0].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.x))
                    bonedict['rotation_euler'][0].keyframe_points[-1].handle_right = co + Vector((1, tgR.x))
                    posebone.keyframe_insert('rotation_euler', index=0, frame=frame)
                if not math.isnan(vct.y):
                    posebone.rotation_euler[1] = vct.y
                    co = bonedict['rotation_euler'][1].keyframe_points[-1].co
                    bonedict['rotation_euler'][1].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.y))
                    bonedict['rotation_euler'][1].keyframe_points[-1].handle_right = co + Vector((1, tgR.y))
                    posebone.keyframe_insert('rotation_euler', index=1, frame=frame)
                if not math.isnan(vct.z):
                    posebone.rotation_euler[2] = vct.z
                    co = bonedict['rotation_euler'][2].keyframe_points[-1].co
                    bonedict['rotation_euler'][2].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.z))
                    bonedict['rotation_euler'][2].keyframe_points[-1].handle_right = co + Vector((1, tgR.z))
                    posebone.keyframe_insert('rotation_euler', index=2, frame=frame)

            if com.frames.times[frame][2]:
                vct, tgL, tgR = get_sc_vct(com, frame)
                if not common.GLOBALS.no_rot_conversion:
                    tgL.z, tgL.y = tgL.y, tgL.z
                    tgR.z, tgR.y = tgR.y, tgR.z
                    vct.z, vct.y = vct.y, vct.z
                if not math.isnan(vct.x):
                    posebone.scale[0] = vct.x
                    co = bonedict['scale'][0].keyframe_points[-1].co
                    bonedict['scale'][0].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.x))
                    bonedict['scale'][0].keyframe_points[-1].handle_right = co + Vector((1, tgR.x))
                    posebone.keyframe_insert('scale', index=0, frame=frame)
                if not math.isnan(vct.y):
                    posebone.scale[1] = vct.y
                    co = bonedict['scale'][1].keyframe_points[-1].co
                    bonedict['scale'][1].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.y))
                    bonedict['scale'][1].keyframe_points[-1].handle_right = co + Vector((1, tgR.y))
                    posebone.keyframe_insert('scale', index=1, frame=frame)
                if not math.isnan(vct.z):
                    posebone.scale[2] = vct.z
                    co = bonedict['scale'][2].keyframe_points[-1].co
                    bonedict['scale'][2].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.z))
                    bonedict['scale'][2].keyframe_points[-1].handle_right = co + Vector((1, tgR.z))
                    posebone.keyframe_insert('scale', index=2, frame=frame)

    return arm_obj.animation_data.action
