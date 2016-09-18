#! /usr/bin/python3
from .Matrix44 import *


class Evp1Header:
    """# <variable tag>
    # -- char[4]  'EVP1'
    # <variable sizeOfSection>
    # -- u32 
    # <variable count>
    # -- u16 
    # <variable pad>
    # -- u16 
    # --0 - count many bytes, each byte describes how many bones belong to this index
    # --1 - sum over all bytes in 0 many shorts (index into some joint stuff? into matrix table?)
    # --2 - bone weights table (as many floats as shorts in 1)
    # --3 - matrix table (matrix is 3x4 float array)
    # <variable offsets>
    # -- u32[4]
    # <function>"""

    def __init__(self):  # GENERATED!
        self.offsets= []

    def LoadData(self, br):
                
        self.tag = br.ReadFixedLengthString(4)
        self.sizeOfSection = br.ReadDWORD()
        self.count = br.ReadWORD()
        self.pad = br.ReadWORD()

        for _ in range(4):
            self.offsets.append(br.ReadDWORD())


class MultiMatrix:
    # <variable weights>
    # -- std::vector<float> ;
    # <variable indices>
    # -- std::vector<u16> indices; //indices into Evp1.matrices (?)
    def __init__(self):  # GENERATED!
        self.weights= []
        self.indices= []


class Evp1:
    # <variable weightedIndices>
    # -- std::vector<MultiMatrix> ;
    # <variable matrices>
    # -- std::vector<Matrix44f> ;
    # <function>

    def __init__(self):  # GENERATED!
        self.matrices= []
        self.weightedIndices= []

    def LoadData(self, br):

        evp1Offset = br.Position()

        header = Evp1Header()
        header.LoadData(br)

        # -- read counts array
        br.SeekSet (evp1Offset + header.offsets[0])  # TR: adapted
        counts = []
        # -- vector<int> counts(h.count);
        sum = 0
        for _ in range(header.count) :
            v = br.GetByte()  # -- u8 v; fread(&v, 1, 1, f);
            sum += v
            counts.append(v)

        self.weightedIndices = []         # --  dst.self.weightedIndices.resize(h.count);

        # -- read indices of weighted self.matrices
        br.SeekSet (evp1Offset + header.offsets[1])  # TR: adapted
        numMatrices = 0

        for i in range(header.count):
            self.weightedIndices.append(MultiMatrix())
            self.weightedIndices[i].indices = []  # -- weightedIndices[i].indices.resize(counts[i]);
            for j in range(counts[i]):
                d = br.ReadWORD()  # -- index to array (starts at one)
                self.weightedIndices[i].indices[j] = d
                numMatrices = max(numMatrices, (d+1))

        # -- read weights of weighted self.matrices
        br.SeekSet (evp1Offset + header.offsets[2])  # TR adapted

        for i in range(header.count):
            self.weightedIndices[i].weights = []  # -- .resize(counts[i]);
            for j in range(counts[i]):  # --(int j = 0; j < counts[i]; ++j)
                # error if f1 = br.GetFloat() used? can print value but assign = undefined
                fz = br.GetFloat()
                self.weightedIndices[i].weights[j] = fz


        # -- read self.matrices
        self.matrices = []
        # -- .resize(numMatrices);
        br.SeekSet (evp1Offset + header.offsets[3])  # TR adapted
        for i in range(numMatrices):
            self.matrices[i] = Matrix44()
            self.matrices[i].LoadIdentity()

            for j in range(3):
                for k in range(4):
                    self.matrices[i].m[j][k] = br.GetFloat()