import mathutils
import math

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
        self.scale = mathutils.Vector((0, 0, 0))
        self.rotation_euler = mathutils.Euler((0, 0, 0), 'XYZ')
        self.position = startpoint
        self.scale_kf = {}
        self.rotation_kf = {}
        self.position_kf = {}
        self.transform = mathutils.Matrix.Identity(4)  # what to do with that?

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

    def update_r_t(self):
        pass  # will work this out later

    def recalculate_transform(self):
        pass  # procrastinating here too.


def getBoneByName(name):
    global instances
    try:
        return instances[name]
    except KeyError:
        return None

