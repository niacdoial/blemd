#! /usr/bin/python
import logging
from . import common
log = logging.getLogger('bpy.ops.import_mesh.bmd.shp1')

"""
Okay.
Mesh structure:
Batches define the attributes that can be contained in them (see ShpAttributes)
Packets define the relative weights
Primitives contain loops (`ShpIndex`es)
"""


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
# ---------------------------------------------------------------------------------------------------------------------


class ShpPrimitive:
    # <variable primitiveType>
    # --u8 see above
    # <variable numVertices>
    # --u16 that many vertices included in this primitive - for
    # --each vertex indices are stored according to batch type
    def __init__(self):  # GENERATED!
        self.points = []
    #---------------------------------------------------------------------------------------------------------------------
    #--for every packet a MatrixData struct is stored at
    #--Shp1Header.offsetToMatrixData + Batch.firstMatrixData*sizeof(MatrixData).
    #--This struct stores which part of the MatrixTable belongs to this packet
    #--(the matrix table is stored at Shp1Header.offsetToMatrixTable)
# ---------------------------------------------------------------------------------------------------------------------


class ShpPacket:
    def __init__(self):  # GENERATED!
        self.matrixTable = []
        # maps attribute matrix index to draw array index
        # -- Shp1BatchAttrib[] attribs
        # -- Packet& dst
        self.primitives = []

    def LoadPacketPrimitives(self, attribs, dataSize, br):
        done = False
        readBytes = 0
        primIndex = 0  # fixed

        while not done:
            type = br.GetByte()
            readBytes += 1
            if type == 0 or readBytes >= dataSize:
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
                            log.error("X shp1: got invalid data type in packet. should never happen because dumpBatch() should check this before calling dumpPacket()")
                            if common.GLOBALS.PARANOID:
                                raise ValueError("ERROR")

                        # -- set appropriate index
                        if attribs[k].attrib == 0:
                            curPoint.matrixIndex = val
                        elif attribs[k].attrib == 9:
                            curPoint.posIndex = val
                        elif attribs[k].attrib == 0xa:
                            curPoint.normalIndex = val
                        elif attribs[k].attrib == 0xb or attribs[k].attrib == 0xc:
                            while len(curPoint.colorIndex) < 2:
                                curPoint.colorIndex.append(None)
                            curPoint.colorIndex[(attribs[k].attrib - 0xb)] = val  # fixed
                        elif 0xd <= attribs[k].attrib <= 0x14:
                            while len(curPoint.texCoordIndex)<8:
                                curPoint.texCoordIndex.append(None)
                            curPoint.texCoordIndex[(attribs[k].attrib - 0xd)] = val  # fixed
                        else:
                            log.error("impossible SHP attribute %d", attribs[k].attrib)
                            if common.GLOBALS.PARANOID and False:
                                raise ValueError('~the dev was an idiot~')
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

    def DumpPacketPrimitives(self, attribs, bw):
        writtenBytes = 0

        for curPrimative in self.primitives:
            bw.writeByte(curPrimative.type)
            writtenBytes += 1

            bw.writeWord(len(curPrimative.points))
            writtenBytes += 2
            curPrimative.points = []
            # --  primative.points.resize(count)
            for curPoint in curPrimative.points:
                for k in range(len(attribs)):
                    # -- set appropriate index
                    if attribs[k].attrib == 0:
                        val = curPoint.matrixIndex
                    elif attribs[k].attrib == 9:
                        val = curPoint.posIndex
                    elif attribs[k].attrib == 0xa:
                        val = curPoint.normalIndex
                    elif attribs[k].attrib == 0xb or attribs[k].attrib == 0xc:
                        while len(curPoint.colorIndex) < 2:
                            curPoint.colorIndex.append(None)
                        val = curPoint.colorIndex[(attribs[k].attrib - 0xb)]  # fixed
                    elif 0xd <= attribs[k].attrib <= 0x14:
                        while len(curPoint.texCoordIndex) < 8:
                            curPoint.texCoordIndex.append(None)
                        val = curPoint.texCoordIndex[(attribs[k].attrib - 0xd)]  # fixed
                    else:
                        log.error("impossible SHP attribute %d", attribs[k].attrib)
                        if common.GLOBALS.PARANOID:
                            raise ValueError('~the dev was an idiot~')

                    if attribs[k].dataType == 1:  # -- s8
                        bw.writeByte(val)
                        writtenBytes += 1
                    elif attribs[k].dataType == 3:  # -- s16
                        bw.writeWord(val)
                        writtenBytes += 2
                    else:
                        log.error("shp1: invalid data type %d", attribs[k].dataType)
                        if common.GLOBALS.PARANOID:
                            raise ValueError("ERROR")
                        # -- messageBox "WARNING shp1: got invalid attrib in packet. should never happen because dumpBatch() should check this before calling dumpPacket()"
                        # --print curPrimative
                        # -- throw "shp1: got invalid attrib in packet. should never happen because dumpBatch() should check this before calling dumpPacket()"
                        # -- ignore unknown types, it's enough to warn() in dumpBatch
        bw.writeByte(0)  # create the incomplete 'termination primitive'

        return writtenBytes
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



class ShpBatch:
    def __init__(self):  # GENERATED!
        self.attribs = None  # ShpAttributes
        self.packets = None


class Shp1BatchDescriptor:
    size = 40
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
        for _ in range(7):
            self.unknown4.append(br.GetFloat())
        # great... (seems to match the last 7 floats of joint info sometimes)
        # (one unknown float, 6 floats bounding box?)

    def DumpData(self, bw):
        bw.writeWord(0x00ff)
        bw.writeWord(self.packetCount)
        bw.writeWord(self.offsetToAttribs)
        bw.writeWord(self.firstMatrixData)
        bw.writeWord(self.firstPacketLocation)
        bw.writeWord(0xffff)
        for _ in range(7):
            bw.writeFloat(0.0)  # XCX might need actual values


class Shp1Header:
    size = 44
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

    def DumpData(self, bw):
        bw.writeString("SHP1")
        bw.writeDword(self.sizeOfSection)
        bw.writeWord(self.batchCount)
        bw.writeWord(self.pad)
        bw.writeDword(self.offsetToBatches)
        bw.writeDword(self.offsetUnknown)
        bw.writeDword(self.zero)
        bw.writeDword(self.offsetToBatchAttribs)
        # batch vertex attrib start
        # The matrixTable is an array of u16, which maps from the matrix data indices
        # to Drw1Data arrays indices. If a batch contains multiple packets, for the
        # 2nd, 3rd, ... packet this array may contain 0xffff values, which means that
        # the corresponding index from the previous packet should be used.
        bw.writeDword(self.offsetToMatrixTable)

        bw.writeDword(self.offsetData)
        # start of the actual primitive data
        bw.writeDword(self.offsetToMatrixData)
        bw.writeDword(self.offsetToPacketLocations)
        # u32 offset to packet start/length info
        # (all offsets relative to Shp1Header start)
# ---------------------------------------------------------------------------------------------------------------------


class Shp1BatchAttrib:
    size = 8
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

    def DumpData(self, bw):
        bw.writeDword(self.attrib)
        bw.writeDword(self.dataType)


class Shp1PacketLocation:
    size = 8
    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        self.packetSize = br.ReadDWORD()  # size in bytes of packet
        self.offset = br.ReadDWORD()  # relative to Shp1Header.offsetData

    def DumpData(self, bw):
        bw.writeDword(self.packetSize)  # size in bytes of packet
        bw.writeDword(self.offset)  # relative to Shp1Header.offsetData
#---------------------------------------------------------------------------------------------------------------------


class Shp1MatrixData:
    size = 8
    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        # from yaz0r's source (animation stuff)
        self.unknown1 = br.ReadWORD()
        # TODO: figure this out... 0xffff is a valid value: probably means "keep last instance", but for what?
        self.count = br.ReadWORD()
        # count many consecutive indices into matrixTable
        self.firstIndex = br.ReadDWORD()
        # first index into matrix table

    def DumpData(self, bw):
        # from yaz0r's source (animation stuff)
        bw.writeWord(self.unknown1)
        bw.writeWord(self.count)
        # count many consecutive indices into matrixTable
        bw.writeDword(self.firstIndex)
        # first index into matrix table
# ---------------------------------------------------------------------------------------------------------------------


class Shp1:
    def __init__(self):  # GENERATED!
        self.batches = []

        self.all_attribs = []
        self.all_p_locs = []
        self.matrices_data = []
        self.matrices_table = []

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

    def makeBatch(self, br, batchSrc, header, baseOffset, dst):

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
            dstPacket.LoadPacketPrimitives(attribs, packetLoc.packetSize, br)
            if len(dst.packets) <= i:
                dst.packets.append(None)
            dst.packets[i] = dstPacket

            # -- read matrix data for current packet
            matrixData = Shp1MatrixData()
            br.SeekSet(baseOffset + header.offsetToMatrixData + (batchSrc.firstMatrixData + i)*matrixData.size)
            matrixData.LoadData(br)

            # --print (matrixData as string)

            # -- read packet's matrix table
            # --dstPacket.matrixTable.resize(matrixData.count);
            dstPacket.matrixTable = [None] * matrixData.count
            br.SeekSet(baseOffset + header.offsetToMatrixTable + 2*matrixData.firstIndex)

            for j in range(matrixData.count):
                dstPacket.matrixTable[j] = br.ReadWORD()
            # --print (dstPacket.matrixTable.count as string) -- matrixTable
            # --print (dstPacket.matrixTable[1] as string)
    # end for i=1 to batchSrc.packetCount do

    def decomposeBatch(self, bww, batch, header, baseOffset, batchDst):

        batchDst.offsetToAttribs = len(self.all_attribs) * Shp1BatchAttrib.size

        batch.raw_attribs = attribs = []

        if batch.attribs.hasMatrixIndices:
            attrib = Shp1BatchAttrib()
            attrib.attrib = 0
            attrib.dataType = 1
            attribs.append(attrib)
        if batch.attribs.hasPositions:
            attrib = Shp1BatchAttrib()
            attrib.attrib = 9
            attrib.dataType = 3
            attribs.append(attrib)
        if batch.attribs.hasNormals:
            attrib = Shp1BatchAttrib()
            attrib.attrib = 0xa
            attrib.dataType = 3
            attribs.append(attrib)
        for i in (0, 1):
            if batch.attribs.hasColor[i]:
                attrib = Shp1BatchAttrib()
                attrib.attrib = 0xb+i
                attrib.dataType = 3
                attribs.append(attrib)
        for i in range(8):
            if batch.attribs.hasTexCoords[i]:
                attrib = Shp1BatchAttrib()
                attrib.attrib = 0xd + i
                attrib.dataType = 3
                attribs.append(attrib)

        attrib = Shp1BatchAttrib()  # each batch must declare a 'separator attibute'
        attrib.attrib = 0xff
        attrib.dataType = 0xff
        attribs.append(attrib)

        self.all_attribs += attribs

        batchDst.firstMatrixData = len(self.matrices_data)

        batch.p_locs = p_locs = []  # give the batch a reference for future completion

        batchDst.packetCount = len(batch.packets)
        batchDst.firstPacketLocation = len(self.all_p_locs)

        for i in range(len(batch.packets)):
            packet = batch.packets[i]

            packetLoc = Shp1PacketLocation()
            # created here, will be completed at primitive write time


            # packetLoc.offset = bw.Position() - baseOffset - header.offsetData

            # bw.SeekSet(baseOffset + header.offsetData + packetLoc.offset)
            # packetLoc.packetSize = packet.DumpPacketPrimitives(attribs, bw)

            p_locs.append(packetLoc)

            # -- read matrix data for current packet
            matrixData = Shp1MatrixData()

            matrixData.unknown1 = 3
            matrixData.count = len(packet.matrixTable)

            # bw.SeekSet(baseOffset + header.offsetToMatrixData + (batchDst.firstMatrixData + i) * matrixData.size)
            self.matrices_data.append(matrixData)

            matrixData.firstIndex = len(self.matrices_table)
            # bw.SeekSet(baseOffset + header.offsetToMatrixTable + 2 * matrixData.firstIndex)  # position indicator

            for j in range(matrixData.count):
                self.matrices_table.append(packet.matrixTable[j])

        self.all_p_locs += p_locs

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
        for _ in range(header.batchCount):
            # -- print ("2: " + str(br.Position()))
            d = Shp1BatchDescriptor()
            d.LoadData(br)

            # --print ("3: " + (br.Position() as string))

            # -- TODO: check code
            dstBatch = ShpBatch()
            dstBatch.attribs = ShpAttributes()
            self.batches.append(dstBatch)

            # --Batch& dstBatch = dst.batches[i]; dst = this
            curPos = br.Position()
            self.makeBatch(br, d, header, shp1Offset, dstBatch)
            # --  print ("4: " + (br.Position() as string))
            br.SeekSet(curPos)

    def DumpData(self, bw):
        # -- print ("0: " + (br.Position() as string))

        shp1Offset = bw.Position()
        header = Shp1Header()

        header.pad = 0xffff
        header.zero = 0

        header.batchCount = len(self.batches)
        header.offsetToBatches = header.size
        header.offsetUnknown = 000  # a short per batch?
        header.offsetToBatchAttribs = 000  # aligned
        header.offsetToMatrixTable = 000
        header.offsetData = 000  # aligned
        header.offsetToMatrixData = 000
        header.offsetToPacketLocations = 000

        bw.writePadding(header.size)
        #header.DumpData(bw)


        for batch in self.batches:
            # -- print ("2: " + str(br.Position()))
            d = Shp1BatchDescriptor()


            # -- TODO: check code
            # --Batch& dstBatch = dst.batches[i]; dst = this
            curPos = bw.Position()
            self.decomposeBatch(bw, batch, header, shp1Offset, d)
            # --  print ("4: " + (br.Position() as string))
            bw.SeekSet(curPos)
            d.DumpData(bw)

        header.offsetUnknown = bw.Position()
        for _ in range(header.batchCount):
            bw.writeWord(0)
        bw.writePaddingTo16()

        header.offsetToBatchAttribs = bw.Position()
        for attrib in self.all_attribs:
            attrib.DumpData(bw)
        # this includes the separator attribs

        header.offsetToMatrixTable = bw.Position()
        for mtx in self.matrices_table:
            bw.writeWord(mtx)
        bw.writePaddingTo16()

        header.offsetData = bw.Position()
        total_length = 0
        for batch in self.batches:
            for i, packet in enumerate(batch.packets):
                batch.p_locs[i].offset = total_length
                length = packet.DumpPacketPrimitives(batch.raw_attribs, bw)
                batch.p_locs[i].packetSize = length
                total_length += length

        header.offsetToMatrixData = bw.Position()
        for mdat in self.matrices_data:
            mdat.DumpData(bw)

        header.offsetToPacketLocations = bw.Position()
        for p_loc in self.all_p_locs:
            p_loc.DumpData()

        bw.writePaddingTo16()
        header.sizeOfSection = bw.Position() - shp1Offset
        bw.SeekSet(shp1Offset)
        header.DumpData(bw)
        bw.Seekset(shp1Offset + header.sizeOfSection)
