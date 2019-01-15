#! /usr/bin/python3
import os
from .common import MessageBox
from math import log2, floor, ceil
import sys
import logging
log = logging.getLogger('bpy.ops.import_mesh.bmd.fileOut')


def bitshiftu8(val, shifter):
    if val // 256:
        raise ValueError("not a U8")
    a8 = val & 0b00000001
    a7 = val & 0b00000010
    a6 = val & 0b00000100
    a5 = val & 0b00001000
    a4 = val & 0b00010000
    a3 = val & 0b00100000
    a2 = val & 0b01000000
    a1 = val & 0b10000000


class ReturnValue:
    # <variable srcPos>
    # <variable dstPos>
    # -- int 
    def __init__(self):  # GENERATED!
        self.srcPos= 0
        self.dstPos= 0

class BinaryWriter:
    """# <variable _f>
    # -- binary file stream
    # <variable _size>
    # <variable _tempFileName>
    # <function>

    # <function>

    # -- get a string with a fixed size
    # <function>

    # -- 4 bytes, unsigned int
    # <function>

    # <function>

    # -- TODO: Dosn't work
    # <function>

    # -- seek with an offset to the current position
    # <function>

    # -- seek to an absolute position
    # <function>

    # <function>

    # <function>

    # -- read a null terminated string from an absolute offset
    # <function>

    # -- 2 bytes, unsigned short
    # <function>

    # -- returns string[]
    # <function>

    # -- 2 bytes, signed short. Using two's complement
    # <function>

    # -- must reverse value for read. big endian [could also write / read from another file]
    # -- http://java.sun.com/j2se/1.3/docs/api/java/lang/Float.html#intBitsToFloat(int)
    # <function>"""

    def __init__(self):  # GENERATED!
        pass

    def Close(self):
        self._f.close()

    def writeDword(self, v):
        #w1 = chr((v & 0xff000000) >> 24).encode()
        #w2 = chr((v & 0x00ff0000) >> 16).encode()
        #w3 = chr((v & 0x0000ff00) >> 8).encode()
        #w4 = chr(v & 0x000000ff).encode()
        self._f.write(v.to_bytes(4, 'big'))#(w1+w2+w3+w4)

    def Open(self, srcPath):
        self._f = open(srcPath, "wb+")
        # --fseek self._f 0 seek_end
        # --self._size = ftell self._f
        self._f.seek(0)
        if self._f is None:
            log.fatal("Unable to open file " + srcPath)
            raise ValueError("Unable to open file " + srcPath)

    def EOF(self):
        raise EOFError("NYI")
        # return self._f.tell()  >= self._size

    def SeekCur(self, offset):
        self._f.seek(self._f.tell() + offset)

    def SeekSet(self, position):
        self._f.seek(position)

    def readlast(self, n):
        self.SeekCur(-n)
        return self._f.read(n)

    def Position(self):
        return self._f.tell()

    def writeByte(self, v):
        self._f.write(v.to_bytes(1, 'big'))  #(chr(v).encode())

    def writeString(self, string, fixed_len=True):

        string = string.encode('cp1252')
        if not fixed_len:
            string += b'\x00'
        self._f.write(string)

    def writeWord(self, v):
        if v < 0:
            log.fatal("ReadWORD should be unsigned")
            raise ValueError("ReadWORD should be unsigned")
        # w1 = chr((v & 0xff00) >> 8).encode()
        # w2 = chr(v & 0x00ff).encode()
        self._f.write(v.to_bytes(2, 'big'))  #(w1+w2)

    def WriteStringTable(self, table):

        origin = self.Position()

        count = len(table)         # -- orig = 35 read = 35. current pos = ok?
        self.writeWord(count)
        self.writeWord(0xffff)  # skip pad bytes

        StringsPos = 4*count + 4

        for i in range(count):
            curPos = self.Position()

            stringOffset = StringsPos
            self.SeekSet(origin + StringsPos)
            self.writeString(table[i], fixed_len=False)
            StringsPos = self.Position() - origin

            self.SeekSet(curPos)
            self.writeWord(stringOffset)
            self.writeWord(0xffff)  # unknown use

        self.SeekSet(origin + StringsPos)

    def writeShort(self, v):

        if v < 0:
            v *= -1
            v -= 1
            v ^= 0xffff
        self.writeWord(v)

    def writeFloat(self, v):
        if v < 0:
            neg = (1 << 31)
            v *= -1
        else:
            neg = 0
        if v == 0:
            e = 0
            m = 0
        else:
            e = int(floor(log2(v/0x1000000))+1 + 150)
        if e < 0 or e > 0xff:
            log.warning("float off range, assuming zero")
            e = 0
            m = 0

        elif e == 0:
            e = e << 23
            m = int(v / 2**(-150)) >> 1
        else:
            e = e << 23
            m = int(v/2**(floor(log2(v/0x1000000))+1))
            if m < 0x800000 or m >= 0x1000000:
                raise ValueError('float dump: bad m value')
            m &= 0x7fffff
        self.writeDword(neg | e | m)

    def writePadding(self, bcount):
        string = 'Padding '
        string = string * int(ceil(bcount/len(string)))
        self.writeString(string[:bcount])

    def writePaddingTo16(self):
        length = 16 - (self._f.tell() % 16)
        self.writePadding(length)

    def addPadding(self, size):
        return 16 * (size//16 + 1)