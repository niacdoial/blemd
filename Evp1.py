#! /usr/bin/python3
from .Matrix44 import *
from mathutils import Matrix

class Evp1Header:

    def __init__(self):  # GENERATED!
        self.offsets = []

    def LoadData(self, br):
                
        self.tag = br.ReadFixedLengthString(4)
        self.sizeOfSection = br.ReadDWORD()
        self.count = br.ReadWORD()
        self.pad = br.ReadWORD()
        # 0 - count many bytes, each byte describes how many bones belong to this index
        # 1 - sum over all bytes in 0 many shorts (index into some joint stuff? into matrix table?)
        # 2 - bone weights table (as many floats as shorts in 1)
        # 3 - matrix table (matrix is 3x4 float array)

        for _ in range(4):
            self.offsets.append(br.ReadDWORD())


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
        br.SeekSet(evp1Offset + header.offsets[0])  # TR: adapted
        counts = []
        # -- vector<int> counts(h.count);
        sum = 0
        for _ in range(header.count):
            v = br.GetByte()  # -- u8 v; fread(&v, 1, 1, f);
            sum += v
            counts.append(v)

        self.weightedIndices = []         # --  dst.self.weightedIndices.resize(h.count);

        # -- read indices of weighted self.matrices
        br.SeekSet(evp1Offset + header.offsets[1])  # TR: adapted
        numMatrices = 0

        for i in range(header.count):
            self.weightedIndices.append(MultiMatrix())
            self.weightedIndices[i].indices = []  # -- weightedIndices[i].indices.resize(counts[i]);
            for j in range(counts[i]):
                d = br.ReadWORD()  # -- index to array (starts at one)
                while len(self.weightedIndices[i].indices) <= j:
                    self.weightedIndices[i].indices.append(0)
                self.weightedIndices[i].indices[j] = d
                numMatrices = max(numMatrices, d+1)  # XCX does the '+1' skrew it up?
                # XCX(probably not, it might just create extra, unused, junk, data)

        # -- read weights of weighted self.matrices
        br.SeekSet(evp1Offset + header.offsets[2])  # TR adapted

        for i in range(header.count):
            self.weightedIndices[i].weights = []  # -- .resize(counts[i]);
            for j in range(counts[i]):  # --(int j = 0; j < counts[i]; ++j)
                # error if f1 = br.GetFloat() used? can print value but assign = undefined
                fz = br.GetFloat()
                while len(self.weightedIndices[i].weights) <= j:
                    self.weightedIndices[i].weights.append(0)
                self.weightedIndices[i].weights[j] = fz


        # -- read matrices
        self.matrices = []
        # -- .resize(numMatrices);
        br.SeekSet(evp1Offset + header.offsets[3])  # TR adapted
        self.matrices = [None] * numMatrices
        for i in range(numMatrices):
            self.matrices[i] = Matrix.Identity(4)
            for j in range(3):
                for k in range(4):
                    self.matrices[i][j][k] = br.GetFloat()