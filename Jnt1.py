#! /usr/bin/python3
from .maxheader import MessageBox
from mathutils import Vector
from math import pi
import logging
log = logging.getLogger('bpy.ops.import_mesh.bmd.jnt1')

class Jnt1Header:
    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        self.tag = br.ReadFixedLengthString(4)  # "jnt1"
        self.sizeOfSection = br.ReadDWORD()
        self.count = br.ReadWORD()  # number of joints
        self.pad = br.ReadWORD()  # padding?
        self.jntEntryOffset = br.ReadDWORD()  # joints are stored at this place
                                              # offset relative to Jnt1Header start
        self.unknownOffset = br.ReadDWORD()  # there are count u16's stored at this point,
                                             # always the numbers 0 to count - 1 (in that order).
                                             # perhaps an index-to-stringtable-index map?
                                             # offset relative to Jnt1Header start
        self.stringTableOffset = br.ReadDWORD()  # names of joints


class JntEntry:
    def __init__(self):  # GENERATED!
        self.bbMin = []
        self.bbMax = []

    def LoadData(self, br):
                
        # values flipped late
        self.unknown = br.ReadWORD()
        # no idea how this works...always 0, 1 or 2.
        # "matrix type" according to yaz0r - whatever this means ;-)
        self.pad = br.ReadWORD()
        # always 0x00ff in mario, but not in zelda
        self.sx = br.GetFloat()
        self.sy = br.GetFloat()
        self.sz = br.GetFloat()

        self.rx = br.GetSHORT()  # short: each increment is an 1/2**16 of turn
        self.ry = br.GetSHORT()
        self.rz = br.GetSHORT()

        self.pad2 = br.ReadWORD()  # always 0xffff

        self.tx = br.GetFloat()  # translation floats
        self.ty = br.GetFloat()
        self.tz = br.GetFloat()

        self.unknown2 = br.GetFloat()

        self.bbMin = []  # bounding box?
        for _ in range(3):
            self.bbMin.append(br.GetFloat())
        self.bbMax = []
        for _ in range(3):
            self.bbMax.append(br.GetFloat())

        if self.unknown < 0 or self.unknown > 2:
            msg = "jnt1: self.unknown of " + str(self.unknown) + " joint not in [0, 2]"
            raise ValueError(msg)


class JntFrame:
    def __init__(self):  # GENERATED!
        pass

    def InitFromJntEntry(self, e):
                
        self.sx = e.sx  # scale
        self.sy = e.sy
        self.sz = e.sz

        self.rx = (e.rx/32768. * pi)  # angles are coded to be a full turn in 2**16 'ticks'
        self.ry = (e.ry/32768. * pi)  # and we need to use radians
        self.rz = (e.rz/32768. * pi)

        self.t = Vector((e.tx, e.ty, e.tz))  # translation

        self._bbMin = e.bbMin  # is this even needed? (bounding box)
        self._bbMax = e.bbMax
  

class Jnt1:
    def __init__(self):  # GENERATED!
        self.matrices = []  # matrixes of the bones' base positions: used to computeoriginal vertex positions
        self.isMatrixValid = []  # TODO: use this or delete it
        self.frames = []  # base position of bones, used as a reference to compute animations as a difference to this

    def LoadData(self, br):
                
        jnt1Offset = br.Position()

        header = Jnt1Header()
        header.LoadData(br)

        stringTable = br.ReadStringTable (jnt1Offset + header.stringTableOffset)


        if len(stringTable) != header.count :
            log.warning("jnt1: number of strings doesn't match number of joints")
            raise ValueError("jnt1: number of strings doesn't match number of joints")




        # -- read joints
        br.SeekSet(jnt1Offset + header.jntEntryOffset)
        self.frames = [None]*header.count
        # -- self.frames.resize(h.count);
        self.matrices = [None]*header.count
        # -- self.matrices.resize(h.count);
        self.isMatrixValid = [False]*header.count
        # -- self.isMatrixValid.resize(h.count);
        for i in range(header.count):
            e = JntEntry()
            e.LoadData(br)
            f = JntFrame()
            f.InitFromJntEntry(e)

            if i < len(stringTable):  # -- should always be true
                f.name = stringTable[i]
            else:
                raise ValueError("i < stringtable.count %d %d " % (i, len(stringTable)))
            self.frames[i] = f