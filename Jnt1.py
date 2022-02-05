#! /usr/bin/python3
from .common import MessageBox
from mathutils import Vector, Matrix, Euler
from math import pi, ceil
from . import common
import logging
log = logging.getLogger('bpy.ops.import_mesh.bmd.jnt1')

class Jnt1Header:
    size = 24
    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        self.tag = br.ReadFixedLengthString(4)  # "JNT1"
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

    def DumpData(self, bw):
        bw.writeString("JNT1")
        bw.writeDword(self.sizeOfSection)
        bw.writeWord(self.count)
        bw.writeWord(self.pad)

        bw.writeDword(self.jntEntryOffset)
        # offset relative to Jnt1Header start
        bw.writeDword(self.unknownOffset)
        # always the numbers 0 to count - 1 (in that order).
        # perhaps an index-to-stringtable-index map?
        # offset relative to Jnt1Header start
        bw.writeDword(self.stringTableOffset)


class JntEntry:
    size = 0x40
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
            if common.GLOBALS.PARANOID:
                raise ValueError(msg)
            else:
                log.error(msg)


    def FromFrame(self, f):
        self.sx = f.sx
        self.sy = f.sy
        self.sz = f.sz

        self.rx = round(f.rx * 32768./pi)
        self.ry = round(f.ry * 32768./pi)
        self.rz = round(f.rz * 32768./pi)

        self.tx, self.ty, self.tz = f.t.xyz
        self.bbMin = f._bbMin
        self.bbMax = f._bbMax

        self.unknown = 0x00  # correct value unknown
        self.pad = 0x00ff  # or 0x0000 ??
        self.pad2 = 0xffff

    def DumpData(self, bw):
        # values flipped late
        bw.WriteWORD(self.unknown)
        # no idea how this works...always 0, 1 or 2.
        # "matrix type" according to yaz0r - whatever this means ;-)
        bw.WriteWORD(self.pad)
        # always 0x00ff in mario, but not in zelda
        bw.writeFloat(self.sx)
        bw.writeFloat(self.sy)
        bw.writeFloat(self.sz)

        bw.writeShort(self.rx)  # short: each increment is an 1/2**16 of turn
        bw.writeShort(self.ry)
        bw.writeShort(self.rz)

        bw.WriteWORD(self.pad2)  # always 0xffff

        bw.writeFloat(self.tx)  # translation floats
        bw.writeFloat(self.ty)
        bw.writeFloat(self.tz)

        bw.writeFloat(self.unknown2)

        # bounding box?
        for i in range(3):
            bw.writeFloat(self.bbMin[i])
        for i in range(3):
            bw.writeFloat(self.bbMax[i])


class JntFrame:
    def __init__(self):  # GENERATED!
        self.matrix = None

    def InitFromJntEntry(self, e):

        self.sx = e.sx  # scale
        self.sy = e.sy
        self.sz = e.sz

        flag = False  # for logging purposes
        if e.sx**2 < 0.01:
            self.sx = 1
            flag = True
        if e.sy**2 < 0.01:
            self.sy = 1
            flag = True
        if e.sz**2 < 0.01:
            self.sz = 1
            flag = True
        if flag:
            log.warning('Joint has zero scaling by default: corecting to 1 (mesh aspect may be weird)')

        self.rx = (e.rx/32768. * pi)  # angles are coded to be a full turn in 2**16 'ticks'
        self.ry = (e.ry/32768. * pi)  # and we need to use radians
        self.rz = (e.rz/32768. * pi)

        self.t = Vector((e.tx, e.ty, e.tz))  # displacement

        self._bbMin = e.bbMin  # is this even needed? (bounding box)
        self._bbMax = e.bbMax


    def getFrameMatrix(self):
        return Matrix.Translation(self.t) @ Euler((self.rx, self.ry, self.rz), 'XYZ').to_matrix().to_4x4()


class Jnt1:
    def __init__(self):  # GENERATED!
        self.frames = []  # base position of bones, used as a reference to compute animations as a difference to this

    def LoadData(self, br):

        jnt1Offset = br.Position()

        header = Jnt1Header()
        header.LoadData(br)

        stringTable = br.ReadStringTable (jnt1Offset + header.stringTableOffset)


        if len(stringTable) != header.count :
            log.error("jnt1: number of strings doesn't match number of joints")
            if common.GLOBALS.PARANOID:
                raise ValueError("jnt1: number of strings doesn't match number of joints")
            else:
                for i in range(header.count-len(stringTable)):
                    stringTable.append('unknown name %d' %i)




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

            f.name = stringTable[i]
            self.frames[i] = f

    def DumpData(self, bw):

        jnt1Offset = bw.Position()

        # prepare (incomplete) header, then write it
        header = Jnt1Header()
        header.count = len(self.frames)
        header.jntEntryOffset = bw.addPadding(Jnt1Header.size)
        header.unknownOffset = header.jntEntryOffset + header.count*JntEntry.size
        header.stringTableOffset = header.unknownOffset + 2 * header.count
        header.pad = 0xffff  # padding

        header.DumpData(bw)
        bw.writePadding(header.jntEntryOffset - Jnt1Header.size)

        if bw.Position != jnt1Offset + header.jntEntryOffset:
            raise ValueError('incorrect lengths in writing Jnt1')

        stringTable = header.count * [""]

        e = JntEntry()
        for i in range(header.count):
            e.FromFrame(self.frames[i])
            stringTable[i] = self.frames[i].name
            e.DumpData(bw)

        if bw.Position != jnt1Offset + header.unknownOffset:
            raise ValueError('incorrect lengths in writing Jnt1')

        for i in range(header.count):
            bw.writeWord(i)

        if bw.Position != jnt1Offset + header.stringTableOffset:
            raise ValueError('incorrect lengths in writing Jnt1')

        bw.writeStringTable(stringTable)

        # now complete and rewrite header
        header.sizeOfSection = bw.addPadding((bw.Position()-jnt1Offset))
        bw.writePadding(jnt1Offset + header.sizeOfSection - bw.Position())
        bw.SeekSet(jnt1Offset + 4)
        bw.writeDword(header.sizeOfSection)
        bw.SeekSet(jnt1Offset + header.sizeOfSection)
