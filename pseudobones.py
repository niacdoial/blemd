import mathutils
from mathutils import Vector, Euler, Matrix
import bpy
import math
import re


def vect_normalize(vect):
    length = math.sqrt(vect.x**2 + vect.y**2 + vect.z**2)
    tempv = vect
    tempv.x /= length
    tempv.y /= length
    tempv.z /= length
    return tempv


def cubic_interpolator(t1, y1, d1, t2, y2, d2, t):
    tn = (t-t1)/(t2-t1)  # normalized time coordinate

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


def matrix_calibrate_r(y, d, mat, parent, bone):
    """transforms "absolute" rotation coordinates into"relative" ones, using the default pose rotation matrix"""
    # note: using GC coordinate organization: therefor rotations are in XYZ order

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

    y,d = ret_y, ret_d

    if hasattr(bone, 'parent_rot_matrix'):  # sililar to calibrate_t, need to transform the original vector
        parent_rot_matrix = bone.parent_rot_matrix
    else:
        if type(bone.parent.fget()) == Pseudobone:
            parent_rot_matrix = bone.parent.fget().jnt_frame.incr_matrix.to_quaternion().to_matrix().to_4x4()
        else:
            parent_rot_matrix = Matrix.Identity(4)
        bone.parent_rot_matrix = parent_rot_matrix
    y = Euler((parent_rot_matrix * Vector(y)), 'XYZ')

    dy = Vector((0, 0, 0))
    dy.x = EPSILON * d.x + y.x
    dy.y = EPSILON * d.y + y.y
    dy.z = EPSILON * d.z + y.z
    dy = parent_rot_matrix * dy
    d = Euler((0, 0, 0), 'XYZ')
    d.x = (dy.x - y.x) / EPSILON
    d.y = (dy.y - y.y) / EPSILON
    d.z = (dy.z - y.z) / EPSILON

    return y, d


def matrix_calibrate_t(y, d, parent, bone):
    EPSILON = 1 / 100

    y.x -= bone.jnt_frame.t.x
    d.x -= bone.jnt_frame.t.x
    y.y -= bone.jnt_frame.t.y
    d.y -= bone.jnt_frame.t.y
    y.z -= bone.jnt_frame.t.z
    d.z -= bone.jnt_frame.t.z

    if hasattr(bone, 'parent_rot_matrix'):
        parent_rot_matrix = bone.parent_rot_matrix
    else:
        if type(bone.parent.fget()) == Pseudobone:
            parent_rot_matrix = bone.parent.fget().jnt_frame.incr_matrix.to_quaternion().to_matrix().to_4x4()
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

    ret_y = (parent * Matrix.Translation(y)).to_translation()  # computing rotation value

    # computes rotation tangents by definition of derivative
    # (and now, the incredibly complex equivalent of "dy = EPSILON*d + y":
    dy = Vector((0, 0, 0))
    dy.x = EPSILON * d.x + y.x
    dy.y = EPSILON * d.y + y.y
    dy.z = EPSILON * d.z + y.z
    ret_dy = (parent * Matrix.Translation(dy)).to_translation()

    ret_d = Vector((0, 0, 0))
    ret_d.x = (ret_dy.x - ret_y.x) / EPSILON
    ret_d.y = (ret_dy.y - ret_y.y) / EPSILON
    ret_d.z = (ret_dy.z - ret_y.z) / EPSILON
    return ret_y, ret_d


def matrix_calibrate_s(y, d, parent, bone):
    EPSILON = 1 / 100

    y.x /= bone.jnt_frame.sx
    y.y /= bone.jnt_frame.sy
    y.z /= bone.jnt_frame.sz

    d.x /= bone.jnt_frame.sx
    d.y /= bone.jnt_frame.sy
    d.z /= bone.jnt_frame.sz

    return y, d

    scalemtx = Matrix.Identity(4)
    scalemtx[0][0] = y.x
    scalemtx[1][1] = y.y
    scalemtx[2][2] = y.z
    ret_y = (parent * scalemtx).to_scale()  # computing rotation value

    # computes rotation tangents by definition of derivative
    # (and now, the incredibly complex equivalent of "dy = EPSILON*d + y":
    dy = Matrix.Identity(4)
    dy[0][0] = EPSILON * d.x + y.x
    dy[1][1] = EPSILON * d.y + y.y
    dy[2][2] = EPSILON * d.z + y.z
    ret_dy = (parent * scalemtx).to_scale()

    ret_d = Vector((0, 0, 0))
    ret_d.x = (ret_dy.x - ret_y.x) / EPSILON
    ret_d.y = (ret_dy.y - ret_y.y) / EPSILON
    ret_d.z = (ret_dy.z - ret_y.z) / EPSILON

    y, d = ret_y, ret_d
    if hasattr(bone, 'parent_rot_matrix'):  # sililar to calibrate_t, need to transform the original vector
        parent_rot_matrix = bone.parent_rot_matrix
    else:
        if type(bone.parent.fget()) == Pseudobone:
            parent_rot_matrix = bone.parent.fget().jnt_frame.incr_matrix.to_quaternion().to_matrix().to_4x4()
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


class Pseudobone:
    def __init__(self, startpoint, endpoint, z_up):
        ori = endpoint - startpoint
        self.endpoint = endpoint
        self._name = None
        self.length = math.sqrt(ori.x**2 + ori.y**2 + ori.z**2)
        self.orientation = vect_normalize(ori)
        self.scale = mathutils.Vector((1, 1, 1))
        self.jnt_frame = None
        self.rotation_euler = mathutils.Euler((0, 0, 0), 'XYZ')
        self.position = startpoint
        self.scale_kf = {}  # keyframes (values)
        self.scale_tkf = {}  # keyframes (tangents)
        self.rotation_kf = {}
        self.rotation_tkf = {}
        self.position_kf = {}
        self.position_tkf = {}
        # self.transform = mathutils.Matrix.Identity(4)  # what to do with that? it will be ultimately useless.

        self._parent = None
        self.children = []

        #  property busyness --------------------------------
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
            if (self.parent.fget() is not None) and (self in self.parent.fget().children):
                self.parent.fget().children.remove(self)
            self._parent = val
            if val is None or isinstance(val, mathutils.Vector):
                return
            val.children.append(self)
        self.parent = property(_getparent, _setparent)

        def _setinchildren(holder, val):
            list.append(holder.children, val)
            val._parent = holder
        self.children_append = (lambda self2, x: _setinchildren(self, x))

    # def update_r_t(self):
    #    pass  # will work this out later

    # def recalculate_transform(self):
    #     pass  # procrastinating here too.


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

def apply_animation(bones, arm_obj, jntframes):
    """apply keyframes from pseudobones to real, armature bones"""
    if arm_obj.animation_data is None:
        arm_obj.animation_data_create()
        arm_obj.animation_data.action = bpy.data.actions.new(arm_obj.name+'_action')
        bpy.context.scene.frame_current = 0
        for com in bones:
            name = com.name.fget()
            arm_obj.data.bones[name].use_inherit_scale = False  # scale can be applied
            posebone = arm_obj.pose.bones[name]
            posebone.rotation_mode = "XZY"  # remember, coords are flipped
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
    for num, com in enumerate(bones):
        name = com.name.fget()
        bonedict = data[name]
        posebone = arm_obj.pose.bones[name]
        bpy.context.scene.frame_current = 0
        posebone.keyframe_insert('location')
        posebone.keyframe_insert('rotation_euler')
        posebone.keyframe_insert('scale')
        every_frame = list(set(com.position_kf.keys()).union(
                           set(com.rotation_kf.keys())).union(
                           set(com.scale_kf.keys())))
        every_frame.sort()
        refpos = jntframes[num]
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
            if frame in com.position_kf.keys():
                vct = com.position_kf[frame]
                tgt = com.position_tkf[frame]
                vct, tgt = matrix_calibrate_t(vct, tgt, com.parentrot, com)
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

            if frame in com.rotation_kf.keys():
                vct = com.rotation_kf[frame]
                tgt = com.rotation_tkf[frame]
                vct, tgt = matrix_calibrate_r(vct, tgt, cancel_ref_rot, com.parentrot, com)
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

            if frame in com.scale_kf.keys():
                vct = com.scale_kf[frame]
                tgt = com.scale_tkf[frame]
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
