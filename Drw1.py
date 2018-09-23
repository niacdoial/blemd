#! /usr/bin/python3
#     -- loads correctly: count=113, offsetToW=20, offsetToD=134 [20 + 113 = 133 (nextBit = offsetToD)]

from math import ceil


class Drw1Header:
    size = 20
    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        self.tag = br.ReadFixedLengthString(4)
        self.sizeOfSection = br.ReadDWORD()
        self.count = br.ReadWORD()
        self.pad = br.ReadWORD()
        # stores for each matrix if it's weighted (normal (0)/skinned (1) matrix types)
        self.offsetToIsWeighted = br.ReadDWORD()
        # for normal (0) matrices, this is an index into the global matrix
        # table (which stores a matrix for every joint). for skinned
        # matrices (1), I'm not yet totally sure how this works (but it's
        # probably an offset into the Evp1-array)
        self.offsetToData = br.ReadDWORD()

    def DumpData(self, bw):
        bw.WriteString('DRW1')
        bw.WriteDword(self.sizeOfSection)
        bw.WriteWord(self.count)
        bw.WriteWord(self.pad)
        bw.WriteDword(self.offsetToIsWeighted)
        bw.WriteDword(self.offsetToData)
  

class Drw1:
    def __init__(self):  # GENERATED!
        self.data= []
        self.isWeighted= []

    def LoadData(self, br):
                
        drw1Offset = br.Position()

        header = Drw1Header()
        header.LoadData(br)

        # -- read bool array
        self.isWeighted = [False] * header.count
        # -- self.isWeighted.resize(h.count);
        br.SeekSet(drw1Offset + header.offsetToIsWeighted)
        for i in range(header.count):
            v = br.GetByte()  # -- u8 v; fread(&v, 1, 1, f);

            if v == 0:
                pass
                # self.isWeighted[i] = False
                # already done when initialized
            elif v == 1:
                self.isWeighted[i] = True
            else:
                raise ValueError("drw1: unexpected value in isWeighted array: " + str(v))

        # -- read self.data array
        self.data = [0] * header.count
        # -- dst.self.data.resize(h.count);
        br.SeekSet(drw1Offset + header.offsetToData)
        for i in range(header.count):
            self.data[i] = br.ReadWORD()

    def DumpData(self, bw):

        drw1Offset = bw.Position()

        header = Drw1Header()
        header.count = len(self.data)
        if len(self.isWeighted) != header.count:
            raise ValueError('Broken Drw1 section')
        header.pad = 0xff
        header.offsetToIsWeighted = bw.addPadding(Drw1Header.size)
        header.offsetToData = header.offsetToIsWeighted + header.count
        header.sizeOfSection = bw.addPadding(header.offsetToData + 2*header.count)

        header.DumpData(bw)

        bw.writePadding(header.offsetToIsWeighted - Drw1Header.size)

        for bool in self.isWeighted:
            bw.WriteByte(int(bool))

        for index in self.data:
            bw.WriteWord(index)

        bw.writePadding(drw1Offset + header.sizeOfSection - bw.Position())
