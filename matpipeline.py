from mathutils import Color
from math import log2

class MaterialSpace:
    def __init__(self):
        self.finalcolorc = Color()
        self.finalcolora = 0.0
        self.reg1c = Color()
        self.reg1a = 0.0
        self.reg2c = Color()
        self.reg2a = 0.0

class Var:
    def __init__(self, op='', data=0.0, other=0):

        if op:
            self.type = 'op'
            self.op = op
            self.other = other
        else:
            self.type = 'val'
        self.value = data
    
    def __add__(self, other):
        if not isinstance(other, Var):
            other = Var(data=other)
        return Var('+', self, other)

    def __mul__(self, other):
        if not isinstance(other, Var):
            other = Var(data=other)
        return Var('*', self, other)

    def __sub__(self, other):
        if not isinstance(other, Var):
            other = Var(data=other)
        return Var('-', self, other)

    def __le__(self, other):
        if not isinstance(other, Var):
            other = Var(dat=other)
        return Var("bool", other-self+0.000001)

    def __ge__(self, other):
        if not isinstance(other, Var):
            other = Var(data=other)
        return Var("bool", self-other+0.000001)

    def __lt__(self, other):
        if not isinstance(other, Var):
            other = Var(data=other)
        return Var("bool", other-self)

    def __gt__(self, other):
        if not isinstance(other, Var):
            other = Var(data=other)
        return Var("bool", self-other)

class Sampler:
    def __init__(self):
        self.wrapS = True
        self.wrapT = True
        self.mirrorS = False
        self.mirrorT = False

    def setTexWrapMode(self, smode, tmode):
        if smode == 0:
            self.wrapS = False
        elif smode == 1: pass
        elif smode == 0:
            self.mirrorS = True
        else:
            raise ValueError('invalid WrapMode')

        if tmode == 0:
            self.wrapT = False
        elif tmode == 1: pass
        elif tmode == 0:
            self.mirrorT = True
        else:
            raise ValueError('invalid WrapMode')


def writeTexGen(material, texGen, i, matbase, mat3):
    dst=material.texCoord[i]

    if texGen.texGenType in (0,1):
        if texGen.matrix == 0x3c:
            pass
        elif (texGen.matrix >= 0x1e and texGen.matrix <= 0x39):
            dst.data= Var((texGen.matrix - 0x1e)/3)  # XCX get the right matrix
        else:
            print("writeTexGen() type "+str(texGen.texGenType)+": unsupported matrix"+hex(texGen.matrix), file=stderr)

        if (texGen.texGenSrc >=4 and texGen.texGenSrc <=11):
            dst.data = dst.data*(texGen.texGenSrc-4)  # XCX get real texcoord
        elif texGen.texGenSrc == 0:
            dst.data = dst.data*("position")
        elif texGen.texGenSrc == 1:
            dst.data = dst.data*("normal")