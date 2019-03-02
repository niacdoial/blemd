#! /usr/bin/python3
from .BinaryReader import BinaryReader
import logging
from . import common
log = logging.getLogger('bpy.ops.import_mesh.bmd.btp')


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
        self.materialIndex = 0
        self.materialName = ""
        self.indices=[0] * self.count


class BtpAnim:
    # <variable materialIndex>
    # <variable materialName>
    # <variable keyFrameIndexTable>
    def __init__(self):  # GENERATED!
        pass


class Btp:

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
            if common.GLOBALS.PARANOID:
                raise ValueError("Btp:LoadTPT1: number of strings (" +
                                str(len(stringtable))+") doesn't match number" \
                                "of animated materials (" +str(header.numMaterialAnims) + ")")
            else:
                log.warning('number of strings doesn\'t match number of animated materials')
                for i in range(header.numMaterialAnims - len(stringtable)):
                    stringtable.append('unnamed %d' %i)

        # --read matAnimIndexToMat3Index table

        # -- (h.numMaterialAnims);
        br.SeekSet(tpt1Offset + header.offsetToIndexTable)
        matAnimIndexToMat3Index = [br.ReadWORD() for _ in range(header.numMaterialAnims)]
        # -- (h.numShorts);
        br.SeekSet(tpt1Offset + header.offsetToShorts)
        shorts = [br.ReadWORD() for _ in range(header.numShorts)]

        # --read animations
        # -- btp.self.anims.resize(h.numMaterialAnims);
        br.SeekSet(tpt1Offset + header.offsetToMatAnims)

        self.anims = [None] * header.numMaterialAnims
        for i in range(header.numMaterialAnims):
            # --messageBox stringtable
            mAnim = MatAnim()
            mAnim.LoadData(br)
            # --anims[i] = anim

            if mAnim.unknown != 0x00ffffff and common.GLOBALS.PARANOID:
                raise ValueError(("btp: "+str(mAnim.unknown) +
                                 " instead of 0x00ffffff for mat anim nr "+str(i)))

            mAnim.materialIndex = matAnimIndexToMat3Index[i]
            mAnim.materialName = stringtable[i]
            mAnim.keyFrameIndexTable = shorts[mAnim.firstIndex:
                                   mAnim.firstIndex + mAnim.count]

            keyframes = [(0, mAnim.keyFrameIndexTable[0] )]
            for i, value in enumerate(mAnim.keyFrameIndexTable):
                if value != keyframes[-1]:
                    keyframes.append( (i, value) )
            mAnim.keyframes = keyframes
            mAnim.length = len(mAnim.keyFrameIndexTable)

            self.anims[i] = mAnim
            # print(animaiton)
            # copy(shorts.begin() + anim.firstIndex, shorts.begin() + anim.firstIndex + anim.count,
            # btp.anims[i].indices.begin());

    def LoadBtp(self, filePath):
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
            log.warning("readBck(): Unsupported section " + tag)
            raise ValueError("readBck(): Unsupported section " + tag)
        br.SeekSet(pos)
        # ) while not EOF br._f
        br.Close()

def animate(btp, mat3, frame):
    for btp_anim in btp.anims:

        #for i in range(len(mat3.indexToMatIndex)):
        #    if curr.materialName == mat3.stringtable[i]:
        #        break
        #else:
        #    if common.GLOBALS.PARANOID:
        #        raise ValueError('material to animate not found')
        #    else:
        #        log.warning('material to animate not found. skipping...')
        #        continue
        #        mat = mat3.materialbases[mat3.indexToMatIndex[i]]
        mat = mat3.materialbases[btm_anim.materialIndex]
        mat.texStages[0] = curr.indices[frame]

# XCX: how in the world are the times known?
# texture matrix animation?
