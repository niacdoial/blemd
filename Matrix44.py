#! /usr/bin/python3


from .Vector3 import *
from math import cos, sin


class Matrix44:
    """# --_00, _01, _02, _03,
    # --_10, _11, _12, _13,
    # --_20, _21, _22, _23,
    # --_30, _31, _32, _33,
    # <variable m>
    # <function>

    # <function>

    # <function>

    # <function>

    # <function>

    # <function>

    # -- returns point
    # -- see drawBmd.cpp
    # <function>

    # <function>

    # <function>

    # <function>

    # <function>

    # <function>

    # <function>

    # <function>

    # <function>"""

    def __init__(self):  # GENERATED!
        pass

    def __eq__(self, b):
        for i in range(4):
            for j in range(4):
                if self.m[i][j] != b.m[i][j]:
                    return False
        return True

    def copy(self):
        ret = Matrix44()
        ret.SetValues(*([0]*16))
        for i in range(4):
            for j in range(4):
                ret.m[i][j] = self.m[i][j]
        return ret

    def SetValues(self, v00, v01, v02, v03, v10, v11, v12, v13, v20, v21, v22, v23, v30, v31, v32, v33):
        self.m = []
        self.m.append([v00, v01, v02, v03])
        self.m.append([v10, v11, v12, v13])
        self.m.append([v20, v21, v22, v23])
        self.m.append([v30, v31, v32, v33])

    def GetIdentity(self):
        mat = Matrix44()
        mat.m = []
        mat.m.append([1.0, 0.0, 0.0, 0.0])
        mat.m.append([0.0, 1.0, 0.0, 0.0])
        mat.m.append([0.0, 0.0, 1.0, 0.0])
        mat.m.append([0.0, 0.0, 0.0, 1.0])
        return mat

    def LoadIdentity(self):
        self.m = []
        self.m.append([1.0, 0.0, 0.0, 0.0])
        self.m.append([0.0, 1.0, 0.0, 0.0])
        self.m.append([0.0, 0.0, 1.0, 0.0])
        self.m.append([0.0, 0.0, 0.0, 1.0])

    def LoadZero(self):
        self.m = []
        self.m.append([0.0, 0.0, 0.0, 0.0])
        self.m.append([0.0, 0.0, 0.0, 0.0])
        self.m.append([0.0, 0.0, 0.0, 0.0])
        self.m.append([0.0, 0.0, 0.0, 0.0])

    def Multiply(self, b):
        ret = Matrix44()
        ret.LoadIdentity()
        for i in range(4):
            for j in range(4):  # corrected
                ret.m[i][j] = self.m[i][0]*b.m[0][j] +\
                              self.m[i][1]*b.m[1][j] +\
                              self.m[i][2]*b.m[2][j]
                return ret

    def MultiplyVector(self, v):
        x = self.m[0][0] * v.x + self.m[0][1]*v.y + self.m[0][2] * v.z + self.m[0][3]  # corrected
        y = self.m[1][0] * v.x + self.m[1][1]*v.y + self.m[1][2] * v.z + self.m[1][3]
        z = self.m[2][0] * v.x + self.m[2][1]*v.y + self.m[2][2] * v.z + self.m[2][3]
        v = Vector3()
        v.setXYZ(x, y, z)
        return v

    def LoadTranslateRM(self, tx, ty, tz):
                
      self.LoadIdentity()  # corrected
      self.m[3][0] = tx
      self.m[3][1] = ty
      self.m[3][2] = tz

    def LoadTranslateLM(self, tx, ty, tz):
      self.LoadIdentity()
      self.m[0][3] = tx  # corrected
      self.m[1][3] = ty
      self.m[2][3] = tz

    def LoadRotateXRM(self, rad):
      self.LoadIdentity()  # corrected
      self.m[1][1] = cos(rad)
      self.m[2][1] =-1 * sin(rad)
      self.m[1][2] =  sin(rad)
      self.m[2][2] =  cos(rad)

    def LoadRotateXLM(self, rad):
      self.LoadIdentity()  # corrected
      self.m[1][1] =  cos(rad)
      self.m[1][2] =-1 * sin(rad)         # -- -1 * sin rad saself.me as -sin 1.5707
      self.m[2][1] =  sin(rad)
      self.m[2][2] =  cos(rad)

    def LoadRotateYRM(self, rad):
       self.LoadIdentity()  # corrected
       self.m[0][0] =  cos(rad)
       self.m[2][0] =  sin(rad)
       self.m[0][2] =-1 * sin(rad)
       self.m[2][2] =  cos(rad)

    def LoadRotateYLM(self, rad):
      self.LoadIdentity()  # corrected
      self.m[0][0] =  cos(rad)
      self.m[0][2] =  sin(rad)
      self.m[2][0] =-1 * sin(rad)
      self.m[2][2] =  cos(rad)

    def LoadRotateZRM(self, rad):
      self.loadIdentity()  # corrected
      self.m[0][0] =  cos(rad)
      self.m[1][0] =-1 * sin(rad)
      self.m[0][1] =  sin(rad)
      self.m[1][1] =  cos(rad)

    def LoadRotateZLM(self, rad):
      self.LoadIdentity()  # corrected
      self.m[0][0] = cos(rad)
      self.m[0][1] = -1 * sin(rad)
      self.m[1][0] = sin(rad)
      self.m[1][1] = cos(rad)


