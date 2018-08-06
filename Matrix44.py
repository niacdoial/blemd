#! /usr/bin/python3


from mathutils import Matrix, Vector, Euler
from .Evp1 import *


'''class Matrix44:
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
        ret.SetValues(*([0] * 16))
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
                              self.m[i][2]*b.m[2][j] +\
                              self.m[i][3]*b.m[3][j]
        return ret

    def MultiplyVector(self, v):
        x = self.m[0][0] * v.x + self.m[0][1] * v.y + self.m[0][2] * v.z + self.m[0][3]  # corrected
        y = self.m[1][0] * v.x + self.m[1][1] * v.y + self.m[1][2] * v.z + self.m[1][3]
        z = self.m[2][0] * v.x + self.m[2][1] * v.y + self.m[2][2] * v.z + self.m[2][3]
        v = Vector3()
        v.setXYZ(x, y, z)
        return v

    def __mul__(self, other):
        if isinstance(other, Matrix44):
            return self.Multiply(other)
        elif isinstance(other, (int, float)):
            for a in range(4):
                for b in range(4):
                    self.m[a][b] *= other
        elif isinstance(other, Vector3):
            return self.MultiplyVector(other)

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
        self.m[2][1] = -sin(rad)
        self.m[1][2] = sin(rad)
        self.m[2][2] = cos(rad)

    def LoadRotateXLM(self, rad):
        self.LoadIdentity()  # corrected
        self.m[1][1] = cos(rad)
        self.m[1][2] = -sin(rad)  # -- -1 * sin rad same as -sin 1.5707
        self.m[2][1] = sin(rad)
        self.m[2][2] = cos(rad)

    def LoadRotateYRM(self, rad):
        self.LoadIdentity()  # corrected
        self.m[0][0] = cos(rad)
        self.m[2][0] = sin(rad)
        self.m[0][2] = -1 * sin(rad)
        self.m[2][2] = cos(rad)

    def LoadRotateYLM(self, rad):
        self.LoadIdentity()  # corrected
        self.m[0][0] = cos(rad)
        self.m[0][2] = sin(rad)
        self.m[2][0] = -1 * sin(rad)
        self.m[2][2] = cos(rad)

    def LoadRotateZRM(self, rad):
        self.LoadIdentity()  # corrected
        self.m[0][0] = cos(rad)
        self.m[1][0] = -1 * sin(rad)
        self.m[0][1] = sin(rad)
        self.m[1][1] = cos(rad)

    def LoadRotateZLM(self, rad):
        self.LoadIdentity()  # corrected
        self.m[0][0] = cos(rad)
        self.m[0][1] = -1 * sin(rad)
        self.m[1][0] = sin(rad)
        self.m[1][1] = cos(rad)

    def LoadScale(self, xs, ys, zs):
        self.LoadIdentity()
        self.m[0][0] = xs
        self.m[1][1] = ys
        self.m[2][2] = zs'''


def Mad(r, m, f):
    for j in range(3):
        for k in range(4):
            r[j][k] += f * m[j][k]
    return r


def LocalMatrix(jnt, i, use_scale):
    scale_vector = Vector((jnt.frames[i].sx, jnt.frames[i].sy, jnt.frames[i].sz))
    sx = Matrix.Scale(scale_vector.x, 4, Vector((1, 0, 0)))
    sy = Matrix.Scale(scale_vector.y, 4, Vector((0, 1, 0)))
    sz = Matrix.Scale(scale_vector.z, 4, Vector((0, 0, 1)))

    # TODO: I don't  know which of these two return values are the right ones
    # (if it's the first, then what is scale used for at all?)

    # looks wrong in certain circumstances...
    if use_scale:
        return jnt.matrices[i] * sz * sy * sx  # this looks a bit better with mario's bottle_in animation
    else:
        return jnt.matrices[i]  # this looks better with vf_064l.bdl (from zelda)



def FrameMatrix(f):
    t = Matrix.Translation(Vector((f.t.x, f.t.y, f.t.z)))
    r = Euler((f.rx, f.ry, f.rz), 'XYZ').to_matrix().to_4x4()
    res = t*r
    return res


def updateMatrix(frame, parentmatrix):
    return parentmatrix*FrameMatrix(frame)

def updateMatrixTable(evp, drw, jnt, currPacket, multiMatrixTable, matrixTable, isMatrixWeighted, use_scale):
    global dataholder
    for n in range(len(currPacket.matrixTable)):
        index = currPacket.matrixTable[n]

        # if index is 0xffff, use the last packet's data.
        if index != 0xffff:  # 0xffff this means keep old entry
            if drw.isWeighted[index]:  # corrected
                # --TODO: the EVP1 data should probably be used here,
                # --figure out how this works (most files look ok
                # --without this, but models/ji.bdl is for example
                # --broken this way)
                # --matrixTable[n] = def_;

                # --the following _does_ the right thing...it looks
                # --ok for all files, but i don't understand why :-P
                # --(and this code is slow as hell, so TODO: fix this)

                # --NO idea if this is right this way...
                m = Matrix()
                m.zero()  # zero-ifiy m

                mm = evp.weightedIndices[drw.data[index]]  # -- get MultiMatrix # corrected
                singleMultiMatrixEntry = MultiMatrix()

                singleMultiMatrixEntry.weights = mm.weights.copy()
                singleMultiMatrixEntry.indices = mm.indices.copy()
                for r in range(len(mm.weights)):
                    # did before.
                    #singleMultiMatrixEntry.weights[r] = mm.weights[r]
                    #singleMultiMatrixEntry.indices[r] = mm.indices[r]

                    # corrected (r]+1) # -- (drw.data[mm.indices[r]+ 1] + 1) -- bone index
                    # --  messageBox (mm.indices as string)
                    # --if (mm.indices[r] != 0) then
                    # -- (
                    sm1 = evp.matrices[mm.indices[r]]  # corrected(r]+1) # -- const Matrix44f
                    sm2 = LocalMatrix(jnt, mm.indices[r], use_scale)  # corrected (r]+1)
                    sm3 = sm2*sm1
                    # )
                    # else
                    # --	sm3 = (LocalMatrix mm.indices[r] )

                    Mad(m, sm3, mm.weights[r])

                while len(multiMatrixTable) <= n:
                    multiMatrixTable.append(None)
                multiMatrixTable[n] = singleMultiMatrixEntry
                m[3][3] = 1  # fixed
                while len(matrixTable) <= n:
                    matrixTable.append(None)
                matrixTable[n] = m
                while len(isMatrixWeighted) <= n:
                    isMatrixWeighted.append(None)
                isMatrixWeighted[n] = True
            else:
                while len(matrixTable) <= n:
                    matrixTable.append(None)
                while len(isMatrixWeighted) <= n:
                    isMatrixWeighted.append(None)
                matrixTable[n] = jnt.matrices[drw.data[index]]  # corrected x2
                isMatrixWeighted[n] = False

                singleMultiMatrixEntry = MultiMatrix()
                singleMultiMatrixEntry.weights = [1]
                singleMultiMatrixEntry.indices = [drw.data[index]]  # corrected x2  # -- bone index

                while len(multiMatrixTable) <= n:
                    multiMatrixTable.append(None)
                multiMatrixTable[n] = singleMultiMatrixEntry
                # -- end if drw.isWeighted[index] then


def rotation_part(mtx):
    ret = mtx.copy()
    for i in range(3):
        ret[i][3] = 0
    return ret