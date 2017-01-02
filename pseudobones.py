import mathutils
from mathutils import Vector
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

instances = {}


class Pseudobone:
    def __init__(self, startpoint, endpoint, z_up):
        ori = endpoint - startpoint
        self.endpoint = endpoint
        self._name = None
        self.length = math.sqrt(ori.x**2 + ori.y**2 + ori.z**2)
        self.orientation = vect_normalize(ori)
        self.scale = mathutils.Vector((1, 1, 1))
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

def apply_animation(bones, arm_obj):
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
    for com in bones:
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
        for frame in every_frame:
            bpy.context.scene.frame_current = frame
            # flip y and z
            if frame in com.position_kf.keys():
                vct = com.position_kf[frame]
                tgt = com.position_tkf[frame]
                if not math.isnan(vct.x):
                    posebone.location[0] = vct.x - posebone.bone.head.x
                    co = bonedict['location'][0].keyframe_points[-1].co
                    bonedict['location'][0].keyframe_points[-1].handle_left = co+Vector((-1, tgt.x))
                    bonedict['location'][0].keyframe_points[-1].handle_right = co+Vector((1, tgt.x))
                    posebone.keyframe_insert('location', 0)
                    # fixed: add frame to keyframes AFTER setting the right value to it. so conter-intuitive.
                if not math.isnan(vct.z):
                    posebone.location[1] = -vct.z - posebone.bone.head.y
                    co = bonedict['location'][1].keyframe_points[-1].co
                    bonedict['location'][1].keyframe_points[-1].handle_left = co + Vector((-1, -tgt.z))
                    bonedict['location'][1].keyframe_points[-1].handle_right = co + Vector((1, -tgt.z))
                    posebone.keyframe_insert('location', 1)
                if not math.isnan(vct.y):
                    posebone.location[2] = vct.y - posebone.bone.head.z
                    co = bonedict['location'][2].keyframe_points[-1].co
                    bonedict['location'][2].keyframe_points[-1].handle_left = co + Vector((-1, tgt.y))
                    bonedict['location'][2].keyframe_points[-1].handle_right = co + Vector((1, tgt.y))
                    posebone.keyframe_insert('location', 2)

            if frame in com.rotation_kf.keys():
                vct = com.rotation_kf[frame]
                tgt = com.rotation_tkf[frame]
                if not math.isnan(vct.x):
                    posebone.rotation_euler[0] = vct.x - com.rotation_euler.x
                    co = bonedict['rotation_euler'][0].keyframe_points[-1].co
                    bonedict['rotation_euler'][0].keyframe_points[-1].handle_left = co + Vector((-1, tgt.x))
                    bonedict['rotation_euler'][0].keyframe_points[-1].handle_right = co + Vector((1, tgt.x))
                    posebone.keyframe_insert('rotation_euler', 0)
                if not math.isnan(vct.z):
                    posebone.rotation_euler[1] = -vct.z + com.rotation_euler.z
                    co = bonedict['rotation_euler'][1].keyframe_points[-1].co
                    bonedict['rotation_euler'][1].keyframe_points[-1].handle_left = co + Vector((-1, -tgt.z))
                    bonedict['rotation_euler'][1].keyframe_points[-1].handle_right = co + Vector((1, -tgt.z))
                    posebone.keyframe_insert('rotation_euler', 1)
                if not math.isnan(vct.y):
                    posebone.rotation_euler[2] = vct.y - com.rotation_euler.y
                    co = bonedict['rotation_euler'][2].keyframe_points[-1].co
                    bonedict['rotation_euler'][2].keyframe_points[-1].handle_left = co + Vector((-1, tgt.y))
                    bonedict['rotation_euler'][2].keyframe_points[-1].handle_right = co + Vector((1, tgt.y))
                    posebone.keyframe_insert('rotation_euler', 2)

            if frame in com.scale_kf.keys():
                vct = com.scale_kf[frame]
                tgt = com.scale_tkf[frame]
                if not math.isnan(vct.x):
                    posebone.scale[0] = vct.x / com.scale[0]
                    co = bonedict['scale'][0].keyframe_points[-1].co
                    bonedict['scale'][0].keyframe_points[-1].handle_left = co + Vector((-1, tgt.x))
                    bonedict['scale'][0].keyframe_points[-1].handle_right = co + Vector((1, tgt.x))
                    posebone.keyframe_insert('scale', 0)
                if not math.isnan(vct.z):
                    posebone.scale[1] = -vct.z / (-com.scale[2])
                    co = bonedict['scale'][1].keyframe_points[-1].co
                    bonedict['scale'][1].keyframe_points[-1].handle_left = co + Vector((-1, -tgt.z))
                    bonedict['scale'][1].keyframe_points[-1].handle_right = co + Vector((1, -tgt.z))
                    posebone.keyframe_insert('scale', 1)
                if not math.isnan(vct.y):
                    posebone.scale[2] = vct.y / com.scale[1]
                    co = bonedict['scale'][2].keyframe_points[-1].co
                    bonedict['scale'][2].keyframe_points[-1].handle_left = co + Vector((-1, tgt.y))
                    bonedict['scale'][2].keyframe_points[-1].handle_right = co + Vector((1, tgt.y))
                    posebone.keyframe_insert('scale', 2)
