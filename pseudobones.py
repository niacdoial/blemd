from mathutils import Vector, Euler, Matrix
import bpy
import math
import re
from time import sleep
from collections import OrderedDict as ODict

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

EPSILON = 1E-4

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


def get_pos_vct(p_bone, frame):
    if p_bone.inverted_static_rotmtx is None:
        p_bone.inverted_static_rotmtx = p_bone.jnt_frame.getInvRotMatrix()
    y, dL, dR = p_bone.frames.get_pos(frame)
    y -= p_bone.jnt_frame.t
    return (
        p_bone.inverted_static_rotmtx @ y,
        p_bone.inverted_static_rotmtx @ dL,
        p_bone.inverted_static_rotmtx @ dR,
    )

def get_rot_vct(p_bone, frame):
    global EPSILON
    if p_bone.inverted_static_rotmtx is None:
        p_bone.inverted_static_rotmtx = p_bone.jnt_frame.getInvRotMatrix()

    y, dL, dR = p_bone.frames.get_rot(frame)
    ydL = sum2(y, product(EPSILON, dL))
    ydR = sum2(y, product(EPSILON, dR))

    y.rotate(p_bone.inverted_static_rotmtx.to_quaternion())
    ydL.rotate(p_bone.inverted_static_rotmtx.to_quaternion())
    ydR.rotate(p_bone.inverted_static_rotmtx.to_quaternion())

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
        self.positions = [ODict(), ODict(), ODict()]
        self.rotations = [ODict(), ODict(), ODict()]
        self.scales = [ODict(), ODict(), ODict()]

    def feed_anim(self, anim, include_sc=True, fr_sc=1, fr_of=0):

        all_collections = [  # all collections of keyframes, each animating a single value
                (self.positions[0], anim.translationsX, 0),
                (self.positions[1], anim.translationsY, 0),
                (self.positions[2],anim.translationsZ, 0),
                (self.rotations[0],anim.rotationsX, 1),
                (self.rotations[1],anim.rotationsY, 1),
                (self.rotations[2],anim.rotationsZ, 1),
        ]
        if include_sc:
            all_collections += [
                (self.scales[0], anim.scalesX, 2),
                (self.scales[1], anim.scalesY, 2),
                (self.scales[2], anim.scalesZ, 2),
            ]
        for dest_collection, src_collection, flag_index in all_collections:
            for key in src_collection:
                frame_time = int(fr_sc*key.time+fr_of)
                dest_collection[frame_time] = (key.value, key.tangentL, key.tangentR)
                dict_get_set(self.times, frame_time, [False, False, False])[flag_index] = True

        # add last frame on everything (to avoid crashes), but not register them as 'real'
        anim_length = max(self.times.keys())  # XXX is that animation length  even correct?
        for dest_collection, _, _ in all_collections:
            max_time = max(dest_collection.keys())
            if max_time < anim_length:
                dest_collection[anim_length] = dest_collection[max_time]

        # compute the distance (in time) between keyframes.
        # for dest_collection, _, _ in all_collections:
        #     local_times = list(dest_collection.keys())
        #     #local_times.sort()  # XXX let's hope it's not needed. if it is, we have bigger problems on our hands.
        #     lh_distances = [1]*len(local_times)
        #     for i in range(1,len(local_times)):
        #         lh_distances[i] = local_times[i] - local_times[i-1]
        #     rh_distances = lh_distances[1:] + [2]

        #     for frame_i, time in enumerate(local_times):
        #         y,dL,dR = dest_collection[time]:
        #         tL = lh_distances[frame_i]
        #         tR = rh_distances[frame_i]
        #         dest_collection[time] = (y,dL,dR, tL,tR)
            

    @staticmethod
    def _get_vt(data, time):
        """for a given array containing animation keyframes, return three values describing the animation at a given time:
        the value itself, its lefthand tangent, and its righthand tangent.
        """
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

        return cubic_interpolator(
            prev_t, data[prev_t][0], data[prev_t][2],
            next_t, data[next_t][0], data[next_t][1],
            time
        )

    def get_pos(self, time):
        """Return the (possibly interpolated) translation value for a given time, through the animation data stored in this object:
        give the translation value itself, its lefthand tangent, and its righthand tangent.
        """
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
        self.inverted_static_rotmtx = None
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


finder = re.compile(r'''pose\.bones\[['"](\w*)['"]\]\.(\w*)''')
#used to determine what curves belong to what bones


def apply_animation(bones, arm_obj, jntframes, name=None):
    """apply keyframes from pseudobones to real, armature bones"""
    if name:
        arm_obj.animation_data.action = bpy.data.actions.new(arm_obj.name + '_' + name)
    else:
        arm_obj.animation_data.action = bpy.data.actions.new(arm_obj.name+'_.unnamed')

    # warning: here, the `name` var changes meaning

    all_curves = {}
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

        bonecurves = {'location': [None,None,None], 'rotation_euler':[None,None,None], 'scale': [None,None,None]}
        all_curves[name] = bonecurves

        for datatype in ('location', 'rotation_euler', 'scale'):
            data_path = f'pose.bones["{name:s}"].{datatype:s}'
            for array_index in (0,1,2):
                curve = arm_obj.animation_data.action.fcurves.find(data_path, index = array_index)
                if curve is None:
                    curve = arm_obj.animation_data.action.fcurves.new(data_path, index = array_index)
                curve.auto_smoothing = 'NONE'
                curve.update()
                all_curves[name][datatype][array_index] = curve

    # create keyframes, with tengents
    for com in bones:
        name = com.name.fget()
        bonecurves = all_curves[name]
        posebone = arm_obj.pose.bones[name]
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
                    co = Vector((frame, vct.x))
                    bonecurves['location'][0].keyframe_points.insert(frame, vct.x, options={'FAST'})
                    bonecurves['location'][0].keyframe_points[-1].handle_left_type = 'FREE'
                    bonecurves['location'][0].keyframe_points[-1].handle_right_type = 'FREE'
                    bonecurves['location'][0].keyframe_points[-1].handle_left = co+Vector((-1, -tgL.x))
                    bonecurves['location'][0].keyframe_points[-1].handle_right = co+Vector((1, tgR.x))
                    bonecurves['location'][0].update()
                if not math.isnan(vct.y):
                    co = Vector((frame, vct.y))
                    bonecurves['location'][1].keyframe_points.insert(frame, vct.y, options={'FAST'})
                    bonecurves['location'][1].keyframe_points[-1].handle_left_type = 'FREE'
                    bonecurves['location'][1].keyframe_points[-1].handle_right_type = 'FREE'
                    bonecurves['location'][1].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.y))
                    bonecurves['location'][1].keyframe_points[-1].handle_right = co + Vector((1, tgR.y))
                    bonecurves['location'][1].update()
                if not math.isnan(vct.z):
                    co = Vector((frame, vct.z))
                    bonecurves['location'][2].keyframe_points.insert(frame, vct.z, options={'FAST'})
                    bonecurves['location'][2].keyframe_points[-1].handle_left_type = 'FREE'
                    bonecurves['location'][2].keyframe_points[-1].handle_right_type = 'FREE'
                    bonecurves['location'][2].update()
                    bonecurves['location'][2].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.z))
                    bonecurves['location'][2].keyframe_points[-1].handle_right = co + Vector((1, tgR.z))

            if com.frames.times[frame][1]:
                vct, tgL, tgR = get_rot_vct(com, frame)
                if not common.GLOBALS.no_rot_conversion:
                    tgL.z, tgL.y = tgL.y, -tgL.z
                    tgR.z, tgR.y = tgR.y, -tgR.z
                    vct.z, vct.y = vct.y, -vct.z
                if not math.isnan(vct.x):
                    co = Vector((frame, vct.x))
                    bonecurves['rotation_euler'][0].keyframe_points.insert(frame, vct.x, options={'FAST'})
                    bonecurves['rotation_euler'][0].keyframe_points[-1].handle_left_type = 'FREE'
                    bonecurves['rotation_euler'][0].keyframe_points[-1].handle_right_type = 'FREE'
                    bonecurves['rotation_euler'][0].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.x))
                    bonecurves['rotation_euler'][0].keyframe_points[-1].handle_right = co + Vector((1, tgR.x))
                if not math.isnan(vct.y):
                    co = Vector((frame, vct.y))
                    bonecurves['rotation_euler'][1].keyframe_points.insert(frame, vct.y, options={'FAST'})
                    bonecurves['rotation_euler'][1].keyframe_points[-1].handle_left_type = 'FREE'
                    bonecurves['rotation_euler'][1].keyframe_points[-1].handle_right_type = 'FREE'
                    bonecurves['rotation_euler'][1].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.y))
                    bonecurves['rotation_euler'][1].keyframe_points[-1].handle_right = co + Vector((1, tgR.y))
                if not math.isnan(vct.z):
                    co = Vector((frame, vct.z))
                    bonecurves['rotation_euler'][2].keyframe_points.insert(frame, vct.z, options={'FAST'})
                    bonecurves['rotation_euler'][2].keyframe_points[-1].handle_left_type = 'FREE'
                    bonecurves['rotation_euler'][2].keyframe_points[-1].handle_right_type = 'FREE'
                    bonecurves['rotation_euler'][2].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.z))
                    bonecurves['rotation_euler'][2].keyframe_points[-1].handle_right = co + Vector((1, tgR.z))

            if com.frames.times[frame][2]:
                vct, tgL, tgR = get_sc_vct(com, frame)
                if not common.GLOBALS.no_rot_conversion:
                    tgL.z, tgL.y = tgL.y, tgL.z
                    tgR.z, tgR.y = tgR.y, tgR.z
                    vct.z, vct.y = vct.y, vct.z
                if not math.isnan(vct.x):
                    co = Vector((frame, vct.x))
                    bonecurves['scale'][0].keyframe_points.insert(frame, vct.x, options={'FAST'})
                    bonecurves['scale'][0].keyframe_points[-1].handle_left_type = 'FREE'
                    bonecurves['scale'][0].keyframe_points[-1].handle_right_type = 'FREE'
                    bonecurves['scale'][0].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.x))
                    bonecurves['scale'][0].keyframe_points[-1].handle_right = co + Vector((1, tgR.x))
                if not math.isnan(vct.y):
                    co = Vector((frame, vct.y))
                    bonecurves['scale'][1].keyframe_points.insert(frame, vct.y, options={'FAST'})
                    bonecurves['scale'][1].keyframe_points[-1].handle_left_type = 'FREE'
                    bonecurves['scale'][1].keyframe_points[-1].handle_right_type = 'FREE'
                    bonecurves['scale'][1].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.y))
                    bonecurves['scale'][1].keyframe_points[-1].handle_right = co + Vector((1, tgR.y))
                if not math.isnan(vct.z):
                    co = Vector((frame, vct.z))
                    bonecurves['scale'][2].keyframe_points.insert(frame, vct.z, options={'FAST'})
                    bonecurves['scale'][2].keyframe_points[-1].handle_left_type = 'FREE'
                    bonecurves['scale'][2].keyframe_points[-1].handle_right_type = 'FREE'
                    bonecurves['scale'][2].keyframe_points[-1].handle_left = co + Vector((-1, -tgL.z))
                    bonecurves['scale'][2].keyframe_points[-1].handle_right = co + Vector((1, tgR.z))


        # now, re-adjust the interpolation
        for fcurve in [
                bonecurves['location'][0],
                bonecurves['location'][1],
                bonecurves['location'][2],
                bonecurves['rotation_euler'][0],
                bonecurves['rotation_euler'][1],
                bonecurves['rotation_euler'][2],
                bonecurves['scale'][0],
                bonecurves['scale'][1],
                bonecurves['scale'][2],
        ]:
            if fcurve is None:
                continue
            for i_kf, kf in enumerate(fcurve.keyframe_points):
                if i_kf == 0:
                    left_time = 1
                else:
                    left_time = (kf.co[0] - fcurve.keyframe_points[i_kf-1].co[0]) /3
                kf.handle_left = kf.co + Vector((-left_time, left_time*(kf.handle_left - kf.co)[1] ))
                if i_kf+1 == len(fcurve.keyframe_points):
                    right_time = 1
                else:
                    right_time = (fcurve.keyframe_points[i_kf+1].co[0] - kf.co[0]) /3
                kf.handle_right = kf.co + Vector((right_time, right_time*(kf.handle_right - kf.co)[1] ))

    return arm_obj.animation_data.action
