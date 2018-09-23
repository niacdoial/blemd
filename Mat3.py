#! /usr/bin/python3


class Mat3Header:
    def __init__(self):  # GENERATED!
        self.offsets= []

    def LoadData(self, br):
        self.tag = br.ReadFixedLengthString(4)
        self.sizeOfSection = br.ReadDWORD()
        self.count = br.ReadWORD()
        self.pad = br.ReadWORD()
        # 0 - MatInit array
        # 1 - array of shorts with 0, 1, 2, ..., count (nearly...sometimes small deviations) -> index into offset[0]
        # 2 - string table
        # 3 - divisible by Mat3Header.count - so the Mat3Entries are stored here
        # 15 - index to texture table?
        for _ in range(30):
            self.offsets.append(br.ReadDWORD())


class MatInit:
    def __init__(self):  # GENERATED!
        self.unknown1 = []
        self.texStages = []
        self.unknown2 = []

    def LoadData(self, br):
        for _ in range(132):
            self.unknown1.append(br.GetByte())
        for _ in range(8):
            self.texStages.append(br.ReadWORD())
        u2Count = 332 - 132 - 8*2

        for _ in range(u2Count):
            self.unknown2.append(br.GetByte())

class MatEntry:
    """
    # -- u8[8];
    # -- 0, 1 - index into color1 (e.g. map_delfino3.bmd)
    # -- 6, 7 - index into color2 (e.g. mo.bdl)
    # -- 2, 3, 4, 5 - index into chanControls
    # <variable chanControls>
    # -- u16[8];
    # <variable color1>
    # --u16[2];
    # <variable chanControls>
    # -- u16[4];
    # <variable color2>
    # --u16[2]; //not in MAT2 block
    # <variable lightList>
    # --lights u16[8]; //all 0xffff most of the time, not in MAT2 block
    # <variable texGenInfo>
    # --u16[8];
    # <variable texGenInfo2>
    # --u16[8];
    # <variable texMatrices>
    # --u16[10]; //direct index
    # <variable dttMatrices>
    # --u16[20]; //?? (I have no idea what dtt matrices do...)
    # <variable texStages>
    # --u16[8]; //indices into textureTable
    # --constColor (GX_TEV_KCSEL_K0-3)
    # <variable color3>
    # --u16[4]; //direct index
    # <variable constColorSel>
    # --u8[16]; //0x0c most of the time (const color sel, GX_TEV_KCSEL_*)
    # <variable constAlphaSel>
    # --u8[16]; //0x1c most of the time (const alpha sel, GX_TEV_KASEL_*)
    # <variable tevOrderInfo>
    # --u16[16]; //direct index
    # --this is to be loaded into
    # --GX_CC_CPREV - GX_CC_A2??
    # <variable colorS10>
    # --u16[4]; //direct index
    # --these two always contained the same data in all files
    # --I've seen...
    # <variable tevStageInfo>
    # --u16[16]; //direct index
    # <variable tevSwapModeInfo>
    # --u16[16]; //direct index
    # <variable tevSwapModeTable>
    # --u16[4];
    # <variable unknown6>
    # --u16[12]; //vf_118 has a float in here (but only in one block...)
    # --f32 unknown6[6];
    # --0 - fog index (vf_117.bdl)
    # --1 - alphaComp (vf_117.bdl, yoshi.bmd)
    # --2 - blendInfo (cl.bdl)
    # --3 - nbt scale?
    # <variable indices2>
    # --u16[4];
    # <function>"""

    def __init__(self):  # GENERATED!
        # (0 - possible values: 1, 4, 253[1: draw on tree down, 4 on up??])
        #    - related to transparency sorting
        #  1 - index into cullModes
        #  2 - index into numChans
        #  3 - index into texgen counts
        #  4 - index into tev counts
        #  5 - index into matData6 (?)
        #  6 - index into zModes? (quite sure)
        #  7 - index into matData7 (?)
        #  //(still missing stuff: isDirect, zCompLoc,
        #  //enable/disable blend alphatest depthtest, ...)

        self.colorS10= []
        self.tevOrderInfo= []
        self.texStages= []
        self.color2= []
        self.tevStageInfo= []
        self.dttMatrices= []
        self.indices2= []
        self.unknown6= []
        # 0 - fog index (vf_117.bdl)
        # 1 - alphaComp (vf_117.bdl, yoshi.bmd)
        # 2 - blendInfo (cl.bdl)
        # 3 - nbt scale?
        self.constAlphaSel= []
        self.unk= []
            # 0, 1 - index into color1 (e.g. map_delfino3.bmd)
            # 6, 7 - index into color2 (e.g. mo.bdl)
            # 2, 3, 4, 5 - index into chanControls
        self.color3= []
        self.texGenInfo2= []
        self.constColorSel= []
        self.color1= []
        self.chanControls= []
        self.tevSwapModeTable= []
        self.texMatrices= []
        self.texGenInfo= []
        self.lightList= []
        self.tevSwapModeInfo= []
        
        self.material = None  # stores the outputted blender material, that could be used several times

    def LoadData(self, br, isMat2):
        for _ in range(8): self.unk.append(br.GetByte())
        self.flag=self.unk[0]
        for _ in range(2): self.color1.append(br.ReadWORD())
        for _ in range(4): self.chanControls.append(br.ReadWORD())
        # --these two fields are only in mat3 headers, not in mat2

        if not isMat2:
            for _ in range(2):
                self.color2.append(br.ReadWORD())
        else :
            raise ValueError("isMat2 header NYI") # memset(init.self.color2, 0xff, 2*2);

        if not isMat2 :
            for _ in range(8) :
                self.lightList.append(br.ReadWORD())
        else:
            raise ValueError("isMat2 header NYI")  # memset(init.lights, 0xff, 8*2);

        for _ in range(8):       self.texGenInfo.append(br.ReadWORD())
        for _ in range(8):      self.texGenInfo2.append(br.ReadWORD())
        for _ in range(10):      self.texMatrices.append(br.ReadWORD())
        for _ in range(20):      self.dttMatrices.append(br.ReadWORD())
        for _ in range(8):        self.texStages.append(br.ReadWORD())
        for _ in range(4):           self.color3.append(br.ReadWORD())
        for _ in range(16):    self.constColorSel.append(br.GetByte())
        for _ in range(16):    self.constAlphaSel.append(br.GetByte())
        for _ in range(16):     self.tevOrderInfo.append(br.ReadWORD())
        for _ in range(4):         self.colorS10.append(br.ReadWORD())
        for _ in range(16):     self.tevStageInfo.append(br.ReadWORD())
        for _ in range(16):  self.tevSwapModeInfo.append(br.ReadWORD())
        for _ in range(4): self.tevSwapModeTable.append(br.ReadWORD())
        for _ in range(12):         self.unknown6.append(br.ReadWORD())
        for _ in range(4):         self.indices2.append(br.ReadWORD())


class Mat3:
    def __init__(self):  # GENERATED!
        # temporary, maps mat index to tex index
        self.texTable= []
        self.materials= []
        # MatEntry array
        self.texStageIndexToTextureIndex= []
        # _texStageIndexToTextureIndex, used by btp
        self.indexToMatIndex= []

    def LoadData(self, br):

        # -- "Mat3 section support is very incomplete"

        mat3Offset = br.Position()

        # -- read header
        h = Mat3Header()
        h.LoadData(br)

        self.isMat2 = (h.tag == "MAT2")

        self.stringtable = br.ReadStringTable(mat3Offset + h.offsets[2])  # fixed
        #  -- readStringtable(mat3Offset + h.offsets[2], f, self.stringtable);

        if h.count != len(self.stringtable):
            raise ValueError("mat3: number of strings (%d) doesn't match number of elements (%d)")

        # -- compute max length of each subsection
        lengths = []         # -- vector<int> lengths(30);

        for i in range(30):
            length = 0
            if h.offsets[i] != 0:

                next = h.sizeOfSection
                for j in range(i + 1, 30):
                    if h.offsets[j] != 0:
                        next = h.offsets[j]
                        break
                length = next - h.offsets[i]

                while len(lengths) <= i:
                    lengths.append(None)
                lengths[i] = length
                if i == 2:  # fixed
                    pass
                    # -- assert(length%h.count == 0); //violated by luigi's mansion files
                    # -- assert(length/h.count == 312); //violated by quite a few files


        # ------------------
        br.SeekSet(mat3Offset + h.offsets[0])  # corrected     # -- offset[0] (MatEntries)
        self.materials = [None] * h.count
        # -- vector<int> indexToInitData(h.count); ' self.indexToMatIndex

        for i in range(h.count):
            m = MatEntry()
            m.LoadData(br, self.isMat2)
            self.materials[i] = m
        # ------------------
        br.SeekSet(mat3Offset + h.offsets[1])  # corrected  # -- offset[1] (indirection table from indices to init data indices)
        maxIndex = 0
        indexToInitData = []
        # -- vector<int> indexToInitData(h.count); ' self.indexToMatIndex

        for _ in range(h.count):
            bla = br.ReadWORD()
            if bla > maxIndex:
                maxIndex = bla
            indexToInitData.append(bla)
            self.indexToMatIndex.append(bla)

        # --self.indexToMatIndex = indexToInitData
        br.SeekSet(mat3Offset + h.offsets[0])  # corrected
        initData = []
        # -- vector<bmd::MatInit> initData(maxIndex + 1)

        for _ in range(maxIndex +1):  #UNcorrected deliberately  # for(i = 0; i <= maxIndex; ++i)
            init = MatInit()
            init.LoadData(br)
            initData.append(init)

        # -- read self.texTable
        br.SeekSet(mat3Offset + h.offsets[15])  # corrected  # --  fseek(f, mat3Offset + h.offsets[15], SEEK_SET);

        texLength = lengths[15]  # corrected
        tempTexTable = []
        # -- vector<int> self.texTable(texLength/2);  self.texStageIndexToTextureIndex
        maxTexIndex = 0

        for _ in range(texLength//2):
            index = br.ReadWORD()
            self.texTable.append(index)
            self.texStageIndexToTextureIndex.append(index)



