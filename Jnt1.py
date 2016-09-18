#! /usr/bin/python3
from .Vector3 import *
from .maxheader import MessageBox

class Jnt1Header:
    """# <variable tag>
    # -- char[4] 'JNT1'
    # <variable sizeOfSection>
    # -- u32 
    # <variable count>
    # -- u16 number of joints
    # <variable pad>
    # -- u16 padding u16 (?)
    # <variable jntEntryOffset>
    # -- u32 joints are stored at this place
    # -- offset relative to Jnt1Header start
    # <variable unknownOffset>
    # -- u32 there are count u16's stored at this point,
    # -- always the numbers 0 to count - 1 (in that order).
    # -- perhaps an index-to-stringtable-index map?
    # -- offset relative to Jnt1Header start
    # <variable stringTableOffset>
    # -- u32 names of joints
    # <function>"""

    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        self.tag = br.ReadFixedLengthString(4)
        self.sizeOfSection = br.ReadDWORD()
        self.count = br.ReadWORD()
        self.pad = br.ReadWORD()
        self.jntEntryOffset = br.ReadDWORD()
        self.unknownOffset = br.ReadDWORD()
        self.stringTableOffset = br.ReadDWORD()
  

class JntEntry:
    """# <variable unknown>
    # -- u16 no idea how this works...always 0, 1 or 2
    # --"matrix type" according to yaz0r - whatever this means ;-)
    # <variable pad>
    # -- u16 always 0x00ff in mario, but not in zelda
    # <variable sx>
    # <variable sy>
    # <variable sz>
    # -- float scale
    # <variable rx>
    # <variable ry>
    # <variable rz>
    # -- s16 -32768 = -180 deg, 32767 = 180 deg
    # <variable pad2>
    # -- u16 always 0xffff
    # <variable tx>
    # <variable ty>
    # <variable tz>
    # -- float translation
    # <variable unknown2>
    # -- float 
    # <variable bbMin>
    # -- float[3] bounding box (?)
    # <variable bbMax>
    # -- float[3] bounding box (?)
    # <function>"""

    def __init__(self):  # GENERATED!
        self.bbMin= []
        self.bbMax= []

    def LoadData(self, br):
                
        # -- don't flip values (has rotation problems)
        self.unknown = br.ReadWORD()
        self.pad = br.ReadWORD()
        self.sx = br.GetFloat()
        self.sy = br.GetFloat()          # -- flip
        self.sz = br.GetFloat()          # -- flip

        self.rx = br.GetSHORT()
        self.ry = br.GetSHORT()
        self.rz = br.GetSHORT()

        self.pad2 = br.ReadWORD()

        self.tx = br.GetFloat()
        self.ty = br.GetFloat()         # -- flip
        self.tz = br.GetFloat()          # -- flip

        self.unknown2 = br.GetFloat()

        self.bbMin = []
        for _ in range(3) :
            self.bbMin.append(br.GetFloat())
        self.bbMax = []
        for _ in range(3):
            self.bbMax.append(br.GetFloat())

        if self.unknown < 0 or self.unknown > 2 :
            msg = "jnt1: self.unknown of " + str(self.unknown) + " joint not in [0, 2]"
            raise ValueError(msg)


class JntFrame:
    """# <variable sx>
    # <variable sy>
    # <variable sz>
    # -- float  scale
    # <variable rx>
    # <variable ry>
    # <variable rz>
    # -- float rotation (in degree)
    # <variable t>
    # -- Vector3f  //translation
    # <variable name>
    # -- string
    # --_unknown ,
    # --_pad,
    # --_unknown2,
    # ---bbMin ,
    # --bbMax,
    # --: u16 unknown
    # --bounding box, float unknown2
    # <function>"""

    def __init__(self):  # GENERATED!
        pass

    def InitFromJntEntry(self, e):
                
        self.sx = e.sx
        self.sy = e.sy
        self.sz = e.sz

        self.rx = (e.rx/32768. *180)
        self.ry = (e.ry/32768. *180)
        self.rz = (e.rz/32768. *180)

        self.t = Vector3()
        self.t.setXYZ(e.tx, e.ty, e.tz)

        _bbMin = e.bbMin
        _bbMax= e.bbMax
  

class Jnt1:
    """# <variable frames>
    # -- std::vector<Frame> 
    # -- the Frames have to be converted to matrices
    # -- to be usable by gl. isMatrixValid stores
    # -- if a matrix represents a frame of if the
    # -- frame has changed since the matrix was
    # -- built (in animations for example)
    # <variable matrices>
    # -- std::vector<Matrix44f> 
    # <variable isMatrixValid>
    # -- std::vector<bool>  //TODO: use this
    # --TODO: unknown array
    # <function>"""

    def __init__(self):  # GENERATED!
        self.matrices= []
        self.isMatrixValid= []
        self.frames= []

    def LoadData(self, br):
                
        jnt1Offset = br.Position()

        header = Jnt1Header()
        header.LoadData(br)

        stringTable = br.ReadStringTable (jnt1Offset + header.stringTableOffset)


        if len(stringTable) != header.count :
            MessageBox("jnt1: number of strings doesn't match number of joints")
            raise ValueError("jnt1: number of strings doesn't match number of joints")




        # -- read joints
        br.SeekSet(jnt1Offset + header.jntEntryOffset)
        self.frames = []
        # -- self.frames.resize(h.count);
        self.matrices = []
        # -- self.matrices.resize(h.count);
        self.isMatrixValid = []
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
            self.frames.append(f)

