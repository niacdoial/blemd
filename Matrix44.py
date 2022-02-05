#! /usr/bin/python3


from mathutils import Matrix, Vector, Euler
from .Evp1 import *


def Mad(r, m, f):
    for j in range(3):
        for k in range(4):
            r[j][k] += f * m[j][k]
    return r


def LocalMatrix(jnt, i, use_scale):
    f = jnt.frames[i]
    scale_vector = Vector((f.sx, f.sy, f.sz))
    sx = Matrix.Scale(scale_vector.x, 4, Vector((1, 0, 0)))
    sy = Matrix.Scale(scale_vector.y, 4, Vector((0, 1, 0)))
    sz = Matrix.Scale(scale_vector.z, 4, Vector((0, 0, 1)))

    # TODO: I don't  know which of these two return values are the right ones
    # (if it's the first, then what is scale used for at all?)

    # looks wrong in certain circumstances...
    if use_scale:
        return f.matrix @ sz @ sy @ sx  # this looks a bit better with mario's bottle_in animation
    else:
        return f.matrix  # this looks better with vf_064l.bdl (from zelda)


def FrameMatrix(f):
    t = Matrix.Translation(Vector((f.t.x, f.t.y, f.t.z)))
    r = Euler((f.rx, f.ry, f.rz), 'XYZ').to_matrix().to_4x4()
    res = t@r
    return res


def updateMatrix(frame, parentmatrix):
    return parentmatrix@FrameMatrix(frame)

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
                    sm1 = evp.matrices[mm.indices[r]]  # -- const Matrix44f
                    sm2 = LocalMatrix(jnt, mm.indices[r], use_scale)
                    sm3 = sm2@sm1
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
                matrixTable[n] = jnt.frames[drw.data[index]].matrix
                isMatrixWeighted[n] = False

                singleMultiMatrixEntry = MultiMatrix()
                singleMultiMatrixEntry.weights = [1]
                singleMultiMatrixEntry.indices = [drw.data[index]]

                while len(multiMatrixTable) <= n:
                    multiMatrixTable.append(None)
                multiMatrixTable[n] = singleMultiMatrixEntry
                # -- end if drw.isWeighted[index] then


def rotation_part(mtx):
    ret = mtx.copy()
    for i in range(3):
        ret[i][3] = 0
    return ret


def is_near(mm1, mm2):
    if len(mm1.indices) != len(mm2.indices) :
        return False

    mm2d = {}
    for i in range(len(mm2.indices)):
        mm2d[mm2.indices[i]] = mm2.weights[i]

    for i in range(len(mm1.indices)):
        ref = mm2d.get(mm1.indices[i], -1)
        if ref == -1:
            return False
        if abs(mm1.weights[i] - ref) > 1E-3:
            return False

    return True
