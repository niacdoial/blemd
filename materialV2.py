import sys
import bpy
from .matpipeline import createMaterialSystem


def arrayresize(L, s):
    if len(L) >= s:
        return
    else:
        if type(s) is float and int(s) == s:
            s=int(s)
        L += [None]*(s-len(L))


class MColor:
    def __init__(self, rr=0, gg=0, bb=0, aa=1):
        self.r = rr  # u8 or s16
        self.g = gg
        self.b = bb
        self.a = aa


class ColorChanInfo:
    def __init__(self):
        # //not sure if this is right
        self.ambColorSource = 0  # U8s
        self.matColorSource = 0
        self.litMask = 0
        self.attenuationFracFunc = 0
        self.diffuseAttenuationFunc = 0


class TexGenInfo:
    def __init__(self):
        self.texGenType = 0  # U8s
        self.texGenSrc = 0
        self.matrix = 0


class TexMtxInfo:
    def __init__(self):
        self.scaleCenterX = 0.  # floats
        self.scaleCenterY = 0.
        self.scaleU = 0.
        self.scaleV = 0.


class TevOrderInfo:
    def __init__(self):
        self.texCoordId = 0  # U8s
        self.texMap = 0
        self.chanId = 0


class TevSwapModeInfo:
    def __init__(self):
        self.rasSel = 0  # U8s
        self.texSel = 0


TevSwapModeTable = MColor


class AlphaCompare:
    def __init__(self):
        self.comp0 = 0  # U8s
        self.ref0 = 0
        self.alphaOp = 0
        self.comp1 = 0
        self.ref1 = 0


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

        self.texGenInfos = [0] * 8

        self.texMtxInfos = [0] * 8

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

    def LoadData(self, br):
        dumpMat3(br, self)

    def convert(self, tex1, texpath):
        matnum = len(self.materialbases)
        self.materials = [None]*matnum
        for index in range(matnum):
            self.materials[index] = createMaterialSystem(index, self, tex1, texpath)
            self.materials[index].flag = self.materialbases[index].flag  # for scenegraph use

class BMD_namespace:
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

    class MatEntry:
        def __init__(self):
            """//(0 - possible values: 1, 4, 253 [1: draw on tree down, 4 on up??])
            //     - related to transparency sorting
            //1 - index into cullModes
            //2 - index into numChans
            //3 - index into texgen counts
            //4 - index into tev counts
            //5 - index into matData6 (?)
            //6 - index into zModes? (quite sure)
            //7 - index into matData7 (?)
            //(still missing stuff: isDirect, zCompLoc,
            //enable/disable blend alphatest depthtest, ...)"""
            self.unk = [0] * 8  # U8s

            """// 0, 1 - index into color1 (e.g. map_delfino3.bmd)
            // 6, 7 - index into color2 (e.g. mo.bdl)
            // 2, 3, 4, 5 - index into chanControls
            //u16 chanControls[8];"""

            self.color1 = [0] * 2  # U16s
            self.chanControls = [0] * 4
            self.color2 = [0] * 2  # //not in MAT2 block

            self.lights = [0] * 8  # //all 0xffff most of the time, not in MAT2 block

            self.texGenInfo = [0] * 8
            self.texGenInfo2 = [0] * 8

            self.texMatrices = [0] * 10  # //direct index
            self.dttMatrices = [0] * 20  # //?? (I have no idea what dtt matrices do...)

            self.texStages = [0] * 8  # //indices into textureTable

            # //constColor (GX_TEV_KCSEL_K0-3)
            self.color3 = [0] * 4  # //direct index

            self.constColorSel = [0] * 16  # U8s  # //0x0c most of the time (const color sel, GX_TEV_KCSEL_*)
            self.constAlphaSel = [0] * 16  # //0x1c most of the time (const alpha sel, GX_TEV_KASEL_*)

            self.tevOrderInfo = [0] * 16  # U16s # //direct index

            # //this is to be loaded into
            # //GX_CC_CPREV - GX_CC_A2??
            self.colorS10 = [0] * 4  # U16s //direct index

            # //these two always contained the same data in all files
            # //I've seen...
            self.tevStageInfo = [0] * 16  # U16s# //direct index
            self.tevSwapModeInfo = [0] * 16  # //direct index

            self.tevSwapModeTable = [0] * 4

            self.unknown6 = [0] * 12  # //vf_118 has a float in here (but only in one block...)
            # //f32 unknown6[6];

            # //0 - fog index (vf_117.bdl)
            # //1 - alphaComp (vf_117.bdl, yoshi.bmd)
            # //2 - blendInfo (cl.bdl)
            # //3 - nbt scale?
            self.indices2 = [0] * 4

    # //structs below are wip

    class MatIndirectTexturingEntry:
        class unk2C:
            def __init__(self):
                self.f = [0.] * 6  # floats # //3x2 matrix? texmatrix?
                self.b = [0] * 4  # U8s

            def __eq__(self, other):
                return self.f == other.f and \
                       self.b == other.b

        class unk4C:
            def __init__(self):
                # //the first 9 bytes of this array are probably the arguments to
                # //GX_SetTevIndirect (index is the first argument), the
                # //other three bytes are padding
                self.unk = [0] * (4 + 2)  # U16s

            def __eq__(self, other):
                return self.unk == other.unk

        def __init__(self):
            # //size = 312 = 0x138
            # //(not always...see default.bmd <- but there 3 and 2 point to the same
            # //location in file (string table). but default.bmd is the only file i know
            # //where number of ind tex entries doesn't match number of mats)

            # //this could be arguments to GX_SetIndTexOrder() plus some dummy values
            self.unk = [0] * 10  # U16s

            self.unk2 = [self.unk2C() for _ in range(3)]

            # //probably the arguments to GX_SetIndTexOrder()
            # //or GX_SetIndtexCoordScale() (index is first param)
            self.unk3 = [0] * 4  # U32s

            self.unk4 = [self.unk4C() for _ in range(16)]

        def __eq__(self, other):
            return (self.unk == other.unk) and \
                   (self.unk2 == other.unk2) and \
                   (self.unk3 == other.unk3) and \
                   (self.unk4 == other.unk4)

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
            # //(enable = litMask != 0...)
            self.ambColorSource = 0  # U8s
            self.matColorSource = 0
            self.litMask = 0
            self.attenuationFracFunc = 0
            self.diffuseAttenuationFunc = 0
            self.unk = 0
            self.pad = [0] * 2

    class TexGenInfo:
        def __init__(self):
            self.texGenType = 0  # U8s
            self.texGenSrc = 0
            self.matrix = 0
            self.pad = 0

    class TexMtxInfo:
        def __init__(self):
            self.unk = 0  # U16s
            self.pad = 0  # //0xffff most of the time

            # //0, 1 - translate u, v ????? scale center????
            # //2    - rotate u, v ?????
            # //3, 4 - repeat texture this many times
            # //       (texcoord scale u, v) (-> model (texmtx).bmd)
            self.f1 = [0.] * 5  # f32s

            self.unk2 = 0  # U16s
            self.pad2 = 0

            self.f2 = [0.] * 2  # F32s
            self.f3 = [0.] * 16  # //nearly always an 4x4 identity matrix

    class TevOrderInfo:
        def __init__(self):
            self.texCoordId = 0  # U8s
            self.texMap = 0
            self.chanId = 0
            self.pad = 0

    class TevStageInfo:
        def __init__(self):
            self.unk = 0  # U8s  # //always 0xff

            # //GX_SetTevColorIn() arguments
            self.colorIn = [0] * 4  # //GX_CC_*

            # //GX_SetTevColorOp() arguments
            self.colorOp = 0
            self.colorBias = 0
            self.colorScale = 0
            self.colorClamp = 0
            self.colorRegId = 0

            # //GX_SetTevAlphaIn() arguments
            self.alphaIn = [0] * 4  # //GC_CA_*

            # //GX_SetTevAlphaOp() arguments
            self.alphaOp = 0
            self.alphaBias = 0
            self.alphaScale = 0
            self.alphaClamp = 0
            self.alphaRegId = 0

            self.unk2 = 0  # //always 0xff

    class TevSwapModeInfo:
        def __init__(self):
            self.rasSel = 0  # U8s
            self.texSel = 0
            self.pad = [0] * 2

    class TevSwapModeTable:
        def __init__(self):
            self.r = 0  # U8s
            self.g = 0
            self.b = 0
            self.a = 0

    class AlphaCompare:
        def __init__(self):
            self.comp0 = 0  # U8s
            self.ref0 = 0
            self.alphaOp = 0
            self.comp1 = 0
            self.ref1 = 0
            self.pad = [0] * 3  # //??

    class BlendInfo:
        def __init__(self):
            self.blendMode = 0  # U8s
            self.srcFactor = 0
            self.dstFactor = 0
            self.logicOp = 0

    class ZModeInfo:
        def __init__(self):
            self.enable = 0  # U8s
            self.func = 0
            self.updateEnable = 0
            self.pad = 0  # //(ref val?)

    class FogInfo:
        def __init__(self):
            self.fogType = 0  # U8s
            self.enable = 0
            self.center = 0  # U16

            self.startZ = 0.  # f32s
            self.endZ = 0.
            self.nearZ = 0.
            self.farZ = 0.

            self.color = 0  # //U32 rgba
            self.adjTable = [0] * 10  # //U16s ????


g_defaultIndirectEntry = BMD_namespace.MatIndirectTexturingEntry()
g_defaultIndirectEntry.unk = \
    [
        0, 0xffff, 0xffff, 0xffff, 0xffff,
        0xffff, 0xffff, 0xffff, 0xffff, 0xffff
    ]

g_defaultIndirectEntry.unk2[0].f = [.5, 0., 0., 0., .5, 0.]
g_defaultIndirectEntry.unk2[0].b = [1, 0xff, 0xff, 0xff]
g_defaultIndirectEntry.unk2[1].f = [.5, 0., 0., 0., .5, 0.]
g_defaultIndirectEntry.unk2[1].b = [1, 0xff, 0xff, 0xff]
g_defaultIndirectEntry.unk2[2].f = [.5, 0., 0., 0., .5, 0.]
g_defaultIndirectEntry.unk2[2].b = [1, 0xff, 0xff, 0xff]

g_defaultIndirectEntry.unk3 = [0x0000ffff, 0x0000ffff, 0x0000ffff, 0x0000ffff]

for i in range(16):
    g_defaultIndirectEntry.unk4[i].unk = [0, 0, 0, 0, 0x00ff, 0xffff]


def displayData(out, str, f, offset, size, space=-1):
    old = f.Position()
    f.SeekSet(offset)

    out.write(str + ":")

    c = 1
    for i in range(size):
        if space > 0 and (i % space == 0):
            if space >= 16:
                print(file=out)
            else:
                out.write(" ")

        v = f.GetByte()
        out.write(hex(v))
        c += 1

    if space > 0:
        print(" (", size / float(space), " many)", sep='', file=out)

    # //log("%s", textStream.str().c_str());

    f.SeekSet(old)


# void readTevStageInfo(FILE* f, bmd::TevStageInfo& info);

def displayTevStage(out, f, offset, size):
    if size % 20 != 0:
        print("TevStage has wrong size", file=sys.stderr)
        return

    old = f.Position()
    f.SeekSet(offset)

    out.write("TevStageInfo (op, bias, scale, doClamp, tevRegId):")

    count = size / 20
    for i in range(count):
        info = BMD_namespace.TevStageInfo()
        readTevStageInfo(f, info)
        # //textStream << hex << setw(2) << setfill('0') << (int)v;

        print('\n',
              hex(info.unk), "  ",
              hex(info.colorIn[0]), ' ',
              hex(info.colorIn[1]), ' ',
              hex(info.colorIn[2]), ' ',
              hex(info.colorIn[3]), "  ",
              hex(info.colorOp), ' ',
              hex(info.colorBias), ' ',
              hex(info.colorScale), ' ',
              hex(info.colorClamp), ' ',
              hex(info.colorRegId), "  ",
              hex(info.alphaIn[0]), ' ',
              hex(info.alphaIn[1]), ' ',
              hex(info.alphaIn[2]), ' ',
              hex(info.alphaIn[3]), "  ",
              hex(info.alphaOp), ' ',
              hex(info.alphaBias), ' ',
              hex(info.alphaScale), ' ',
              hex(info.alphaClamp), ' ',
              hex(info.alphaRegId), "  ",
              hex(info.unk2), sep="", end="", file=out)

    print(" (", count, " many)", sep="", file=out)

    # //log("%s", textStream.str().c_str(), count);


    f.SeekSet(old)


def displaySize(out, str, len, space=-1):
    count = -1
    if space > 0:
        count = len / float(space)

    print(str, ": ", len, " bytes (", count, " many)", file=out, sep='')


def writeMat3Data(debugOut, f, mat3Offset, h, lengths):
    # //displayData(debugOut, "matEntries", f, mat3Offset + h.offsets[0], sizeof(bmd::MatEntry));
    displayData(debugOut, "indexToMatIndex", f, mat3Offset + h.offsets[1], 2 * h.count, 2)
    # //2: string table
    displaySize(debugOut, "IndirectTexturing", lengths[3], 312)
    displayData(debugOut, "cull mode", f, mat3Offset + h.offsets[4], lengths[4], 4)
    displayData(debugOut, "color1", f, mat3Offset + h.offsets[5], lengths[5], 4)
    displayData(debugOut, "numChans (?) (unk[2])", f, mat3Offset + h.offsets[6], lengths[6], 1)
    displayData(debugOut, "colorChanInfo", f, mat3Offset + h.offsets[7], lengths[7], 8)
    displayData(debugOut, "color2", f, mat3Offset + h.offsets[8], lengths[8], 4)
    displayData(debugOut, "light", f, mat3Offset + h.offsets[9], lengths[9], 52)  # //there's one dr_comp.bdl
    displayData(debugOut, "texCounts (unk[3])", f, mat3Offset + h.offsets[10], lengths[10], 1)
    displayData(debugOut, "TexGen", f, mat3Offset + h.offsets[11], lengths[11], 4)
    displayData(debugOut, "TexGen2", f, mat3Offset + h.offsets[12], lengths[12], 4)
    displaySize(debugOut, "TexMtxInfo", lengths[13], 100)  # //13: TexMtxInfo (below)
    displaySize(debugOut, "TexMtxInfo2", lengths[14])
    displayData(debugOut, "indexToTexIndex", f, mat3Offset + h.offsets[15], lengths[15], 2)
    displayData(debugOut, "tevOrderInfo", f, mat3Offset + h.offsets[16], lengths[16], 4)
    displayData(debugOut, "colorS10", f, mat3Offset + h.offsets[17], lengths[17], 8)
    displayData(debugOut, "color3", f, mat3Offset + h.offsets[18], lengths[18], 4)
    displayData(debugOut, "tevStageCounts (unk[4])", f, mat3Offset + h.offsets[19], lengths[19], 1)
    displayTevStage(debugOut, f, mat3Offset + h.offsets[20], lengths[20])
    displayData(debugOut, "tevSwapModeInfo", f, mat3Offset + h.offsets[21], lengths[21], 4)
    displayData(debugOut, "tevSwapModeTable", f, mat3Offset + h.offsets[22], lengths[22], 4)
    displayData(debugOut, "fog", f, mat3Offset + h.offsets[23], lengths[23], 44)
    displayData(debugOut, "alpha comp", f, mat3Offset + h.offsets[24], lengths[24], 8)
    displayData(debugOut, "blend info", f, mat3Offset + h.offsets[25], lengths[25], 4)
    displayData(debugOut, "z mode", f, mat3Offset + h.offsets[26], lengths[26], 4)
    displayData(debugOut, "matData6 (isIndirect (?))", f, mat3Offset + h.offsets[27], lengths[27], 1)
    displayData(debugOut, "matData7", f, mat3Offset + h.offsets[28], lengths[28], 1)
    displayData(debugOut, "NBTscale", f, mat3Offset + h.offsets[29], lengths[29])


def writeMatEntry(debugOut, init):
    j = 0
    # debugOut << setfill('0');
    debugOut.write("unk: unk1, cull, numChans, texCounts, tevCounts, matData6Index, zMode, matData7Index:")
    for j in range(8): debugOut.write(" " + hex(init.unk[j]) + '\n')

    debugOut.write("color1 (?): ")
    for j in range(2): debugOut.write(init.color1[j] + '\n')

    debugOut.write("chanControls (?): ")
    for j in range(4): debugOut.write(init.chanControls[j], '\n')

    debugOut.write("color2 (?): ")
    for j in range(2): debugOut.write(init.color2[j] + '\n')

    debugOut.write("lights: ")
    for j in range(8): debugOut.write(init.lights[j] + '\n')

    debugOut.write("texGenInfo: ")
    for j in range(8): debugOut.write(init.texGenInfo[j] + '\n')

    debugOut.write("texGenInfo2: ")
    for j in range(8): debugOut.write(init.texGenInfo2[j] + '\n')

    debugOut.write("texMatrices: ")
    for j in range(10): debugOut.write(init.texMatrices[j] + '\n')

    debugOut.write("dttMatrices: ")
    for j in range(20): debugOut.write(init.dttMatrices[j] + '\n')

    debugOut.write("Textures: ")
    for j in range(8): debugOut.write(init.texStages[j] + '\n')

    debugOut.write("color3: ")
    for j in range(4): debugOut.write(init.color3[j] + '\n')

    debugOut.write("constColorSel: ")
    for j in range(16): debugOut.write(hex(init.constColorSel[j]) + '\n')

    debugOut.write("constAlphaSel: ")
    for j in range(16): debugOut.write(hex(init.constAlphaSel[j]) + '\n')

    debugOut.write("tevOrderInfo: ")
    for j in range(16): debugOut.write(init.tevOrderInfo[j] + '\n')

    debugOut.write("colorS10: ")
    for j in range(4): debugOut.write(init.colorS10[j] + '\n')

    debugOut.write("tevStageInfo: ")
    for j in range(16): debugOut.write(init.tevStageInfo[j] + '\n')

    debugOut.write("tevSwapModeInfo: ")
    for j in range(16): debugOut.write(init.tevSwapModeInfo[j] + '\n')

    debugOut.write("tevSwapModeTable: ")
    for j in range(4): debugOut.write(init.tevSwapModeTable[j] + '\n')

    debugOut.write("unk6: ")
    for j in range(12): debugOut.write(init.unknown6[j] + '\n')
    # //for(j = 0; j < 6; ++j) debugOut << " " << init.unknown6[j]; debugOut << endl;

    debugOut.write("index fog, alphaComp, blend, nbtScale: ")
    for j in range(4): debugOut.write(init.indices2[j] + '\n')
    print(file=debugOut)


def writeTexMtxInfo(debugOut, info):
    j = 0

    print(info.unk, " ", info.pad, file=debugOut, sep='')
    for j in range(5):
        debugOut.write(str(info.f1[j]) + ' ')
    print('\n', info.unk2, " ", file=debugOut, sep='', end='')
    print(info.pad2, file=debugOut)
    for j in range(2):
        print(info.f2[j], " ", file=debugOut, sep='')
    for j in range(16):
        debugOut.write(str(info.f3[j]) + " ")
        if (j + 1) % 4 == 0:
            debugOut.write('\n')
    debugOut.write('\n')


def readMat3Header(f, h):
    h.tag = f.ReadFixedLengthString(4)
    h.sizeOfSection = f.ReadDWORD()
    h.count = f.ReadWORD()
    h.pad = f.ReadWORD()
    for i in range(30):
        h.offsets[i] = f.ReadDWORD()

    if h.tag == "MAT2":
        # //check if this is a MAT3 section (most of the time) or a MAT2 section
        # //(TODO: probably there's also a MAT1 section - find one...)

        # //if this is a mat2 section, convert header to a mat3 header
        for j in range(29, 0, -1):
            t = 0
            if j < 3:
                t = h.offsets[j]
            elif (j == 3 or j == 8 or j == 9):
                t = 0
            elif (j < 8):
                t = h.offsets[j - 1]
            else:
                t = h.offsets[j - 3]
            h.offsets[j] = t


def readMatIndirectTexturingEntry(f, indEntry):
    k = 0
    m = 0
    for k in range(10):
        indEntry.unk[k] = f.ReadWORD()
    for k in range(3):
        for m in range(6):
            indEntry.unk2[k].f[m] = f.GetFloat()
        for m in range(4):
            indEntry.unk2[k].b[m] = f.GetByte()

    for k in range(4):
        indEntry.unk3[k] = f.ReadDWORD()
    for k in range(16):
        for m in range(6):
            indEntry.unk4[k].unk[m] = f.ReadWORD()


def readMatEntry(f, init, isMat2):
    j = 0
    for j in range(8):
        init.unk[j] = f.GetByte()
    for j in range(2):
        init.color1[j] = f.ReadWORD()
    for j in range(4):
        init.chanControls[j] = f.ReadWORD()

    # //these two fields are only in mat3 headers, not in mat2
    if not isMat2:
        for j in range(2):
            init.color2[j] = f.ReadWORD()
        for j in range(8):
            init.lights[j] = f.ReadWORD()
    else:
        for j in range(2):
            init.color2[j] = 0xffff
        for j in range(8):
            init.lights[j] = 0xffff

    for j in range(8):
        init.texGenInfo[j] = f.ReadWORD()
    for j in range(8):
        init.texGenInfo2[j] = f.ReadWORD()
    for j in range(10):
        init.texMatrices[j] = f.ReadWORD()
    for j in range(20):
        init.dttMatrices[j] = f.ReadWORD()
    for j in range(8):
        init.texStages[j] = f.ReadWORD()
    for j in range(4):
        init.color3[j] = f.ReadWORD()
    for j in range(16):
        init.constColorSel[j] = f.GetByte()
    for j in range(16):
        init.constAlphaSel[j] = f.GetByte()
    for j in range(16):
        init.tevOrderInfo[j] = f.ReadWORD()
    for j in range(4):
        init.colorS10[j] = f.ReadWORD()
    for j in range(16):
        init.tevStageInfo[j] = f.ReadWORD()
    for j in range(16):
        init.tevSwapModeInfo[j] = f.ReadWORD()
    for j in range(4):
        init.tevSwapModeTable[j] = f.ReadWORD()
    for j in range(12):
        init.unknown6[j] = f.ReadWORD()
        # //for j in range(6):
        # init.unknown6[j] = f.GetFloat()
    for j in range(4):
        init.indices2[j] = f.ReadWORD()


def readTexMtxInfo(f, info):
    info.unk = f.ReadWORD()
    info.pad = f.ReadWORD()
    for j in range(5):
        info.f1[j] = f.GetFloat()
    info.unk2 = f.ReadWORD()
    info.pad2 = f.ReadWORD()
    for j in range(2):
        info.f2[j] = f.GetFloat()
    for j in range(16):
        info.f3[j] = f.GetFloat()


def readTevStageInfo(f, info):
    info.unk = f.GetByte()

    for j in range(4):
        info.colorIn[j] = f.GetByte()
    info.colorOp = f.GetByte()
    info.colorBias = f.GetByte()
    info.colorScale = f.GetByte()
    info.colorClamp = f.GetByte()
    info.colorRegId = f.GetByte()

    for j in range(4):
        info.alphaIn[j] = f.GetByte()
    info.alphaOp = f.GetByte()
    info.alphaBias = f.GetByte()
    info.alphaScale = f.GetByte()
    info.alphaClamp = f.GetByte()
    info.alphaRegId = f.GetByte()

    info.unk2 = f.GetByte()


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


def dumpMat3(f, dst):
    # //warn("Mat3 section support is incomplete");

    # assert (sizeof(bmd::MatEntry) == 332)

    mat3Offset = f.Position()
    i = 0

    # //read header
    h = BMD_namespace.Mat3Header()
    readMat3Header(f, h)

    isMat2 = (h.tag == 'MAT2')
    if isMat2:
        print("Model contains MAT2 block instead of MAT3", file=sys.stderr)

    # //read stringtable
    # //vector<string> stringtable;
    dst.stringtable = f.ReadStringTable(mat3Offset + h.offsets[2])
    if h.count != len(dst.stringtable):
        print("mat3: number of strings (%d) doesn't match number of elements (%d)",
              len(dst.stringtable), h.count, file=sys.stderr)

    # //compute max length of each subsection
    # //(it's probably better to check the maximal indices
    # //of every MatEntry and use these as counts, but
    # //this works fine as well, so stick with it for now)
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
        dst.color1[i].r = f.GetByte()
        dst.color1[i].g = f.GetByte()
        dst.color1[i].b = f.GetByte()
        dst.color1[i].a = f.GetByte()

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
        info = BMD_namespace.ColorChanInfo()
        info.ambColorSource = f.GetByte()
        info.matColorSource = f.GetByte()
        info.litMask = f.GetByte()
        info.attenuationFracFunc = f.GetByte()
        info.diffuseAttenuationFunc = f.GetByte()
        info.unk = f.GetByte()
        info.pad[0] = f.GetByte()
        info.pad[1] = f.GetByte()

        dstInfo = ColorChanInfo()

        # //this is wrong:
        dstInfo.ambColorSource = info.ambColorSource
        dstInfo.matColorSource = info.matColorSource
        dstInfo.litMask = info.litMask
        dstInfo.attenuationFracFunc = info.attenuationFracFunc
        dstInfo.diffuseAttenuationFunc = info.diffuseAttenuationFunc
        dst.colorChanInfos[i] = dstInfo
    # //offset[8] (color2)
    f.SeekSet(mat3Offset + h.offsets[8])
    arrayresize(dst.color2, lengths[8] / 4)
    for i in range(len(dst.color2)):
        dst.color2[i] = MColor()
        dst.color2[i].r = f.GetByte()
        dst.color2[i].g = f.GetByte()
        dst.color2[i].b = f.GetByte()
        dst.color2[i].a = f.GetByte()

    # //offset[0] (MatEntries)
    f.SeekSet(mat3Offset + h.offsets[0])
    arrayresize(dst.materialbases, maxIndex + 1)
    for i in range(maxIndex + 1):
        init = BMD_namespace.MatEntry()
        readMatEntry(f, init, isMat2)

        # //copy data
        # //(this assumes that init has already been endian-fixed)
        dstMat = dst.materialbases[i]
        if dstMat is None:
            dstMat = MaterialBase()
            dst.materialbases[i] = dstMat

        dstMat.flag = init.unk[0]
        dstMat.cullIndex = init.unk[1]
        dstMat.numChansIndex = init.unk[2]
        dstMat.texGenCountIndex = init.unk[3]
        dstMat.tevCountIndex = init.unk[4]
        dstMat.zModeIndex = init.unk[6]

        j = 0
        for j in range(8):
            dstMat.texGenInfos[j] = init.texGenInfo[j]
            dstMat.texMtxInfos[j] = init.texMatrices[j]
            dstMat.texStages[j] = init.texStages[j]
        for j in range(4):
            dstMat.color3[j] = init.color3[j]
            dstMat.colorS10[j] = init.colorS10[j]

            dstMat.chanControls[j] = init.chanControls[j]

            dstMat.tevSwapModeTable[j] = init.tevSwapModeTable[j]
        for j in range(2):
            dstMat.color1[j] = init.color1[j]
            dstMat.color2[j] = init.color2[j]
        for j in range(16):
            dstMat.constColorSel[j] = init.constColorSel[j]
            dstMat.constAlphaSel[j] = init.constAlphaSel[j]
            dstMat.tevOrderInfo[j] = init.tevOrderInfo[j]
            dstMat.tevStageInfo[j] = init.tevStageInfo[j]
            dstMat.tevSwapModeInfo[j] = init.tevSwapModeInfo[j]

        dstMat.alphaCompIndex = init.indices2[1]
        dstMat.blendIndex = init.indices2[2]

    # //offset[3] indirect texturing blocks (always as many as count)
    # assert (sizeof(bmd::MatIndirectTexturingEntry) == 312)
    f.SeekSet(mat3Offset + h.offsets[3])
    if lengths[3] % 312 != 0:
        print("mat3: indirect texturing block size no multiple of 312: %d", lengths[3], file=sys.stderr)
    elif lengths[3] / 312 != h.count:
        print("mat3: number of ind texturing blocks (%d) doesn't match number of materials (%d)",
              lengths[3] / 312, h.count, file=sys.stderr)
    else:
        for i in range(h.count):
            indEntry = BMD_namespace.MatIndirectTexturingEntry()
            readMatIndirectTexturingEntry(f, indEntry)
            # //...
            if g_defaultIndirectEntry != indEntry:
                print("found different ind tex block", file=sys.stderr)

    # //offsets[10] (read texGenCounts)
    f.SeekSet(mat3Offset + h.offsets[10])
    arrayresize(dst.texGenCounts, lengths[10])
    for i in range(len(dst.texGenCounts)):
        dst.texGenCounts[i] = f.GetByte()

    # //offsets[11] (texGens)
    f.SeekSet(mat3Offset + h.offsets[11])
    arrayresize(dst.texGenInfos, lengths[11] / 4)
    for i in range(len(dst.texGenInfos)):
        info = BMD_namespace.TexGenInfo()
        info.texGenType = f.GetByte()
        info.texGenSrc = f.GetByte()
        info.matrix = f.GetByte()
        info.pad = f.GetByte()

        dst.texGenInfos[i] = TexGenInfo()
        dst.texGenInfos[i].texGenType = info.texGenType
        dst.texGenInfos[i].texGenSrc = info.texGenSrc
        dst.texGenInfos[i].matrix = info.matrix

    # //offset[13] (texmtxinfo debug)
    if (lengths[13] % (100) != 0):
        print("ARGH: unexpected texmtxinfo lengths[13]: %d", lengths[13], file=sys.stderr)
    else:
        f.SeekSet(mat3Offset + h.offsets[13])

        for m in range(lengths[13] // (25 * 4)):
            info = BMD_namespace.TexMtxInfo()
            readTexMtxInfo(f, info)

            if (info.unk != 0x0100):  # //sometimes violated
                print("(mat3texmtx) %x instead of 0x0100", info.unk, file=sys.stderr)
            if (info.pad != 0xffff):
                print("(mat3texmtx) %x instead of 0xffff", info.pad, file=sys.stderr)
            if (info.unk2 != 0x0000):
                print("(mat3texmtx) %x instead of 0x0000", info.unk2, file=sys.stderr)
            if (info.pad2 != 0xffff):
                print("(mat3texmtx) %x instead of 2nd 0xffff", info.pad2, file=sys.stderr)

    # //offsets[13] (read texMtxInfo)
    f.SeekSet(mat3Offset + h.offsets[13])
    arrayresize(dst.texMtxInfos, lengths[13] / 100)
    for i in range(len(dst.texMtxInfos)):
        info = BMD_namespace.TexMtxInfo()
        readTexMtxInfo(f, info)
        dstInfo = TexMtxInfo()
        dstInfo.scaleCenterX = info.f1[0]
        dstInfo.scaleCenterY = info.f1[1]
        dstInfo.scaleU = info.f1[3]
        dstInfo.scaleV = info.f1[4]
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
        info = BMD_namespace.TevOrderInfo()
        info.texCoordId = f.GetByte()
        info.texMap = f.GetByte()
        info.chanId = f.GetByte()
        info.pad = f.GetByte()

        dst.tevOrderInfos[i] = TevOrderInfo()
        dst.tevOrderInfos[i].texCoordId = info.texCoordId
        dst.tevOrderInfos[i].texMap = info.texMap
        dst.tevOrderInfos[i].chanId = info.chanId

    # //offsets[17] (read colorS10)
    f.SeekSet(mat3Offset + h.offsets[17])
    arrayresize(dst.colorS10, lengths[17] / (4 * 2))
    for i in range(len(dst.colorS10)):
        col = [f.GetSHORT() for _ in range(4)]
        dst.colorS10[i] = MColor()
        dst.colorS10[i].r = col[0]
        dst.colorS10[i].g = col[1]
        dst.colorS10[i].b = col[2]
        dst.colorS10[i].a = col[3]

    # //offsets[18] (color3)
    f.SeekSet(mat3Offset + h.offsets[18])
    arrayresize(dst.color3, lengths[18] / 4)
    for i in range(len(dst.color3)):
        dst.color3[i] = MColor()
        dst.color3[i].r = f.GetByte()
        dst.color3[i].g = f.GetByte()
        dst.color3[i].b = f.GetByte()
        dst.color3[i].a = f.GetByte()

    # //offset[19] (tevCounts)
    f.SeekSet(mat3Offset + h.offsets[19])
    dst.tevCounts = [f.GetByte() for _ in range(lengths[19])]

    # //offset[20] (TevStageInfos)
    f.SeekSet(mat3Offset + h.offsets[20])
    arrayresize(dst.tevStageInfos, lengths[20] / 20)
    for i in range(lengths[20] // 20):
        info = BMD_namespace.TevStageInfo()
        readTevStageInfo(f, info)

        # boring retranscription
        dstInfo = TevStageInfo()
        dstInfo.colorIn = info.colorIn
        dstInfo.colorOp = info.colorOp
        dstInfo.colorBias = info.colorBias
        dstInfo.colorScale = info.colorScale
        dstInfo.colorClamp = info.colorClamp
        dstInfo.colorRegId = info.colorRegId
        dstInfo.alphaIn = info.alphaIn
        dstInfo.alphaOp = info.alphaOp
        dstInfo.alphaBias = info.alphaBias
        dstInfo.alphaScale = info.alphaScale
        dstInfo.alphaClamp = info.alphaClamp
        dstInfo.alphaRegId = info.alphaRegId
        dst.tevStageInfos[i] = dstInfo

    # //offset[21] (TevSwapModeInfos)
    f.SeekSet(mat3Offset + h.offsets[21])
    for i in range(lengths[21] // 4):
        info = BMD_namespace.TevSwapModeInfo()
        info.rasSel = f.GetByte()
        info.texSel = f.GetByte()
        info.pad[0] = f.GetByte()
        info.pad[1] = f.GetByte()
        dst.tevSwapModeInfos.append(TevSwapModeInfo())
        dst.tevSwapModeInfos[i].rasSel = info.rasSel
        dst.tevSwapModeInfos[i].texSel = info.texSel

    # //offset[22] (TevSwapModeTable)
    f.SeekSet(mat3Offset + h.offsets[22])
    # dst.tevSwapModeTables.resize(lengths[22]/4)
    for i in range(lengths[22] // 4):
        table = BMD_namespace.TevSwapModeTable()
        table.r = f.GetByte()
        table.g = f.GetByte()
        table.b = f.GetByte()
        table.a = f.GetByte()

        dstTable = TevSwapModeTable(table.r, table.g, table.b, table.a)
        dst.tevSwapModeTables.append(dstTable)

    # //offset[24] (alphaCompares)
    f.SeekSet(mat3Offset + h.offsets[24])
    arrayresize(dst.alphaCompares, lengths[24] / 8)
    for i in range(lengths[24] // 8):
        info = BMD_namespace.AlphaCompare()
        info.comp0 = f.GetByte()
        info.ref0 = f.GetByte()
        info.alphaOp = f.GetByte()
        info.comp1 = f.GetByte()
        info.ref1 = f.GetByte()
        info.pad[0] = f.GetByte()
        info.pad[1] = f.GetByte()
        info.pad[2] = f.GetByte()

        dstInfo = AlphaCompare()
        dstInfo.comp0 = info.comp0
        dstInfo.ref0 = info.ref0
        dstInfo.alphaOp = info.alphaOp
        dstInfo.comp1 = info.comp1
        dstInfo.ref1 = info.ref1
        dst.alphaCompares[i] = dstInfo

    # //offset[25] (blendInfo)
    f.SeekSet(mat3Offset + h.offsets[25])
    arrayresize(dst.blendInfos, lengths[25] / 4)
    for i in range(lengths[25] // 4):
        info = BMD_namespace.BlendInfo()
        info.blendMode = f.GetByte()
        info.srcFactor = f.GetByte()
        info.dstFactor = f.GetByte()
        info.logicOp = f.GetByte()

        dstInfo = BlendInfo()
        dstInfo.blendMode = info.blendMode
        dstInfo.srcFactor = info.srcFactor
        dstInfo.dstFactor = info.dstFactor
        dstInfo.logicOp = info.logicOp
        dst.blendInfos[i] = dstInfo

    # //offset[26] (z mode)
    f.SeekSet(mat3Offset + h.offsets[26])
    arrayresize(dst.zModes, lengths[26] / 4)
    for i in range(lengths[26] // 4):
        zInfo = BMD_namespace.ZModeInfo()
        zInfo.enable = f.GetByte()
        zInfo.func = f.GetByte()
        zInfo.updateEnable = f.GetByte()
        zInfo.pad = f.GetByte()

        m = ZMode()
        m.enable = zInfo.enable != 0
        m.zFunc = zInfo.func
        m.enableUpdate = zInfo.updateEnable != 0
        dst.zModes[i] = m


"""void writeMat3Info(FILE* f, ostream& out)
{
  int mat3Offset = ftell(f);
  size_t i;

  out << string(50, '/') << endl
      << "//Mat3 section" << endl
      << string(50, '/') << endl << endl;

  out << "(only partially implemented)" << endl << endl << endl;

  //read header
  bmd::Mat3Header h;
  readMat3Header(f, h);
  bool isMat2 = strncmp(h.tag, "MAT2", 4) == 0;

  //compute lengths (see comment above for some notes on this)
  vector<size_t> lengths(30);
  computeSectionLengths(h, lengths);

  //offset[1] (indirection table from indices to init data indices)
  fseek(f, mat3Offset + h.offsets[1], SEEK_SET);
  u16 maxIndex = 0;
  vector<u16> indexToMatIndex(h.count);
  for(i = 0; i < h.count; ++i)
  {
    u16 bla; fread(&bla, 2, 1, f); toWORD(bla);
    maxIndex = max(maxIndex, bla);
    indexToMatIndex[i] = bla;
  }

  //indexed data
  out << string(h.tag, 4) <<  " data" << endl << endl;
  writeMat3Data(out, f, mat3Offset, h, lengths);

  //read stringtable
  vector<string> stringtable;
  readStringtable(mat3Offset + h.offsets[2], f, stringtable);

  //offset[0] (MatEntries)
  out << endl << endl << "MatEntries" << endl << endl;
  fseek(f, mat3Offset + h.offsets[0], SEEK_SET);
  for(i = 0; i <= maxIndex; ++i)
  {
    bmd::MatEntry init;
    readMatEntry(f, init, isMat2);

    //dump names of this stage info block
    for(size_t m = 0; m < indexToMatIndex.size(); ++m)
      if(indexToMatIndex[m] == i)
        out << stringtable[m] << " ";
    out << endl;

    //dump block
    writeMatEntry(out, init);
  }

  //offset[3] indirect texturing blocks (always as many as count)
  out << endl << endl << "Indirect texturing entries" << endl;
  fseek(f, mat3Offset + h.offsets[3], SEEK_SET);
  if(lengths[3]%312 != 0)
    out << "mat3: indirect texturing block size no multiple of 312: " << lengths[3] << endl << endl;
  else if(lengths[3]/312 != h.count)
    out << "mat3: number of ind texturing blocks (" << lengths[3]/312
        << ") doesn't match number of materials (" << h.count << ")" << endl << endl;
  else
  {
    //dump data
    for(i = 0; i < h.count; ++i)
    {
      bmd::MatIndirectTexturingEntry indEntry;
      readMatIndirectTexturingEntry(f, indEntry);

      //dump block
      int k;
      if(i < stringtable.size())
        out << " " << stringtable[i] << endl;
      out << " Ten shorts:" << endl << "  ";
      for(k = 0; k < 10; ++k)
        out << hex << setw(4) << indEntry.unk[k] << " ";
      out << endl;
      out << " Three times 6 floats, 4 bytes:" << endl;
      for(k = 0; k < 3; ++k)
      {
        out << "  ";
        int m;
        for(m = 0; m < 3; ++m)
          out << setw(6) << indEntry.unk2[k].f[m] << " ";
        out << endl << "  ";
        for(m = 3; m < 6; ++m)
          out << setw(6) << indEntry.unk2[k].f[m] << " ";
        out << endl << "  ";
        for(m = 0; m < 4; ++m)
          out << hex << setw(2) << (int)indEntry.unk2[k].b[m] << " ";
        out << endl;
      }
      out << " 4 ints:" << endl;
      for(k = 0; k < 4; ++k)
        out << hex << "  " << setw(8) << indEntry.unk3[k] << endl;
      out << " 16 times 6 shorts:" << endl;
      for(k = 0; k < 16; ++k)
      {
        out << "  ";
        for(int m = 0; m < 6; ++m)
          out << hex << setw(4) << indEntry.unk4[k].unk[m] << " ";
        out << endl;
      }
      out << endl;

      if(memcmp(&g_defaultIndirectEntry, &indEntry, sizeof(indEntry)) != 0)
        out << " ->This was a different block." << endl;

      out << endl;
    }
  }

  //offset[13] (texmtxinfo)
  out << "TexMtxInfos" << endl << endl;
  fseek(f, mat3Offset + h.offsets[13], SEEK_SET);

  for(size_t m = 0; m < lengths[13]/100; ++m)
  {
    bmd::TexMtxInfo info;
    readTexMtxInfo(f, info);
    writeTexMtxInfo(out, info);
  }
}"""


def create_material(msys):
    material = bpy.data.materials.new('stupid_name_that_will_be_erased_in_a_moment')
    material.use_nodes = True
    material.use_transparency = True
    material.transparency_method = 'Z_TRANSPARENCY'
    msys.export(material.node_tree)
    return material