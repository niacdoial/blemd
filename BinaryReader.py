#! /usr/bin/python3
import os
from .maxheader import MessageBox, newfile
from array import array

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
        self.srcPos = 0
        self.dstPos = 0

    def __iadd__(self, other):
        self.srcPos += other.srcPos
        self.dstPos += other.dstPos


def decodeBlock(src, dst):
    currCodeByte = None  # u8
    r = ReturnValue()
    pos = dst.tell()
    dst.seek(0, 2)  # end

    currByteCode = src.read(1)
    if currByteCode == b'':
        # EOF
        raise EOFError()
    r.srcPos += 1
    for _ in range(8):  # bytecode is for 8 "instructions"
        if (currCodeByte & 0x80) != 0:
            # straight copy
            temp = src.read(1)
            if temp == b'':
                break  # EOF
            dst.write(temp)
            r.dstPos += 1
            r.srcPos += 1

        else:
            # RLE part
            byte1 = src.read(1)  # u4 + u12, little-end
            byte2 = src.read(1)  # (second part)
            r.srcPos += 2

            dist = ((ord(byte1) & 0xF) << 8) | ord(byte2)  # -- u32  ((byte1 & 0xF) << 8) | byte2;
            copySource = dst.tell() - (dist + 1)  # -- u32 copySource = r.dstPos - (dist + 1);

            if copySource < 0:
                # MessageBox ("copySource < 0 ??? " + str(r.dstPos) +":"+ str(dist) +":"+ str(copySource))
                raise ValueError("ERROR")

            numBytes = ord(byte1) >> 4  # u32  byte1 >> 4

            if numBytes == 0:
                #if r.srcPos >= srcSize:
                #    return r
                numBytes = ord(src.read(1)) + 0x12
                r.srcPos += 1
            else:
                numBytes += 2

            # copy run
            dst.seek(copySource)
            temp = b''
            #if r.dstPos >= uncompressedSize:
            #    return r
            temp += dst.read(numBytes)
            r.dstPos += len(temp)
            dst.seek(0, 2)  # end
            dst.write(temp)

        # use next bit from "code" byte
        currCodeByte <<= 1  # currCodeByte <<= 1
    dst.seek(pos)
    return r


class CompressedStream:
    def __init__(self, fileobj):
        self.cf = fileobj
        self.cursor = ReturnValue
        self.tempFileName = os.path.splitext(self.cf.name)[0] + ".tempYaz0"
        newfile(self.tempFileName)
        self.cursor.dstPos = os.stat(self.tempFileName).st_size
        self.uf = open(self.tempFileName, 'rb+')

    def read(self, length):
        while self.cursor.dstPos - self.uf.tell() < length:
            if self.cursor.srcPos == 0:
                # in case of existing cached data not long enough, recreate it
                self.cursor.dstPos = 0
                self.uf.close()
                self.uf = open(self.tempFileName, 'wb+')
            try:
                self.cursor += decodeBlock(self.cf, self.uf)
            except Exception as err:
                print("EOF!!!", err)
        return self.uf.read(length)

    def close(self):
        self.cf.close()
        self.uf.close()

    def tell(self):
        return self.uf.tell()

    def seek(self, where, mode=0):
        if mode == 1:  # cursor
            while where > self.cursor.dstPos - self.uf.tell():
                self.cursor += decodeBlock(self.cf, self.uf)
            self.uf.seek(where, 1)

        elif mode == 0:  # from beginning
            while where > self.cursor.dstPos:
                self.cursor += decodeBlock(self.cf, self.uf)
            self.uf.seek(where)
        else:
            raise ValueError('plz impelment seek_2 4 copmresed strim')





class BinaryReader:
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
        if hasattr(self, "_tempFileName"):
            pass  # os.remove(self._tempFileName) # DEBUG: plz uncomment this when tests finished

    def DecodeYaz0(self, src, srcSize, dst, uncompressedSize):
        r = ReturnValue()  # current read/write positions

        validBitCount = 0  # u32 number of valid bits left in "code" byte
        currCodeByte = None  # u8
    
        while r.dstPos < uncompressedSize:
            # read new "code" byte if the current one is used up
            if validBitCount == 0:
                if r.srcPos >= srcSize:
                    return r
                currCodeByte = src[r.srcPos]
                r.srcPos += 1
                validBitCount = 8

            if (currCodeByte & 0x80) != 0:
                # straight copy
                if r.srcPos >= srcSize:
                    return r
                dst[r.dstPos] = src[r.srcPos]
                r.dstPos += 1
                r.srcPos += 1

            else:
                # RLE part
                if r.srcPos >= srcSize - 1:
                    return r
                byte1 = src[r.srcPos]  # u8
                byte2 = src[r.srcPos + 1]  # u8

                r.srcPos += 2


                dist = ((byte1 & 0xF)<<8) |  byte2 # -- u32  ((byte1 & 0xF) << 8) | byte2;
                copySource = r.dstPos - (dist + 1)  # -- u32 copySource = r.dstPos - (dist + 1);

                if copySource < 0:
                    # MessageBox ("copySource < 0 ??? " + str(r.dstPos) +":"+ str(dist) +":"+ str(copySource))
                    raise ValueError("ERROR")

                numBytes = byte1 >> 4  # u32  byte1 >> 4
              
                if numBytes == 0:
                    if r.srcPos >= srcSize:
                        return r
                    numBytes = src[r.srcPos] + 0x12
                    r.srcPos += 1
                else:
                  numBytes += 2
                
                # -- copy run
                for i in range(numBytes):
                    if r.dstPos >= uncompressedSize:
                        return r
                    dst[r.dstPos] = dst[copySource]
                    copySource += 1
                    r.dstPos += 1
        
            # use next bit from "code" byte
            currCodeByte <<= 1  # -- currCodeByte <<= 1
            validBitCount -= 1
        return r

    def ReadFixedLengthString(self, len):
        strRead = b""
        for _ in range(len):
            strRead += (self._f.read(1))
        return strRead.decode('cp1252')

    def ReadDWORD(self):
        w1 = ord(self._f.read(1))
        w2 = ord(self._f.read(1))
        w3 = ord(self._f.read(1))
        w4 = ord(self._f.read(1))
        d = (w1 << 24) | (w2 << 16)
        d |= w3 << 8
        d |= w4
        return d

    def Open(self, srcPath, compressed_stream=False):
        self._f = open(srcPath, "rb+")
        # --fseek self._f 0 seek_end
        # --self._size = ftell self._f
        self._f.seek(0)
        self.filesz = os.stat(self._f.fileno()).st_size
        if self._f is None:
            MessageBox("Unable to open file " + srcPath)
            raise ValueError("Unable to open file " + srcPath)

        tag = self.ReadFixedLengthString(4)
        # self._f.seek(0)
        if tag != "Yaz0":
            return  # not compressed, return file directly

        # yaz0-compressed file - uncompress as read, for optimisation, or decompress first
        elif compressed_stream == False:

            uncompressedSize = self.ReadDWORD()
            compressedSize = len(self._f.read()) - 8  # -- 16 byte header (including "Yaz0" and size)
            self._f.seek(16)  # -- seek to start of data

            srcData = array('B')  # [0]*compressedSize  # two arrays of u8s
            # --srcData[compressedSize] = 0 -- Pre-initialize array size
            dstData = array('B')  # [0]*uncompressedSize
            # --dstData[uncompressedSize] = 0 -- Pre-initialize array size

            for _ in range(uncompressedSize):
                dstData.append(0)
            for _ in range(compressedSize):
                srcData.append(ord(self._f.read(1)))
            self._f.close()

            r = self.DecodeYaz0(srcData, compressedSize, dstData, uncompressedSize)

            # --write decompressed data to a temporary file and
            # --return handle to this file
            self._tempFileName = os.path.splitext(srcPath)[0] + ".tempYaz0"

            self._f = open(self._tempFileName, "wb")  # -- creates file if not found
            for i in range(r.dstPos):
                self._f.write(dstData[i].to_bytes(1, 'big'))
            self._f.close()

            # -- open temp file for reading
            self._f = open(self._tempFileName, "rb+")
            self._f.seek(0)

        elif compressed_stream:
            self._f = CompressedStream(self._f)

    def is_eof(self):
        return self._f.tell() >= self.filesz
        # return self._f.tell()  >= self._size

    def SeekCur(self, offset):
        self._f.seek(self._f.tell() + offset)

    def SeekSet(self, position):
        self._f.seek(position)

    def Position(self):
        return self._f.tell()

    def GetByte(self):
        return ord(self._f.read(1))

    def ReadString(self, offset):
                
        t = self._f.tell()
        self._f.seek(offset)
        strRead = b""
        c = self._f.read(1)
        strRead += c
        while c != b'\x00':
            c = self._f.read(1)
            strRead += c
        strRead = strRead[:-1]  # strip final '\x00'
        self._f.seek(t)

        return strRead.decode('cp1252')

    def ReadWORD(self):
        w1 = ord(self._f.read(1))
        w2 = ord(self._f.read(1))
        w = (w1 << 8) | w2  # -- w = (w1 << 8) | w2;
        if w < 0:
            MessageBox("ReadWORD should be unsigned")
            raise ValueError("ReadWORD should be unsigned")
        return w

    def ReadStringTable(self, pos):
                
        oldPos = self.Position()
        self.SeekSet(pos)
        count = self.ReadWORD()         # -- orig = 35 read = 35. current pos = ok?
        unknown1 = self.ReadWORD()         # -- skip pad bytes
        result = []
        for _ in range(count):
            unknown = self.ReadWORD()
            stringOffset = self.ReadWORD()
            s = self.ReadString(pos + stringOffset)
            result.append(s)
        self.SeekSet(oldPos)
        return result

    def GetSHORT(self):
                
        signedValue = self.ReadWORD()         # -- unsigned
        negativeSign = signedValue // (2**15)

        if negativeSign :
            # -- flip bits and add 1
            # -- signedValue = bit.not signedValue // Dosn't work?
            signedValue = signedValue ^ 65535 # -- 65535 == all 1's
            signedValue += 1
            signedValue = signedValue * -1
        return signedValue

    def GetFloat(self):
        bits = self.ReadDWORD()
        s =-1
        if (bits >> 31) == 0 :
            s = 1
        e = (bits >> 23) & 0xff
        m = 0
        if e == 0 :
            m =(bits & 0x7fffff) << 1
        else:
            m = (bits & 0x7fffff) | 0x800000
        fx = s * m * (2**(e-150))
        return fx


