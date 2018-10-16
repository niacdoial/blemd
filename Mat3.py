import sys
import bpy
import logging
log = logging.getLogger('bpy.ops.import_mesh.bmd.matv2')


def arrayresize(L, s):
    if len(L) >= s:
        return
    else:
        if type(s) is float and int(s) == s:
            s=int(s)
        L += [None]*(s-len(L))


class Mat3Header:
    def __init__(self):
        self.tag = ""  # //'MAT3' or 'MAT2'
        self.sizeOfSection = 0  # U32
        self.count = 0  # U16s
        self.pad = 0
        # Left-indented stuff not completely known

        # The entries marked with * are missing in MAT2 blocks
        # (ie. in a MAT2 block entry 3 is cull mode etc.), the
        # Mat2Header is 12 bytes shorter because of this


        # 0 - MatEntry array (indexed by next array)
        # 1 - indexToMatEntryIndex (count many)
        # 2 - string table
        # *3 - MatIndirectTexturingEntry array, count many for all files i've seen
        # 4 - cull mode                               (indexed by MatEntry.unk[1])
        # 5 - color1 (rgba8) (amb color??)
        # 6 - numChans (?)                              (indexed by MatEntry.unk[2])
        # 7 - colorChanInfo
        # *8 - color2 (rgba8) (mat color??)
        # *9 - light
        # 10 - texgen counts (-> vr_back_cloud.bdl)   (indexed by MatEntry.unk[3])
        # 11 - TexGen
        # 12 - TexGen2
        # 13 - TexMtxInfo
        # 14 - TexMtxInfo2
        # 15 - index to texture table
        # 16 - TevOrderInfo array
        # 17 - colorS10 (rgba16) (prev, c0-c2)
        # 18 - color3 (rgba8) (konst0-3)
        # 19 - tev counts                             (indexed by MatEntry.unk[4])
        # 20 - tev stages
        # 21 - tev swap mode info
        # 22 - tev swap mode table
        # 23 - fog info            (indexed by MatEntry.indices2[0])
        # 24 - alphacomp array     (indexed by MatEntry.indices2[1])
        # 25 - blend info array    (indexed by MatEntry.indices2[2])
        # 26 - zmode info array                       (indexed by MatEntry.unk[6])

        # The following fields are only here for MAT3 blocks, not for MAT2

        # 27 - matData6
        # 28 - matData7
        # 30 - NBTScale              (indexed by MatEntry.indices2[3])
        self.offsets = [0] * 30  # U32

    def LoadData(self, f):
        self.tag = f.ReadFixedLengthString(4)
        self.sizeOfSection = f.ReadDWORD()
        self.count = f.ReadWORD()
        self.pad = f.ReadWORD()
        for i in range(30):
            self.offsets[i] = f.ReadDWORD()

        if self.tag == "MAT2":
            # //check if this is a MAT3 section (most of the time) or a MAT2 section
            # //(TODO: probably there's also a MAT1 section - find one...)

            # //if this is a mat2 section, convert header to a mat3 header
            for j in range(29, 0, -1):
                t = 0
                if j < 3:
                    t = self.offsets[j]
                elif (j == 3 or j == 8 or j == 9):
                    t = 0
                elif (j < 8):
                    t = self.offsets[j - 1]
                else:
                    t = self.offsets[j - 3]
                self.offsets[j] = t


class MColor:
    def __init__(self, rr=0, gg=0, bb=0, aa=1):
        self.r = rr  # u8 or s16
        self.g = gg
        self.b = bb
        self.a = aa
    
    def LoadData(self, br):
        self.r = br.GetByte()
        self.g = br.GetByte()
        self.b = br.GetByte()
        self.a = br.GetByte()
        
    def LoadDataS(self, br):
        self.r = br.GetSHORT()
        self.g = br.GetSHORT()
        self.b = br.GetSHORT()
        self.a = br.GetSHORT()


class ColorChanInfo:
    def __init__(self):
        # //this is wrong, the third element is sometimes 3 or 4,
        # //so perhaps the third argument is the channel, but
        # //then the order of the other fields may be different too

        # //perhaps no "channel" but two pad bytes at the end?

        # //observation:
        # //the second byte is always 0 if the model has not vertex colors,
        # //sometimes 1 otherwise
        disabled1 = """
        u8 channel; // /* chan id */
        u8 enable; //0/1
        u8 ambSrc; //GX_SRC_REG, GX_SRC_VTX (0, 1) (??)
        u8 matSrc; //GX_SRC_REG, GX_SRC_VTX (0, 1) (??)
        u8 litMask; //GL_LIGHT* ??
        u8 diffuseAttenuationFunc; //GX_DF_NONE, GX_DF_SIGNED, GX_DF_CLAMP (0, 1, 2) (??)
        u8 attenuationFracFunc; //GX_AF_SPEC, GX_AF_SPOT, GX_AUF_NONE (0, 1, 2) (??)
        u8 pad;"""
        disabled2 = """
        # //this could be right: (no)
        u8 unk1;
        u8 matColorSource;
        u8 unk2;
        u8 attenuationFracFunc; //quite sure
        u8 diffuseAttenuationFunc; //quite sure
        u8 unk3;
        u8 pad[2];

        #//(lit mask is implied by index position in array in MatEntry)"""

        # //I think I finally got it:
        # //(enable = litMask != 0...)# //not sure if this is right
        self.ambColorSource = 0  # U8s
        self.matColorSource = 0
        self.litMask = 0
        self.attenuationFracFunc = 0
        self.diffuseAttenuationFunc = 0
    
    def LoadData(self, br):
        self.ambColorSource = br.GetByte()
        self.matColorSource = br.GetByte()
        self.litMask = br.GetByte()
        self.attenuationFracFunc = br.GetByte()
        self.diffuseAttenuationFunc = br.GetByte()
        self.unk = br.GetByte()
        self.pad = [br.GetByte(), br.GetByte()]


class TexGenInfo:
    def __init__(self):
        self.texGenType = 0  # U8s
        self.texGenSrc = 0
        self.matrix = 0
        self.pad = 0
    
    def LoadData(self, br):
        self.texGenType = br.GetByte()
        self.texGenSrc = br.GetByte()
        self.matrix = br.GetByte()
        self.pad = br.GetByte()


class TexMtxInfo:
    def __init__(self):
        self.scaleCenterX = 0.  # floats
        self.scaleCenterY = 0.
        self.scaleU = 0.
        self.scaleV = 0.
        self.f2 = [0,0]
        self.f3 = [0]*16
    def LoadData(self, br):
        self.unk = br.ReadWORD()
        self.pad = br.ReadWORD()  # 0xffff most of the time
        self.scaleCenterX = br.GetFloat()
        self.scaleCenterY = br.GetFloat()
        self.unk2 = br.GetFloat()  # rotate u, v ?????
        self.scaleU = br.GetFloat()
        self.scaleV = br.GetFloat()
        self.unk3 = br.ReadWORD()  # (originally pad2)
        self.pad2 = br.ReadWORD()
        # Mipmap switching ?
        # Interpolation method ?
        for j in range(2):
            self.f2[j] = br.GetFloat()
        for j in range(16):  # //nearly always an 4x4 identity matrix
            self.f3[j] = br.GetFloat()

            
class TevStageInfo:
    def __init__(self):
        # //GX_SetTevColorIn() arguments
        self.colorIn = [0, 0, 0, 0]  # U8s //GX_CC_*

        # //GX_SetTevColorOp() arguments
        self.colorOp = 0  # U8s
        self.colorBias = 0
        self.colorScale = 0
        self.colorClamp = 0
        self.colorRegId = 0

        # //GX_SetTevAlphaIn() arguments
        self.alphaIn = [0, 0, 0, 0]  # U8s //GC_CA_*

        # //GX_SetTevAlphaOp() arguments
        self.alphaOp = 0
        self.alphaBias = 0
        self.alphaScale = 0
        self.alphaClamp = 0
        self.alphaRegId = 0

    def LoadData(self, br):
        self.unk = br.GetByte()
        for j in range(4):
            self.colorIn[j] = br.GetByte()
        self.colorOp = br.GetByte()
        self.colorBias = br.GetByte()
        self.colorScale = br.GetByte()
        self.colorClamp = br.GetByte()
        self.colorRegId = br.GetByte()

        for j in range(4):
            self.alphaIn[j] = br.GetByte()
        self.alphaOp = br.GetByte()
        self.alphaBias = br.GetByte()
        self.alphaScale = br.GetByte()
        self.alphaClamp = br.GetByte()
        self.alphaRegId = br.GetByte()

        self.unk2 = br.GetByte()

      
class TevOrderInfo:
    def __init__(self):
        self.texCoordId = 0  # U8s
        self.texMap = 0
        self.chanId = 0
        self.pad = 0
    
    def LoadData(self, br):
        self.texCoordId = br.GetByte()
        self.texMap = br.GetByte()
        self.chanId = br.GetByte()
        self.pad = br.GetByte()


class TevSwapModeInfo:
    def __init__(self):
        self.rasSel = 0  # U8s
        self.texSel = 0
        self.pad = [0]*2


TevSwapModeTable = MColor

class MatIndirectTexturingEntry:
    class unk2C:
        def __init__(self):
            self.f = [.5, 0., 0., 0., .5, 0.]  # floats # //3x2 matrix? texmatrix?
            self.b = [1, 0xff, 0xff, 0xff]  # U8s

        def __eq__(self, other):
            return self.f == other.f and \
                   self.b == other.b

    class unk4C:
        def __init__(self):
            # //the first 9 bytes of this array are probably the arguments to
			# //GX_SetTevIndirect (index is the first argument), the
			# //other three bytes are padding
            self.unk = [0, 0, 0, 0, 0x00ff, 0xffff]  # U16s

        def __eq__(self, other):
            return self.unk == other.unk

    def __init__(self):
        # //size = 312 = 0x138
        # //(not always...see default.bmd <- but there 3 and 2 point to the same
        # //location in file (string table). but default.bmd is the only file i know
        # //where number of ind tex entries doesn't match number of mats)

        # //this could be arguments to GX_SetIndTexOrder() plus some dummy values
        self.unk = [0] + [0xffff] * 9  # U16s

        self.unk2 = [self.unk2C() for _ in range(3)]
        # //probably the arguments to GX_SetIndTexOrder()
        # //or GX_SetIndtexCoordScale() (index is first param)
        self.unk3 = [0x0000ffff] * 4  # U32s

        self.unk4 = [self.unk4C() for _ in range(16)]

    def __eq__(self, other):
        return (self.unk == other.unk) and \
               (self.unk2 == other.unk2) and \
               (self.unk3 == other.unk3) and \
               (self.unk4 == other.unk4)

    def LoadData(self, br):
        k = 0
        m = 0
        for k in range(10):
            self.unk[k] = br.ReadWORD()
        for k in range(3):
            for m in range(6):
                self.unk2[k].f[m] = br.GetFloat()
            for m in range(4):
                self.unk2[k].b[m] = br.GetByte()

        for k in range(4):
            self.unk3[k] = br.ReadDWORD()
        for k in range(16):
            for m in range(6):
                self.unk4[k].unk[m] = br.ReadWORD()

                
class AlphaCompare:
    def __init__(self):
        self.comp0 = 0  # U8s
        self.ref0 = 0
        self.alphaOp = 0
        self.comp1 = 0
        self.ref1 = 0
        self.pad = [0] * 3  # //??
    
    def LoadData(self, br):
        self.comp0 = br.GetByte()
        self.ref0 = br.GetByte()
        self.alphaOp = br.GetByte()
        self.comp1 = br.GetByte()
        self.ref1 = br.GetByte()
        self.pad = [br.GetByte(),
                     br.GetByte(),
                     br.GetByte()]
        

class BlendInfo:
    def __init__(self):
        self.blendMode = 0  # U8s
        self.srcFactor = 0
        self.dstFactor = 0
        self.logicOp = 0
        

class ZMode:
    def __init__(self):
        self.enable = False
        self.zFunc = 0  # U8
        self.enableUpdate = False
        self.enable_raw = 0  # U8s
        self.enableUpdate_raw = 0
        self.pad = 0  # //(ref val?)
    
    def LoadData(self, br):
        self.enable_raw = br.GetByte()
        self.enable = self.enable_raw != 0
        self.zFunc = br.GetByte()
        self.enableUpdate_raw = br.GetByte()
        self.enableUpdate = self.enableUpdate_raw != 0
        self.pad = br.GetByte()

        
class FogInfo:
    def __init__(self):
        self.fogType = 0  # U8s
        self.enable = 0
        self.center = 0  # U16

        self.startZ = 0.  # f32s
        self.endZ = 0.
        self.nearZ = 0.
        self.farZ = 0.

        self.color = None  # //Mcolor
        self.adjTable = [0] * 10  # //U16s ????

        
class MaterialBase:
    def __init__(self):
        self.flag = 0  # U8s
        self.cullIndex = 0
        self.numChansIndex = 0
        self.texGenCountIndex = 0
        self.tevCountIndex = 0

        self.zModeIndex = 0

        self.color1 = [0] * 2  # U16s
        self.chanControls = [0] * 4
        self.color2 = [0] * 2

        self.lights = [0] * 8
        self.texGenInfos = [0] * 8
        self.texGenInfos2 = [0] * 8

        self.texMtxInfos = [0] * 10
        self.dttMtxInfos = [0] * 20

        self.texStages = [0] * 8
        # //constColor (GX_TEV_KCSEL_K0-3)
        self.color3 = [0] * 4
        self.constColorSel = [0] * 16  # U8s  # //0x0c most of the time (const color sel, GX_TEV_KCSEL_*)
        self.constAlphaSel = [0] * 16  # //0x1c most of the time (const alpha sel, GX_TEV_KASEL_*)
        self.tevOrderInfo = [0] * 16  # u16s
        # //this is to be loaded into
        # //GX_CC_CPREV - GX_CC_A2??
        self.colorS10 = [0] * 4  # U16s
        self.tevStageInfo = [0] * 16
        self.tevSwapModeInfo = [0] * 16
        self.tevSwapModeTable = [0] * 4

        self.alphaCompIndex = [0] * 4
        self.blendIndex = [0] * 4

        self.unknown6 = [0] * 12
        self.indices2 = [0] * 4
        
        self.material = None  # cached result to avoid unnecessary calculations

    def LoadData(self, br, isMat2):
        # possible values: 1, 4, 253 [1: draw on tree down, 4 on up??]
        # related to transparency sorting
        self.flag = br.GetByte()
        self.cullIndex = br.GetByte()  # index into cullModes
        self.numChansIndex = br.GetByte()
        self.texGenCountIndex = br.GetByte()
        self.tevCountIndex = br.GetByte()
        self.unk1 = br.GetByte()  # index into matData6 (?)
        self.zModeIndex = br.GetByte()
        self.unk2 = br.GetByte()  # index into matData7 (?)
        
        # (still missing stuff: isDirect, zCompLoc,
        # enable/disable blend alphatest depthtest, ...)

        for j in range(2):
            self.color1[j] = br.ReadWORD()
        for j in range(4):
            self.chanControls[j] = br.ReadWORD()
        if not isMat2:
            for j in range(2):
                self.color2[j] = br.ReadWORD()
            for j in range(8):
                # all 0xffff most of the time, not in MAT2 block
                self.lights[j] = br.ReadWORD()
        else:
            for j in range(2):
                self.color2[j] = 0xffff
            for j in range(8):
                self.lights[j] = 0xffff
        for j in range(8):  # 'TexGenInfo'
            self.texGenInfos[j] = br.ReadWORD()
        for j in range(8):
            self.texGenInfos2[j] = br.ReadWORD()
        for j in range(10):  # direct index,  'texMatrices'
            self.texMtxInfos[j] = br.ReadWORD()
        for j in range(20):  # ?? (I have no idea what dtt matrices do...)
            self.dttMtxInfos[j] = br.ReadWORD()  # 'dttMatrices'
        for j in range(8):  # indices into textureTable
            self.texStages[j] = br.ReadWORD()
            
        # constColor (GX_TEV_KCSEL_K0-3)
        for j in range(4):  # direct index
            self.color3[j] = br.ReadWORD()
        for j in range(16):  # U8s  # 0x0c most of the time (const color sel, GX_TEV_KCSEL_*)
            self.constColorSel[j] = br.GetByte()
        for j in range(16):  # 0x1c most of the time (const alpha sel, GX_TEV_KASEL_*)
            self.constAlphaSel[j] = br.GetByte()
        for j in range(16):  # U16s # direct index
            self.tevOrderInfo[j] = br.ReadWORD()
        # this is to be loaded into
        # GX_CC_CPREV - GX_CC_A2??
        for j in range(4):  # direct index
            self.colorS10[j] = br.ReadWORD()
        # //these two always contained the same data in all files
        # //I've seen...
        for j in range(16):
            self.tevStageInfo[j] = br.ReadWORD()
        for j in range(16):
            self.tevSwapModeInfo[j] = br.ReadWORD()
        for j in range(4):
            self.tevSwapModeTable[j] = br.ReadWORD()

        for j in range(12):  # vf_118 has a float in here (but only in one block...)
            self.unknown6[j] = br.ReadWORD()
            # //for j in range(6):
            # init.unknown6[j] = br.GetFloat()
        for j in range(4):
            self.indices2[j] = br.ReadWORD()
        self.fogIndex = self.indices2[0]
        self.alphaCompIndex = self.indices2[1]
        self.blendIndex = self.indices2[2]
        # 3 - nbt scale?

        
g_defaultIndirectEntry = MatIndirectTexturingEntry()


def computeSectionLengths(h, lengths):
    for i in range(30):
        length = 0
        if h.offsets[i] != 0:
            next = h.sizeOfSection
            for j in range(i + 1, 30):
                if h.offsets[j] != 0:
                    next = h.offsets[j]
                    break
            length = next - h.offsets[i]

        lengths[i] = length
        if i == 3:
            pass
            # //assert(length%h.count == 0); //violated by luigi's mansion files
            # //assert(length/h.count == 312); //violated by quite a few file


class Mat3:
    def __init__(self):
        self.color1 = []  # MColors
        self.numChans = []  # U8s
        self.colorChanInfos = []  # ColorChanInfo(s)
        self.color2 = []  # MColor(s)

        self.materialbases = []  # MaterialBase
        self.materials = []
        self.indexToMatIndex = []  # int
        self.stringtable = []  # str

        self.cullModes = []  # u32

        self.texGenCounts = []  # u8
        self.texGenInfos = []  # TexGenInfo
        self.texMtxInfos = []  # TexMtxInfo

        self.texStageIndexToTextureIndex = []  # int
        self.tevOrderInfos = []  # TevOrderInfo
        self.colorS10 = []  # Color16
        self.color3 = []  # MColor
        self.tevCounts = []  # u8
        self.tevStageInfos = []  # TevStageInfo
        self.tevSwapModeInfos = []  # TevSwapModeInfo
        self.tevSwapModeTables = []  # TevSwapModeTable
        self.alphaCompares = []  # AlphaCompare
        self.blendInfos = []  # BlendInfo
        self.zModes = []  # ZMode

    def LoadData(dst, f):
        # //warn("Mat3 section support is incomplete");
        # assert (sizeof(bmd::MatEntry) == 332)

        mat3Offset = f.Position()
        i = 0

        # //read header
        h = Mat3Header()
        h.LoadData(f)

        isMat2 = (h.tag == 'MAT2')
        if isMat2:
            log.info("Model contains MAT2 block instead of MAT3")

        # //read stringtable
        # //vector<string> stringtable;
        dst.stringtable = f.ReadStringTable(mat3Offset + h.offsets[2])
        if h.count != len(dst.stringtable):
            log.warning("number of strings (%d) doesn't match number of elements (%d)",
                  len(dst.stringtable), h.count)

        # compute max length of each subsection
        # (it's probably better to check the maximal indices
        # of every MatEntry and use these as counts, but
        # this works fine as well, so stick with it for now)
        lengths = [0] * 30
        computeSectionLengths(h, lengths)

        # //offset[1] (indirection table from indices to init data indices)
        f.SeekSet(mat3Offset + h.offsets[1])
        maxIndex = 0
        arrayresize(dst.indexToMatIndex, h.count)
        for i in range(h.count):
            bla = f.ReadWORD()
            maxIndex = max(maxIndex, bla)
            dst.indexToMatIndex[i] = bla

        # //offset[4] (cull mode)
        f.SeekSet(mat3Offset + h.offsets[4])
        arrayresize(dst.cullModes, lengths[4] / 4)
        for i in range(len(dst.cullModes)):
            tmp = f.ReadDWORD()
            dst.cullModes[i] = tmp

        # //offset[5] (color1)
        f.SeekSet(mat3Offset + h.offsets[5])
        arrayresize(dst.color1, lengths[5] / 4)
        for i in range(len(dst.color1)):
            dst.color1[i] = MColor()
            dst.color1[i].LoadData(f)

        # //offset[6] (numChans)
        f.SeekSet(mat3Offset + h.offsets[6])
        arrayresize(dst.numChans, lengths[6])
        for i in range(lengths[6]):
            dst.numChans[i] = f.GetByte()
        # fread(&dst.numChans[0], 1, lengths[6], f);

        # //offset[7] (colorChanInfo)
        f.SeekSet(mat3Offset + h.offsets[7])
        arrayresize(dst.colorChanInfos, lengths[7] / 8)
        for i in range(len(dst.colorChanInfos)):
            dstInfo = ColorChanInfo()
            dstInfo.LoadData(f)
            dst.colorChanInfos[i] = dstInfo
            
        # //offset[8] (color2)
        f.SeekSet(mat3Offset + h.offsets[8])
        arrayresize(dst.color2, lengths[8] / 4)
        for i in range(len(dst.color2)):
            dst.color2[i] = MColor()
            dst.color2[i].LoadData(f)

        # //offset[0] (MatEntries)
        f.SeekSet(mat3Offset + h.offsets[0])
        arrayresize(dst.materialbases, maxIndex + 1)
        for i in range(maxIndex + 1):
            # //(this assumes that init has already been endian-fixed [?!])
            dstMat = dst.materialbases[i]
            if dstMat is None:
                dstMat = MaterialBase()
                dst.materialbases[i] = dstMat
            dstMat.LoadData(f, isMat2)
            

        # //offset[3] indirect texturing blocks (always as many as count)
        # assert (sizeof(bmd::MatIndirectTexturingEntry) == 312)
        f.SeekSet(mat3Offset + h.offsets[3])
        if lengths[3] % 312 != 0:
            log.warning("indirect texturing block size no multiple of 312: %d", lengths[3])
        elif lengths[3] // 312  != h.count:
            log.warning("number of ind texturing blocks (%d) doesn't match number of materials (%d)",
                  lengths[3] // 312, h.count)
        else:
            for i in range(h.count):
                indEntry = MatIndirectTexturingEntry()
                indEntry.LoadData(f)
                # //...
                if g_defaultIndirectEntry != indEntry:
                    log.warning("found different indirect texuring block: features will be missing from material")

        # //offsets[10] (read texGenCounts)
        f.SeekSet(mat3Offset + h.offsets[10])
        arrayresize(dst.texGenCounts, lengths[10])
        for i in range(len(dst.texGenCounts)):
            dst.texGenCounts[i] = f.GetByte()

        # //offsets[11] (texGens)
        f.SeekSet(mat3Offset + h.offsets[11])
        arrayresize(dst.texGenInfos, lengths[11] / 4)
        for i in range(len(dst.texGenInfos)):
            dst.texGenInfos[i] = TexGenInfo()
            dst.texGenInfos[i].LoadData(f)

        # //offset[13] (texmtxinfo debug)
        if (lengths[13] % (100) != 0):
            log.warning("unexpected texmtxinfo lengths[13]: %d", lengths[13])

        # //offsets[13] (read texMtxInfo)
        f.SeekSet(mat3Offset + h.offsets[13])
        arrayresize(dst.texMtxInfos, lengths[13] / 100)
        for i in range(len(dst.texMtxInfos)):
            dstInfo = TexMtxInfo()
            dstInfo.LoadData(f)

            if dstInfo.unk != 0x0100:  # //sometimes violated
                log.info("(mat3texmtx) %x instead of 0x0100", dstInfo.unk)
            if dstInfo.pad != 0xffff:
                log.info("(mat3texmtx) %x instead of 0xffff", dstInfo.pad)
            if dstInfo.unk3 != 0x0000:
                log.info("(mat3texmtx) %x instead of 0x0000", dstInfo.unk3)
            if dstInfo.pad2 != 0xffff:
                log.info("(mat3texmtx) %x instead of 2nd 0xffff", dstInfo.pad2)
            dst.texMtxInfos[i] = dstInfo

        # //offsets[15] (read texTable)
        f.SeekSet(mat3Offset + h.offsets[15])
        texLength = lengths[15]
        arrayresize(dst.texStageIndexToTextureIndex, texLength / 2)
        for i in range(texLength // 2):
            index = f.ReadWORD()
            dst.texStageIndexToTextureIndex[i] = index

        # //offsets[16] (read TevOrderInfos)
        f.SeekSet(mat3Offset + h.offsets[16])
        arrayresize(dst.tevOrderInfos, lengths[16] / 4)
        for i in range(len(dst.tevOrderInfos)):
            dst.tevOrderInfos[i] = TevOrderInfo()
            dst.tevOrderInfos[i].LoadData(f)


        # //offsets[17] (read colorS10)
        f.SeekSet(mat3Offset + h.offsets[17])
        arrayresize(dst.colorS10, lengths[17] / (4 * 2))
        for i in range(len(dst.colorS10)):
            dst.colorS10[i] = MColor()
            dst.colorS10[i].LoadDataS(f)

        # //offsets[18] (color3)
        f.SeekSet(mat3Offset + h.offsets[18])
        arrayresize(dst.color3, lengths[18] / 4)
        for i in range(len(dst.color3)):
            dst.color3[i] = MColor()
            dst.color3[i].LoadData(f)
        # //offset[19] (tevCounts)
        f.SeekSet(mat3Offset + h.offsets[19])
        dst.tevCounts = [f.GetByte() for _ in range(lengths[19])]

        # //offset[20] (TevStageInfos)
        f.SeekSet(mat3Offset + h.offsets[20])
        arrayresize(dst.tevStageInfos, lengths[20] / 20)
        for i in range(lengths[20] // 20):
            dstInfo = TevStageInfo()
            dstInfo.LoadData(f)
            dst.tevStageInfos[i] = dstInfo

        # //offset[21] (TevSwapModeInfos)
        f.SeekSet(mat3Offset + h.offsets[21])
        for i in range(lengths[21] // 4):
            info = TevSwapModeInfo()
            info.rasSel = f.GetByte()
            info.texSel = f.GetByte()
            info.pad[0] = f.GetByte()
            info.pad[1] = f.GetByte()
            dst.tevSwapModeInfos.append(info)

        # //offset[22] (TevSwapModeTable)
        f.SeekSet(mat3Offset + h.offsets[22])
        # dst.tevSwapModeTables.resize(lengths[22]/4)
        for i in range(lengths[22] // 4):
            table = TevSwapModeTable()
            table.LoadData(f)

            # dstTable = TevSwapModeTable(table.r, table.g, table.b, table.a)
            dst.tevSwapModeTables.append(table)

        # //offset[24] (alphaCompares)
        f.SeekSet(mat3Offset + h.offsets[24])
        arrayresize(dst.alphaCompares, lengths[24] / 8)
        for i in range(lengths[24] // 8):
            dstInfo = AlphaCompare()
            dstInfo.LoadData(f)
            dst.alphaCompares[i] = dstInfo

        # //offset[25] (blendInfo)
        f.SeekSet(mat3Offset + h.offsets[25])
        arrayresize(dst.blendInfos, lengths[25] / 4)
        for i in range(lengths[25] // 4):
            dstInfo = BlendInfo()
            dstInfo.blendMode = f.GetByte()
            dstInfo.srcFactor = f.GetByte()
            dstInfo.dstFactor = f.GetByte()
            dstInfo.logicOp = f.GetByte()
            dst.blendInfos[i] = dstInfo

        # //offset[26] (z mode)
        f.SeekSet(mat3Offset + h.offsets[26])
        arrayresize(dst.zModes, lengths[26] / 4)
        for i in range(lengths[26] // 4):
            m = ZMode()
            m.LoadData(f)
            dst.zModes[i] = m

        dst.materials = [None] * len(dst.materialbases)  # to prepare conversion

    #def convert(self, tex1, texpath, ext):
    #    matnum = len(self.materialbases)
    #    self.materials = [None]*matnum
    #    for index in range(matnum):
    #        self.materials[index] = createMaterialSystem(index, self, tex1, texpath, ext)
    #        self.materials[index].flag = self.materialbases[index].flag  # for scenegraph use


"""incorrect:
ColorS10"""