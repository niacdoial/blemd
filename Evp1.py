#! /usr/bin/python3
from .Matrix44 import *
from mathutils import Matrix
from math import ceil
import math

class Evp1Header:
    size = 28

    def __init__(self):  # GENERATED!
        self.offsets = [0, 0, 0, 0]

    def LoadData(self, br):

        self.tag = br.ReadFixedLengthString(4)
        self.sizeOfSection = br.ReadDWORD()
        self.count = br.ReadWORD()
        self.pad = br.ReadWORD()
        # 0 - count many bytes, each byte describes how many bones belong to this index
        # 1 - sum over all bytes in 0 many shorts (index into some joint stuff? into matrix table?)
        # 2 - bone weights table (as many floats as shorts in 1)
        # 3 - matrix table (matrix is 3x4 float array)

        for i in range(4):
            self.offsets[i] = br.ReadDWORD()

    def DumpData(self, bw):

        bw.WriteString('EVP1')
        bw.WriteDword(self.sizeOfSection)
        bw.WriteWord(self.count)
        bw.WriteWord(self.pad)
        # 0 - count many bytes, each byte describes how many bones belong to this index
        # 1 - sum over all bytes in 0 many shorts (index into some joint stuff? into matrix table?)
        # 2 - bone weights table (as many floats as shorts in 1)
        # 3 - matrix table (matrix is 3x4 float array)

        for i in range(4):
            bw.WriteDword(self.offsets[i])


class MultiMatrix:
    def __init__(self):  # GENERATED!
        self.weights = []
        self.indices = []  # indices into Evp1.matrices (?)


class Evp1:
    def __init__(self):  # GENERATED!
        self.matrices = []
        self.weightedIndices = []

    def LoadData(self, br):

        evp1Offset = br.Position()

        header = Evp1Header()
        header.LoadData(br)

        # -- read counts array
        br.SeekSet(evp1Offset + header.offsets[0])
        counts = [0] * header.count
        sum = 0
        for i in range(header.count):
            v = br.GetByte()
            sum += v
            counts[i] = v

        self.weightedIndices = []  # size : h.count

        # -- read indices of weighted self.matrices
        br.SeekSet(evp1Offset + header.offsets[1])
        numMatrices = 0

        for i in range(header.count):
            self.weightedIndices.append(MultiMatrix())
            self.weightedIndices[i].indices = [0] * counts[i]
            for j in range(counts[i]):
                d = br.ReadWORD()  # index to array (starts at one)
                self.weightedIndices[i].indices[j] = d
                numMatrices = max(numMatrices, d+1)  # XCX does the '+1' skrew it up?
                # XCX(probably not, it might just create extra, unused, junk, data)

        # -- read weights of weighted self.matrices
        br.SeekSet(evp1Offset + header.offsets[2])

        for i in range(header.count):
            self.weightedIndices[i].weights = [0] * counts[i]
            for j in range(counts[i]):
                fz = br.GetFloat()
                self.weightedIndices[i].weights[j] = fz


        # -- read matrices
        self.matrices = []  # size: numMatrices
        br.SeekSet(evp1Offset + header.offsets[3])
        self.matrices = [None] * numMatrices
        for i in range(numMatrices):
            self.matrices[i] = Matrix.Identity(4)
            for j in range(3):
                for k in range(4):
                    self.matrices[i][j][k] = br.GetFloat()

    def DumpData(self, bw):
        evp1Offset = bw.Position()

        header = Evp1Header()
        numMatrices = len(self.matrices)
        header.count = len(self.weightedIndices)
        counts = [len(self.weightedIndices[i].indices)
                      for i in range(header.count)]
        countsum = sum(counts)
        header.pad = 0xffff

        header.offsets[0] = bw.addPadding(Evp1Header.size)
        header.offsets[1] = header.offsets[0] + header.count
        header.offsets[2] = header.offsets[1] + 2 * countsum
        header.offsets[3] = header.offsets[2] + 4 * countsum
        header.sizeOfSection = header.offsets[3] + numMatrices * 12 * 4
        header.sizeOfSection = bw.addPadding(header.sizeOfSection)

        header.DumpData(bw)

        bw.WritePadding(header.offsets[0] - Evp1Header.size)
        # read counts array
        # bw.SeekSet(evp1Offset + header.offsets[0])

        for i in range(header.count):
            bw.WriteByte(counts[i])


        # -- read indices of weighted self.matrices
        # bw.SeekSet(evp1Offset + header.offsets[1])

        for i in range(header.count):
            for j in range(counts[i]):
                bw.WriteWord(self.weightedIndices[i].indices[j])

        # read weights of weighted matrices
        # bw.SeekSet(evp1Offset + header.offsets[2])

        for i in range(header.count):
            for j in range(counts[i]):
                bw.WriteFloat(self.weightedIndices[i].weights[j])


        # write matrices
        # bw.SeekSet(evp1Offset + header.offsets[3])
        for i in range(numMatrices):
            for j in range(3):
                for k in range(4):
                    bw.WriteFloat(self.matrices[i][j][k])

        bw.WritePadding(evp1Offset + header.sizeofsection - bw.Position())