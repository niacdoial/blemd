#! /usr/bin/python3
from .maxheader import MessageBox
import logging
log = logging.getLogger('bpy.ops.import_mesh.bmd.shp1')


class ShpIndex:
    # <variable matrixIndex>
    # -- u16 -- can be undefined
    # <variable posIndex>
    # -- u16 
    # <variable normalIndex>
    # -- u16 
    # <variable colorIndex>
    # -- u16[2]
    # <variable texCoordIndex>
    # -- u16[8]
    def __init__(self):  # GENERATED!
        self.colorIndex= []
        self.texCoordIndex= []
#---------------------------------------------------------------------------------------------------------------------


class ShpPrimitive:
    def __init__(self):  # GENERATED!
        self.points = []
# ---------------------------------------------------------------------------------------------------------------------


class ShpPacket:
    def __init__(self):  # GENERATED!
        self.matrixTable= []
        # maps attribute matrix index to draw array index
        # -- Shp1BatchAttrib[] attribs
        # -- Packet& dst
        self.primitives= []

    def LoadPacketPrimitives(self, attribs, dataSize, br):
        done = False
        readBytes = 0
        primIndex = 0  # fixed

        while not done:
            type = br.GetByte()
            readBytes += 1
            if type == 0 or readBytes >= dataSize :
                done = True
            else:
                curPrimative = ShpPrimitive()
                curPrimative.type = type
                if len(self.primitives) <= primIndex:
                    self.primitives.append(None)
                self.primitives[primIndex] = curPrimative
                primIndex += 1

                count = br.ReadWORD()

                readBytes += 2
                curPrimative.points = []
                # --  primative.points.resize(count)
                for j in range(count):
                    curPoint = ShpIndex()
                    for k in range(len(attribs)):
                        val = 0
                        # -- get value
                        if attribs[k].dataType == 1:  # -- s8
                            val = br.GetByte()
                            readBytes += 1
                        elif attribs[k].dataType == 3:  # -- s16
                            val = br.ReadWORD()
                            readBytes += 2
                        else:
                            log.warning("X shp1: got invalid data type in packet. should never happen because dumpBatch() should check this before calling dumpPacket()")
                            raise ValueError("ERROR")

                        # -- set appropriate index
                        if attribs[k].attrib == 0:
                            curPoint.matrixIndex = val  # -- can be undefined
                        elif attribs[k].attrib == 9:
                            curPoint.posIndex = val
                        elif attribs[k].attrib == 0xa:
                            curPoint.normalIndex = val
                        elif attribs[k].attrib == 0xb or attribs[k].attrib == 0xc:
                            while len(curPoint.colorIndex) < 2:
                                curPoint.colorIndex.append(None)
                            curPoint.colorIndex[(attribs[k].attrib - 0xb)] = val  # fixed
                        elif attribs[k].attrib == 0xd or\
                             attribs[k].attrib == 0xe or\
                             attribs[k].attrib == 0xf or\
                             attribs[k].attrib == 0x10 or\
                             attribs[k].attrib == 0x11 or\
                             attribs[k].attrib == 0x12 or\
                             attribs[k].attrib == 0x13 or\
                             attribs[k].attrib == 0x14:

                            while len(curPoint.texCoordIndex)<8:
                                curPoint.texCoordIndex.append(None)
                            curPoint.texCoordIndex[(attribs[k].attrib - 0xd)] = val # fixed
                        else:
                            pass
                            #-- messageBox "WARNING shp1: got invalid attrib in packet. should never happen because dumpBatch() should check this before calling dumpPacket()"
                            #--print curPrimative
                            #-- throw "shp1: got invalid attrib in packet. should never happen because dumpBatch() should check this before calling dumpPacket()"
                            #-- ignore unknown types, it's enough to warn() in dumpBatch
                    # end for k = 0 to attribs.count

                    if len(curPrimative.points) <= j:
                        curPrimative.points.append(None)
                    curPrimative.points[j] = curPoint
                # for j = 1 to count do
            # -- end else (type == 0 || readBytes >= dataSize) then
         # -- end while not done do
# ---------------------------------------------------------------------------------------------------------------------


class ShpAttributes:
    # <variable hasMatrixIndices>
    # <variable hasPositions>
    # <variable hasNormals>
    # -- bool 
    # <variable hasColors>
    # -- bool[2] 
    # <variable hasTexCoords>
    # -- bool[8]; 
    def __init__(self):  # GENERATED!
        self.hasColors = [False]*2  # Bools[2]
        self.hasTexCoords = [False]*8  # Bools[8]

# ---------------------------------------------------------------------------------------------------------------------
# -- Used in dumpBatch


class ShpBatch:
    def __init__(self):  # GENERATED!
        self.attribs = None  # ShpAttributes
        self.packets = None

# ---------------------------------------------------------------------------------------------------------------------
# -- same as ShpBatch?


class Shp1HeaderBatch:
    def __init__(self):  # GENERATED!
        self.unknown4 = []

    def LoadData(self, br):
        self.unknown = br.ReadWORD()
        # seems to be always 0x00ff ("matrix type, unk")
        self.packetCount = br.ReadWORD()
        # u16 number of packets belonging to this batch
        # attribs used for the strips in this batch. relative to
        # Shp1Header.offsetToBatchAttribs
        # Read StripTypes until you encounter an 0x000000ff/0x00000000,
        # for all these types indices are included. If, for example,
        # a Batch has types (9, 3), (a, 3), (0xff, 0), then for this batch two shorts (= 3)
        # are stored per vertex: position index and normal index
        self.offsetToAttribs = br.ReadWORD()
        self.firstMatrixData = br.ReadWORD()  # index to first matrix data (packetCount consecutive indices)
        self.firstPacketLocation = br.ReadWORD()  # index to first packet position (packetCount consecutive indices)
        self.unknown3 = br.ReadWORD()  # 0xffff
        for j in range(7) :
            self.unknown4.append(br.GetFloat())
        # great... (seems to match the last 7 floats of joint info sometimes)
        # (one unknown float, 6 floats bounding box?)


class Shp1Header:
    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        self.tag = br.ReadFixedLengthString(4)
        self.sizeOfSection = br.ReadDWORD()
        self.batchCount = br.ReadWORD()
        self.pad = br.ReadWORD()
        self.offsetToBatches = br.ReadDWORD()
        self.offsetUnknown = br.ReadDWORD()
        self.zero = br.ReadDWORD()
        self.offsetToBatchAttribs = br.ReadDWORD()
        # batch vertex attrib start
        # The matrixTable is an array of u16, which maps from the matrix data indices
        # to Drw1Data arrays indices. If a batch contains multiple packets, for the
        # 2nd, 3rd, ... packet this array may contain 0xffff values, which means that
        # the corresponding index from the previous packet should be used.
        self.offsetToMatrixTable = br.ReadDWORD()

        self.offsetData = br.ReadDWORD()
        # start of the actual primitive data
        self.offsetToMatrixData = br.ReadDWORD()
        self.offsetToPacketLocations = br.ReadDWORD()
        # u32 offset to packet start/length info
        # (all offsets relative to Shp1Header start)
# ---------------------------------------------------------------------------------------------------------------------


class Shp1BatchAttrib:
    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
                
        self.attrib = br.ReadDWORD()
        # cf. ArrayFormat.arrayType
        self.dataType= br.ReadDWORD()
        # cf. ArrayFormat.dataType (always bytes or shorts...)

        ###########################################
        # for every packet a PacketLocation struct is stored at
        # Shp1Header.offsetToPacketLocation + Batch.firstPacketLocation*sizeof(PacketLocation).
        # This struct stores where the primitive data for this packet is stored in the
        # data block.


class Shp1PacketLocation:
    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        self.size = br.ReadDWORD()  # size in bytes of packet
        self.offset = br.ReadDWORD()  # relative to Shp1Header.offsetData
#---------------------------------------------------------------------------------------------------------------------


class Shp1Primitive:
    # <variable primitiveType>
    # --u8 see above
    # <variable numVertices>
    # --u16 that many vertices included in this primitive - for
    # --each vertex indices are stored according to batch type
    def __init__(self):  # GENERATED!
        pass
    #---------------------------------------------------------------------------------------------------------------------
    #--for every packet a MatrixData struct is stored at
    #--Shp1Header.offsetToMatrixData + Batch.firstMatrixData*sizeof(MatrixData).
    #--This struct stores which part of the MatrixTable belongs to this packet
    #--(the matrix table is stored at Shp1Header.offsetToMatrixTable)


class Shp1MatrixData:
    def __init__(self):  # GENERATED!
        pass

    def StructSize(self):
        return 8

    def LoadData(self, br):
        # from yaz0r's source (animation stuff)
        self.unknown1 = br.ReadWORD()         # -- TODO: figure this out...
        self.count = br.ReadWORD()
        # count many consecutive indices into matrixTable
        self.firstIndex = br.ReadDWORD()
        # first index into matrix table
# ---------------------------------------------------------------------------------------------------------------------


class Shp1:
    def __init__(self):  # GENERATED!
        self.batches= []

    def GetBatchAttribs(self, br, offset):
                
        origPos = br.Position()
        br.SeekSet(offset)
        batchAttribs = []
        # -- of type Shp1BatchAttrib
        attrib = Shp1BatchAttrib()
        attrib.LoadData(br)

        while attrib.attrib != 0xff:
            batchAttribs.append(attrib)
            attrib = Shp1BatchAttrib()
            attrib.LoadData(br)

        br.SeekSet(origPos)

        return batchAttribs

    def dumpBatch(self, br, batchSrc, header, baseOffset, dst):
                
        # -- read and interpret batch vertex attribs
        attribs = self.GetBatchAttribs(br, baseOffset + header.offsetToBatchAttribs + batchSrc.offsetToAttribs)

        dst.attribs.hasMatrixIndices = False
        dst.attribs.hasPositions = False
        dst.attribs.hasNormals = False


        for i in range(len(attribs)):
            if attribs[i].dataType not in (1, 3):
                # --print "Warning: shp1, dumpBatch(): unknown attrib data type %d, skipping batch"
                log.warning("shp1, dumpBatch(): unknown attrib data type %d, skipping batch")
                return None

            if attribs[i].attrib == 0:
                dst.attribs.hasMatrixIndices = True
            elif attribs[i].attrib == 9:
                dst.attribs.hasPositions = True
            elif attribs[i].attrib == 0xa:
                dst.attribs.hasNormals = True
            elif attribs[i].attrib == 0xb or attribs[i].attrib == 0xc:
                dst.attribs.hasColors[(attribs[i].attrib - 0xb)] = True  # fixed
            elif attribs[i].attrib >= 0xd and attribs[i].attrib <= 0x14:
                dst.attribs.hasTexCoords[(attribs[i].attrib - 0xd)] = True  # fixed
            else:
                log.warning("shp1, dumpBatch(): unknown attrib %d in batch, it might not display correctly")
                # -- return; //it's enough to warn
        # -- end for i=1 to attribs.count do

        # -- read packets
        dst.packets = []
        # -- dst.packets.resize(batch.packetCount);
        for i in range(batchSrc.packetCount):
            br.SeekSet(baseOffset + header.offsetToPacketLocations +
                       (batchSrc.firstPacketLocation + i)*8)  # -- sizeof(packetLocation) = 8
            packetLoc = Shp1PacketLocation()
            packetLoc.LoadData(br)

            # -- read packet's primitives
            dstPacket = ShpPacket()
            br.SeekSet(baseOffset + header.offsetData + packetLoc.offset)
            dstPacket.LoadPacketPrimitives(attribs, packetLoc.size, br)
            if len(dst.packets) <= i:
                dst.packets.append(None)
            dst.packets[i] = dstPacket

            # -- read matrix data for current packet
            matrixData = Shp1MatrixData()
            br.SeekSet(baseOffset + header.offsetToMatrixData + (batchSrc.firstMatrixData + i)*matrixData.StructSize())
            matrixData.LoadData(br)

            # --print (matrixData as string)

            # -- read packet's matrix table
            # --dstPacket.matrixTable.resize(matrixData.count);
            dstPacket.matrixTable = []
            br.SeekSet(baseOffset + header.offsetToMatrixTable + 2*matrixData.firstIndex)

            for j in range(matrixData.count):
                if len(dstPacket.matrixTable) <= j:
                    dstPacket.matrixTable.append(None)
                dstPacket.matrixTable[j] = br.ReadWORD()
            # --print (dstPacket.matrixTable.count as string) -- matrixTable
            # --print (dstPacket.matrixTable[1] as string)
    # end for i=1 to batchSrc.packetCount do

    def LoadData(self, br):
        # -- print ("0: " + (br.Position() as string))

        shp1Offset = br.Position()
        header = Shp1Header()
        header.LoadData(br)

        # -- print ("1: " + (br.Position() as string))

        # -- read self.batches
        br.SeekSet(header.offsetToBatches + shp1Offset)
        self.batches = []
        # --.resize(h.batchCount);
        # -- print  (header.batchCount as string)  = 1 on face
        for _ in range(header.batchCount):
            # -- print ("2: " + str(br.Position()))
            d = Shp1HeaderBatch()
            d.LoadData(br)

            # --print ("3: " + (br.Position() as string))

            # -- TODO: check code
            dstBatch = ShpBatch()
            dstBatch.attribs = ShpAttributes()
            self.batches.append(dstBatch)

            # --Batch& dstBatch = dst.batches[i]; dst = this
            curPos = br.Position()
            self.dumpBatch(br, d, header, shp1Offset, dstBatch)
            # --  print ("4: " + (br.Position() as string))
            br.SeekSet(curPos)
