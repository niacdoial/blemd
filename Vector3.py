#! /usr/bin/python
from .maxheader import MessageBox


class Vector3:
    # <variable x>
    # <variable y>
    # <variable z>
    # <function>

    # <function>

    # <function>

    # <function>

    # <function>

    def __init__(self):  # GENERATED!
        pass

    def ToMaxScriptPos(self):
        return [self.x, self.y, self.z]
        # --return [self.x, -self.z, self.y] -- flip order

    def ToMaxScriptPosFlip(self):
        return [self.x, -self.z, self.y] # -- flip order

    def IsZero(self):
        return self.x != 0 and\
               self.y != 0 and\
               self.z != 0

    def setXYZFlip(self, aX, aY, aZ):
                
        self.x = aX
        self.y = -aZ
        self.z = aY

    def setXYZ(self, aX, aY, aZ):
                
        self.x = aX
        self.y = aY
        self.z = aZ

        # --self.y = -aZ
        # --self.z = aY

        # -- left hand
        # -- self.y,self.z,self.x // top ok. needs self.z rotate
        # -- self.z,self.x,self.y
        # -- self.x,self.z,self.y
        # -- self.z,self.y,self.x // same as orig?
        # -- self.y,self.z,self.x,    self.z,self.x,self.y,
        # --self.x = -aY
        # --self.y = -aX
        # --self.z= -aY
        if self.x is None:
            MessageBox("X Undefined")
        if self.y is None:
            MessageBox("Y Undefined")
        if self.z is None:
            MessageBox("Z Undefined")