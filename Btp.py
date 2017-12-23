#! /usr/bin/python3
from .BinaryReader import BinaryReader
from .maxheader import MessageBox


class TptHeader:
    def LoadData(self, br):
        self.tag = br.ReadFixedLengthString(4)  # 'TPT1'
        self.sizeOfSection = br.ReadDWORD()
        self.unk = br.GetByte()  # loop type????
        self.pad = br.GetByte()
        self.unk2 = br.ReadWORD()  # (shortsPerMaterialAnim - no...sometimes 1 less (?))
        self.numMaterialAnims = br.ReadWORD()
        self.numShorts = br.ReadWORD()  # (should be product of previous shorts)
        self.offsetToMatAnims = br.ReadDWORD()  # for each materialAnim: u16 numSorts, u16 firstShort, u32 unk
        self.offsetToShorts = br.ReadDWORD()  # (shorts are texture indices)
        self.offsetToIndexTable = br.ReadDWORD()  # stores for every material to which mat3 index it belongs
        self.offsetToStringTable = br.ReadDWORD()


class MatAnim:
    def LoadData(self, br):
        self.count = br.ReadWORD()
        self.firstIndex = br.ReadWORD()
        self.unknown = br.ReadDWORD()


class BtpAnim:
    # <variable materialIndex>
    # <variable materialName>
    # <variable keyFrameIndexTable>
    def __init__(self):  # GENERATED!
        pass


class Btp:
    # <variable anims>
    # <function>

    # <function>

    def __init__(self):  # GENERATED!
        self.anims = []

    def LoadData(self, br):
        tpt1Offset = br.Position()
        # --size_t i;

        # -- read header
        header = TptHeader()
        header.LoadData(br)

        # -- read stringtable
        stringtable = br.ReadStringTable(tpt1Offset + header.offsetToStringTable)

        if len(stringtable) != header.numMaterialAnims:
            raise ValueError("Btp:LoadTPT1: number of strings (" +
                             str(len(stringtable))+") doesn't match number" \
                              "of animated materials (" +str(header.numMaterialAnims) + ")")

        # --read matAnimIndexToMat3Index table
        matAnimIndexToMat3Index = []
        # -- (h.numMaterialAnims);
        br.SeekSet(tpt1Offset + header.offsetToIndexTable)

        for _ in range(header.numMaterialAnims):
            matAnimIndexToMat3Index.append(br.ReadWORD())
        
        # -- messagebox (matAnimIndexToMat3Index as string)
        # --read shorts table
        shorts = []
        # -- (h.numShorts);
        br.SeekSet(tpt1Offset + header.offsetToShorts)

        for _ in range(header.numShorts):
            shorts.append(br.ReadWORD())

        # --read animations
        # -- btp.self.anims.resize(h.numMaterialAnims);
        br.SeekSet(tpt1Offset + header.offsetToMatAnims)

        for i in range(header.numMaterialAnims):
            # --messageBox stringtable
            mAnim = MatAnim()
            mAnim.LoadData(br)
            # --anims[i] = anim

            if mAnim.unknown != 0x00ffffff:
                raise ValueError(("btp: "+str(mAnim.unknown) +
                                 " instead of 0x00ffffff for mat anim nr "+str(i)))

            # --anims[i].indexToMat3Table = matAnimIndexToMat3Index[i]
            # --btp.anims[i].indices.resize(anim.count)
            # --messageBox (matAnimIndexToMat3Index as string)
            animaiton = ""
            for c in shorts:
                animaiton = animaiton + str(c) + " "

            anim = BtpAnim()
            anim.materialIndex = i
            anim.materialName = stringtable[i]
            anim.keyFrameIndexTable = shorts
            while len(self.anims) <= i:
                self.anims.append(None)
            self.anims[i] = anim
            # print(animaiton)
            # copy(shorts.begin() + anim.firstIndex, shorts.begin() + anim.firstIndex + anim.count,
            # btp.anims[i].indices.begin());

    def LoadBTP(self, filePath):
        br = BinaryReader()
        br.Open(filePath)
        br.SeekSet(0x20)

        pos = br.Position()
        tag = br.ReadFixedLengthString(4)
        size = br.ReadDWORD()
        # do
        # (
        # br.SeekCur size
        if size < 8:
            size = 8  # -- prevent endless loop on corrupt data
        br.SeekSet(pos)
        if br.is_eof():
            return  # Error

        if tag == "TPT1":
            self.LoadData(br)
        else:
            MessageBox("readBck(): Unsupported section " + tag)
            raise ValueError("readBck(): Unsupported section " + tag)
        br.SeekSet(pos)
        # ) while not EOF br._f
        br.Close()


