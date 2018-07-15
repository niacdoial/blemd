from mathutils import Vector, Euler, Matrix
import bpy
import math
import re
from .maxheader import dict_get_set
# import weakref
import logging
log = logging.getLogger('bpy.ops.import_mesh.bmd.pseudobones')

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
    tempv = vect
    tempv.x /= length
    tempv.y /= length
    tempv.z /= length
    return tempv


def cubic_interpolator(t1, y1, d1, t2, y2, d2, t):
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

    return ya+yb+yc+yd, (da+db+dc+dd)/(t2-t1)


def get_total_mtx(p_bone, frame):
    if not isinstance(p_bone, Pseudobone):
        return Matrix.Identity(4), Matrix.Identity(4)
    if frame not in p_bone.computed_t_matrices.keys():
        parent_tot_mtx = get_total_mtx(p_bone.parent.fget(), frame)
        local_t_mtx = p_bone.frames.get_mtx(frame)
        p_bone.computed_t_matrices[frame] = (parent_tot_mtx[0] * local_t_mtx[0],
                                             parent_tot_mtx[1] * local_t_mtx[1])
    return p_bone.computed_t_matrices[frame]


def get_dynamic_mtx(p_bone, frame):
    # for a (n+1)-th generation dynamic matrix in the tree (Dmat_{n+1})
    # we have Dmat_{n+1} = inverted(Smat_{n+1} * Product(k from 1 to n)(Dmat_{k}))) * Tmat_{n+1}
    if frame not in p_bone.computed_d_matrices.keys():
        solo_mtx_y = p_bone.inverted_static_mtx * get_total_mtx(p_bone, frame)[0]
        solo_mtx_yd = p_bone.inverted_static_mtx * get_total_mtx(p_bone, frame)[1]
        temp_bone = p_bone.parent.fget()
        ancestor_mtx_y = Matrix.Identity(4)
        ancestor_mtx_yd = Matrix.Identity(4)
        while isinstance(temp_bone, Pseudobone):
            ancestor_mtx_y = get_dynamic_mtx(temp_bone, frame)[0] * ancestor_mtx_y
            ancestor_mtx_yd = get_dynamic_mtx(temp_bone, frame)[1] * ancestor_mtx_yd
            temp_bone = temp_bone.parent.fget()
        p_bone.computed_d_matrices[frame] = (ancestor_mtx_y.inverted() * solo_mtx_y,
                                             ancestor_mtx_yd.inverted() * solo_mtx_yd)
    return p_bone.computed_d_matrices[frame]


def get_pos_vct(p_bone, frame):
    EPSILON = 1E-4
    y, yd = get_dynamic_mtx(p_bone, frame)
    y = y.to_translation()
    yd = yd.to_translation()
    # yd = get_dynamic_mtx(p_bone, frame+EPSILON).position()
    d = (yd-y)/EPSILON
    return y, d


def get_rot_vct(p_bone, frame):
    EPSILON = 1E-4
    y, yd = get_dynamic_mtx(p_bone, frame)
    y = y.to_euler('XYZ')
    yd = yd.to_euler('XYZ')
    # yd = get_dynamic_mtx(p_bone, frame+EPSILON).rotation()
    d = product(1/EPSILON, subtract2(yd, y))
    return y, d


def matrix_calibrate_r(y, d, mat, parent, bone):
    """transforms "absolute" rotation coordinates into"relative" ones, using the default pose rotation matrix"""
    # note: using GC coordinate organization: therefor rotations are in XYZ order

    # ## first cancel local default pose
    EPSILON = 1/100


    # ret_y = (parent*y.to_matrix().to_4x4()*mat).to_euler('XYZ')  # computing rotation value
    ret_y = (y.to_matrix().to_4x4()*mat).to_euler('XYZ')  # computing rotation value

    # computes rotation tangents by definition of derivative
    # (and now, the incredibly complex equivalent of "dy = EPSILON*d + y":
    dy = Euler((0,0,0), "XYZ")
    dy.x = EPSILON * d.x + y.x
    dy.y = EPSILON * d.y + y.y
    dy.z = EPSILON * d.z + y.z

    ret_dy = (parent*dy.to_matrix().to_4x4()*mat).to_euler('XYZ')
    ret_d = Euler((0,0,0), 'XYZ')
    ret_d.x = (ret_dy.x - ret_y.x) / EPSILON
    ret_d.y = (ret_dy.y - ret_y.y) / EPSILON
    ret_d.z = (ret_dy.z - ret_y.z) / EPSILON

    # return y, d

    y, d = ret_y, ret_d  # "apply" transformation

    # ## then add parent rotations?

    if hasattr(bone, 'parent_rot_matrix'):  # sililar to calibrate_t, need to transform the original vector
        parent_rot_matrix = bone.parent_rot_matrix
    else:
        if type(bone.parent.fget()) == Pseudobone:
            parent_rot_matrix = (bone.parent.fget().jnt_frame.incr_matrix.
                                    to_quaternion().to_matrix().to_4x4())
        else:
            parent_rot_matrix = Matrix.Identity(4)
        bone.parent_rot_matrix = parent_rot_matrix

    # final modifications:
    # (y, d) represent bone rotation, relative to default, but assuming bone is in "collapsed"
    # pose compared to parent (bmd_y); with parent rotation __already__ applied (no need to do it here).
    # blender needs translation from default pose (bl_y) __without__ parent default rotation applied _previously_:
    # it needs to be applied __here__
    # therefor, with parent bone default rotation (from collapsed position) (par_rot);
    # we have par_rot * bmd_y = bl_y. We need bl_y.

    ret_y = Euler((parent_rot_matrix * Vector(y)), 'XYZ')  # XCX how the *heck* is this the right move?
    # ret_y = (parent_rot_matrix * y.to_matrix().to_4x4()).to_euler('XYZ')

    # dy = Vector((0, 0, 0))
    dy.x = EPSILON * d.x + y.x
    dy.y = EPSILON * d.y + y.y
    dy.z = EPSILON * d.z + y.z
    dy = Euler((parent_rot_matrix * Vector(dy)), 'XYZ')
    # dy = (parent_rot_matrix * dy.to_matrix().to_4x4()).to_euler('XYZ')
    # d = Euler((0, 0, 0), 'XYZ')
    d.x = (dy.x - y.x) / EPSILON
    d.y = (dy.y - y.y) / EPSILON
    d.z = (dy.z - y.z) / EPSILON

    return ret_y, d  # y had to be stored into a temp variable, not d


def matrix_calibrate_t(y, d, parent, bone):

    # ## cancel default pose first
    EPSILON = 1 / 100

    y.x -= bone.jnt_frame.t.x
    # d.x -= bone.jnt_frame.t.x  # adding constants doesn't change derivative, dummy!
    y.y -= bone.jnt_frame.t.y
    # d.y -= bone.jnt_frame.t.y
    y.z -= bone.jnt_frame.t.z
    # d.z -= bone.jnt_frame.t.z


    # ## then add inherited rotations

    # getting parent bone default rotation (accoriding to BMD file; in matrix form)
    if hasattr(bone, 'parent_rot_matrix'):
        parent_rot_matrix = bone.parent_rot_matrix
    else:
        if type(bone.parent.fget()) == Pseudobone:
            parent_rot_matrix = (bone.parent.fget().jnt_frame.incr_matrix.
                                 to_quaternion().to_matrix().to_4x4())
        else:
            parent_rot_matrix = Matrix.Identity(4)
        bone.parent_rot_matrix = parent_rot_matrix

    # final modifications:
    # (y, d) represent bone translation, relative to default, but assuming bone is in "collapsed"
    # pose compared to parent (bmd_y); with parent rotation __already__ applied (no need to do it here).

    # blender needs translation from default pose (bl_y) __without__ parent default rotation applied _previously_:
    # it needs to be applied __here__

    # therefor, with parent bone default rotation (from collapsed position) (par_rot);
    # we have par_rot * bmd_y = bl_y. We need bl_y.

    y = parent_rot_matrix * y

    dy = Vector((0, 0, 0))
    dy.x = EPSILON * d.x + y.x
    dy.y = EPSILON * d.y + y.y
    dy.z = EPSILON * d.z + y.z
    dy = parent_rot_matrix * dy
    d = Vector((0, 0, 0))
    d.x = (dy.x - y.x) / EPSILON
    d.y = (dy.y - y.y) / EPSILON
    d.z = (dy.z - y.z) / EPSILON

    return y, d


def matrix_calibrate_s(y, d, parent, bone):

    # ## first cancel local default pose
    EPSILON = 1 / 100

    y.x /= bone.jnt_frame.sx
    y.y /= bone.jnt_frame.sy
    y.z /= bone.jnt_frame.sz

    d.x /= bone.jnt_frame.sx
    d.y /= bone.jnt_frame.sy
    d.z /= bone.jnt_frame.sz

    return y, d
    # note: scaling happens "inside" rotation, and does not require rotation calibration

    # ## then add inherited rotations

    # getting parent bone default rotation (accoriding to BMD file; in matrix form)
    if hasattr(bone, 'parent_rot_matrix'):
        parent_rot_matrix = bone.parent_rot_matrix
    else:
        if type(bone.parent.fget()) == Pseudobone:
            parent_rot_matrix = (bone.parent.fget().jnt_frame.incr_matrix.
                                    to_quaternion().to_matrix().to_4x4())
        else:
            parent_rot_matrix = Matrix.Identity(4)
        bone.parent_rot_matrix = parent_rot_matrix

    y = parent_rot_matrix * y

    dy = Vector((0, 0, 0))
    dy.x = EPSILON * d.x + y.x
    dy.y = EPSILON * d.y + y.y
    dy.z = EPSILON * d.z + y.z
    dy = parent_rot_matrix * dy
    d = Vector((0, 0, 0))
    d.x = (dy.x - y.x) / EPSILON
    d.y = (dy.y - y.y) / EPSILON
    d.z = (dy.z - y.z) / EPSILON

    return y, d


instances = {}


class KeyFrames:
    def __init__(self):
        self.times = {}
        self.positions = [{}, {}, {}]
        self.rotations = [{}, {}, {}]
        self.scales = [{}, {}, {}]

    def feed_anim(self, anim, include_sc=True, fr_sc=1, fr_of=0):
        for key in anim.translationsX:
            self.positions[0][fr_sc*key.time+fr_of] = (key.value, key.tangent)
            dict_get_set(self.times, fr_sc*key.time+fr_of, [False, False, False])[0] = True
        for key in anim.translationsY:
            self.positions[1][fr_sc*key.time+fr_of] = (key.value, key.tangent)
            dict_get_set(self.times, fr_sc*key.time+fr_of, [False, False, False])[0] = True
        for key in anim.translationsZ:
            self.positions[2][fr_sc*key.time+fr_of] = (key.value, key.tangent)
            dict_get_set(self.times, fr_sc*key.time+fr_of, [False, False, False])[0] = True

        for key in anim.rotationsX:
            self.rotations[0][fr_sc*key.time+fr_of] = (key.value, key.tangent)
            dict_get_set(self.times, fr_sc*key.time+fr_of, [False, False, False])[1] = True
        for key in anim.rotationsY:
            self.rotations[1][fr_sc*key.time+fr_of] = (key.value, key.tangent)
            dict_get_set(self.times, fr_sc*key.time+fr_of, [False, False, False])[1] = True
        for key in anim.rotationsZ:
            self.rotations[2][fr_sc*key.time+fr_of] = (key.value, key.tangent)
            dict_get_set(self.times, fr_sc*key.time+fr_of, [False, False, False])[1] = True
        if include_sc:
            for key in anim.scalesX:
                self.scales[0][fr_sc*key.time+fr_of] = (key.value, key.tangent)
                dict_get_set(self.times, fr_sc*key.time+fr_of, [False, False, False])[2] = True
            for key in anim.scalesY:
                self.scales[1][fr_sc*key.time+fr_of] = (key.value, key.tangent)
                dict_get_set(self.times, fr_sc*key.time+fr_of, [False, False, False])[2] = True
            for key in anim.scalesZ:
                self.scales[2][fr_sc*key.time+fr_of] = (key.value, key.tangent)
                dict_get_set(self.times, fr_sc*key.time+fr_of, [False, False, False])[2] = True

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

        return cubic_interpolator(prev_t, data[prev_t][0], data[prev_t][1],
                                  next_t, data[next_t][0], data[next_t][1], time)

    def get_pos(self, time):
        temp_x = self._get_vt(self.positions[0], time)
        temp_y = self._get_vt(self.positions[1], time)
        temp_z = self._get_vt(self.positions[2], time)
        return (Vector((temp_x[0], temp_y[0], temp_z[0])),
                Vector((temp_x[1], temp_y[1], temp_z[1])))

    def get_rot(self, time):
        temp_x = self._get_vt(self.rotations[0], time)
        temp_y = self._get_vt(self.rotations[1], time)
        temp_z = self._get_vt(self.rotations[2], time)
        return (Euler((temp_x[0], temp_y[0], temp_z[0]), 'XYZ'),
                Euler((temp_x[1], temp_y[1], temp_z[1]), 'XYZ'))

    def get_sc(self, time):
        temp_x = self._get_vt(self.scales[0], time)
        temp_y = self._get_vt(self.scales[1], time)
        temp_z = self._get_vt(self.scales[2], time)
        return (Vector((temp_x[0], temp_y[0], temp_z[0])),
                Vector((temp_x[1], temp_y[1], temp_z[1])))

    def get_mtx(self, time):
        EPSILON = 1E-4
        vct_y, vct_d = self.get_pos(time)
        rot_y, rot_d = self.get_rot(time)
        vct_yd = sum2(vct_y, product(EPSILON, vct_d))
        rot_yd = sum2(rot_y, product(EPSILON, rot_d))
        return ( (Matrix.Translation(vct_y) * rot_y.to_matrix().to_4x4()),
                 (Matrix.Translation(vct_yd) * rot_yd.to_matrix().to_4x4()) )


class Pseudobone:
    def __init__(self, parentBone, frame, matrix, startpoint, endpoint, roll):

        self._name = None
        ori = endpoint - startpoint
        self.endpoint = endpoint
        self.length = math.sqrt(ori.x**2 + ori.y**2 + ori.z**2)
        self.orientation = vect_normalize(ori)
        self.roll = roll
        self.scale = Vector((1, 1, 1))
        self.jnt_frame = None
        self.rotation_euler = Euler((0, 0, 0), 'XYZ')
        self.position = startpoint
        self.frames = KeyFrames()
        self.inverted_static_mtx = None
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
        arm_obj.animation_data.action = bpy.data.actions.new(arm_obj.name + '_' + name)
    else:
        arm_obj.animation_data.action = bpy.data.actions.new(arm_obj.name+'_action')
    bpy.context.scene.frame_current = 0

    # warning: here, the `name` var changes meaning

    for com in bones:
        name = com.name.fget()
        arm_obj.data.bones[name].use_inherit_scale = False  # scale can be applied
        posebone = arm_obj.pose.bones[name]
        posebone.rotation_mode = "XZY"  # remember, coords are flipped
        bpy.context.scene.frame_current = 0
        # this keyframe is needed, overwritten anyways
        # also it is always at 1 because this function is called once per action
        posebone.keyframe_insert('location')
        posebone.keyframe_insert('rotation_euler')
        posebone.keyframe_insert('scale')
    fcurves = arm_obj.animation_data.action.fcurves
    data = {}

    for curve in fcurves:
        # create data in dicts ({bonename:{datatype:[0,1,2]...}...})
        bonename, datatype = finder.match(curve.data_path).groups()
        data[bonename] = bonedict = data.get(bonename, {})
        bonedict[datatype] = datadict = bonedict.get(datatype, [None, None, None])
        datadict[curve.array_index] = curve

    # create keyframes, with tengents
    for com in bones:
        name = com.name.fget()
        bonedict = data[name]
        posebone = arm_obj.pose.bones[name]
        bpy.context.scene.frame_current = 0
        posebone.keyframe_insert('location')
        posebone.keyframe_insert('rotation_euler')
        posebone.keyframe_insert('scale')
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
        com.rotmatrix *= tempmat
        cancel_ref_rot = tempmat.inverted()
        for frame in every_frame:
            bpy.context.scene.frame_current = frame
            # flip y and z
            if com.frames.times[frame][0]:
                vct, tgt = com.frames.get_pos(frame)
                vct, tgt = matrix_calibrate_t(vct, tgt, com.parentrot, com)
                # vct, tgt = get_pos_vct(com, frame)
                if not math.isnan(vct.x):
                    # remember: in JNT, bone coordinates are relative to their parents, not in blender
                    # (the animation data must be corrected by the relative bone position only)
                    posebone.location[0] = vct.x
                    co = bonedict['location'][0].keyframe_points[-1].co
                    bonedict['location'][0].keyframe_points[-1].handle_left = co+Vector((-1, -tgt.x))
                    bonedict['location'][0].keyframe_points[-1].handle_right = co+Vector((1, tgt.x))
                    posebone.keyframe_insert('location', 0)
                    # fixed: add frame to keyframes AFTER setting the right value to it. so conter-intuitive.
                if not math.isnan(vct.z):
                    posebone.location[1] = -vct.z
                    co = bonedict['location'][1].keyframe_points[-1].co
                    bonedict['location'][1].keyframe_points[-1].handle_left = co + Vector((-1, tgt.z))
                    bonedict['location'][1].keyframe_points[-1].handle_right = co + Vector((1, -tgt.z))
                    posebone.keyframe_insert('location', 1)
                if not math.isnan(vct.y):
                    posebone.location[2] = vct.y
                    co = bonedict['location'][2].keyframe_points[-1].co
                    bonedict['location'][2].keyframe_points[-1].handle_left = co + Vector((-1, -tgt.y))
                    bonedict['location'][2].keyframe_points[-1].handle_right = co + Vector((1, tgt.y))
                    posebone.keyframe_insert('location', 2)

            if com.frames.times[frame][1]:
                vct, tgt = com.frames.get_rot(frame)
                vct, tgt = matrix_calibrate_r(vct, tgt, cancel_ref_rot, com.parentrot, com)
                # vct, tgt = get_rot_vct(com, frame)
                if not math.isnan(vct.x):
                    posebone.rotation_euler[0] = vct.x
                    co = bonedict['rotation_euler'][0].keyframe_points[-1].co
                    bonedict['rotation_euler'][0].keyframe_points[-1].handle_left = co + Vector((-1, -tgt.x))
                    bonedict['rotation_euler'][0].keyframe_points[-1].handle_right = co + Vector((1, tgt.x))
                    posebone.keyframe_insert('rotation_euler', 0)
                if not math.isnan(vct.z):
                    posebone.rotation_euler[1] = -vct.z
                    co = bonedict['rotation_euler'][1].keyframe_points[-1].co
                    bonedict['rotation_euler'][1].keyframe_points[-1].handle_left = co + Vector((-1, tgt.z))
                    bonedict['rotation_euler'][1].keyframe_points[-1].handle_right = co + Vector((1, -tgt.z))
                    posebone.keyframe_insert('rotation_euler', 1)
                if not math.isnan(vct.y):
                    posebone.rotation_euler[2] = vct.y
                    co = bonedict['rotation_euler'][2].keyframe_points[-1].co
                    bonedict['rotation_euler'][2].keyframe_points[-1].handle_left = co + Vector((-1, -tgt.y))
                    bonedict['rotation_euler'][2].keyframe_points[-1].handle_right = co + Vector((1, tgt.y))
                    posebone.keyframe_insert('rotation_euler', 2)

            if com.frames.times[frame][2]:
                vct, tgt = com.frames.get_sc(frame)
                vct, tgt = matrix_calibrate_s(vct, tgt, com.parentrot, com)
                if not math.isnan(vct.x):
                    posebone.scale[0] = vct.x
                    co = bonedict['scale'][0].keyframe_points[-1].co
                    bonedict['scale'][0].keyframe_points[-1].handle_left = co + Vector((-1, -tgt.x))
                    bonedict['scale'][0].keyframe_points[-1].handle_right = co + Vector((1, tgt.x))
                    posebone.keyframe_insert('scale', 0)
                if not math.isnan(vct.z):
                    posebone.scale[1] = vct.z
                    co = bonedict['scale'][1].keyframe_points[-1].co
                    bonedict['scale'][1].keyframe_points[-1].handle_left = co + Vector((-1, tgt.z))
                    bonedict['scale'][1].keyframe_points[-1].handle_right = co + Vector((1, -tgt.z))
                    posebone.keyframe_insert('scale', 1)
                if not math.isnan(vct.y):
                    posebone.scale[2] = vct.y
                    co = bonedict['scale'][2].keyframe_points[-1].co
                    bonedict['scale'][2].keyframe_points[-1].handle_left = co + Vector((-1, -tgt.y))
                    bonedict['scale'][2].keyframe_points[-1].handle_right = co + Vector((1, tgt.y))
                    posebone.keyframe_insert('scale', 2)

    return arm_obj.animation_data.action
