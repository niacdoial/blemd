#! /usr/bin/python3
from .maxheader import MessageBox


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
    # <variable type>
    # -- u8 
    # <variable points>
    # -- vector<ShpIndex>
    def __init__(self):  # GENERATED!
        self.points= []
# ---------------------------------------------------------------------------------------------------------------------


class ShpPacket:
    # <variable primitives>
    # -- std::vector<ShpPrimitive>
    # <variable matrixTable>
    # -- std::vector<u16> maps attribute matrix index to draw array index
    # -- Shp1BatchAttrib[] attribs 
    # -- Packet& dst
    # <function>

    # -- end function
    def __init__(self):  # GENERATED!
        self.matrixTable= []
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
                        elif attribs[k].dataType == 3: # -- s16
                            val = br.ReadWORD()
                            readBytes += 2
                        else:
                            MessageBox("X shp1: got invalid data type in packet. should never happen because dumpBatch() should check this before calling dumpPacket()")
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
        self.hasColors= []
        self.hasTexCoords= []

# ---------------------------------------------------------------------------------------------------------------------
# -- Used in dumpBatch


class ShpBatch:
    # <variable attribs>
    # -- ShpAttributes
    # <variable packets>
    # -- std::vector<ShpPacket>
    def __init__(self):  # GENERATED!
        self.attribs = None
        self.packets = None

# ---------------------------------------------------------------------------------------------------------------------
# -- same as ShpBatch?


class Shp1HeaderBatch:
    """# <variable unknown>
    # -- u16 seems to be always 0x00ff ("matrix type, unk")
    # <variable packetCount>
    # -- u16 number of packets belonging to this batch
    # --attribs used for the strips in this batch. relative to
    # --Shp1Header.offsetToBatchAttribs
    # --Read StripTypes until you encounter an 0x000000ff/0x00000000,
    # --for all these types indices are included. If, for example,
    # --a Batch has types (9, 3), (a, 3), (0xff, 0), then for this batch two shorts (= 3)
    # --are stored per vertex: position index and normal index
    # <variable offsetToAttribs>
    # --u16 
    # <variable firstMatrixData>
    # --u16 index to first matrix data (packetCount consecutive indices)
    # <variable firstPacketLocation>
    # --u16 index to first packet position (packetCount consecutive indices)
    # <variable unknown3>
    # --u16 0xffff
    # <variable unknown4>
    # --float[7]  great... (seems to match the last 7 floats of joint info sometimes)
    # --(one unknown float, 6 floats bounding box?)
    # <function>"""

    def __init__(self):  # GENERATED!
        self.unknown4 = []

    def LoadData(self, br):
        self.unknown = br.ReadWORD()
        self.packetCount = br.ReadWORD()
        self.offsetToAttribs = br.ReadWORD()
        self.firstMatrixData = br.ReadWORD()
        self.firstPacketLocation = br.ReadWORD()
        self.unknown3 = br.ReadWORD()
        for j in range(7) :
            self.unknown4.append(br.GetFloat())


class Shp1Header:
    """# <variable tag>
    # -- char[4]
    # <variable sizeOfSection>
    # -- u32 
    # <variable batchCount>
    # -- u16 number of batches 
    # <variable pad>
    # -- u16 ??
    # <variable offsetToBatches>
    # -- u32 should be 0x2c (batch info starts here)
    # <variable offsetUnknown>
    # -- u32 ??
    # <variable zero>
    # -- u32 ??
    # <variable offsetToBatchAttribs>
    # -- u32 batch vertex attrib start
    # --The matrixTable is an array of u16, which maps from the matrix data indices
    # --to Drw1Data arrays indices. If a batch contains multiple packets, for the
    # --2nd, 3rd, ... packet this array may contain 0xffff values, which means that
    # --the corresponding index from the previous packet should be used.
    # <variable offsetToMatrixTable>
    # -- u32 
    # <variable offsetData>
    # -- u32 start of the actual primitive data
    # <variable offsetToMatrixData>
    # -- u32 
    # <variable offsetToPacketLocations>
    # -- u32 offset to packet start/length info
    # --(all offsets relative to Shp1Header start)
    # <function>"""

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
        self.offsetToMatrixTable = br.ReadDWORD()

        self.offsetData = br.ReadDWORD()
        self.offsetToMatrixData = br.ReadDWORD()
        self.offsetToPacketLocations = br.ReadDWORD()
# ---------------------------------------------------------------------------------------------------------------------


class Shp1BatchAttrib:
    # <variable attrib>
    # --u32 cf. ArrayFormat.arrayType
    # <variable dataType>
    # --u32 cf. ArrayFormat.dataType (always bytes or shorts...)
    # <function>

    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
                
        self.attrib = br.ReadDWORD()
        self.dataType= br.ReadDWORD()


        #-----------------------------------------
        #--for every packet a PacketLocation struct is stored at
        #--Shp1Header.offsetToPacketLocation + Batch.firstPacketLocation*sizeof(PacketLocation).
        #--This struct stores where the primitive data for this packet is stored in the
        #--data block.


class Shp1PacketLocation:
    # <variable size>
    # --u32 size in bytes of packet
    # <variable offset>
    # --u32 relative to Shp1Header.offsetData
    # <function>

    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        self.size = br.ReadDWORD()
        self.offset = br.ReadDWORD()
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
    # --from yaz0r's source (animation stuff)
    # <variable unknown1>
    # --u16 
    # <variable count>
    # --u16 count many consecutive indices into matrixTable
    # <variable firstIndex>
    # --u32 first index into matrix table
    # <function>

    # <function>

    def __init__(self):  # GENERATED!
        pass

    def StructSize(self):
        return 8

    def LoadData(self, br):
        self.unknown1 = br.ReadWORD()         # -- TODO: figure this out...
        self.count = br.ReadWORD()
        self.firstIndex = br.ReadDWORD()
# ---------------------------------------------------------------------------------------------------------------------


class Shp1:
    # <variable batches>
    # -- std::vector<ShpBatch> 
    # -- return Shp1BatchAttrib[]
    # <function>

    # -- TODO: unknown data is missing, ...
    # -- void dumpBatch(const bmd::Batch& batch, const bmd::Shp1Header& h, FILE* f, long baseOffset, Batch& dst)
    # <function>

    # -- end fn dumpBatch 
    # <function>

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

        for i in range(2):
            if len(dst.attribs.hasColors) <= i:
                dst.attribs.hasColors.append(None)
            dst.attribs.hasColors[i] = False

        for i in range(8):
            if len(dst.attribs.hasTexCoords) <= i:
                dst.attribs.hasTexCoords.append(None)
            dst.attribs.hasTexCoords[i] = False

        for i in range(len(attribs)):
            if attribs[i].dataType not in (1, 3):
                # --print "Warning: shp1, dumpBatch(): unknown attrib data type %d, skipping batch"
                MessageBox("Warning: shp1, dumpBatch(): unknown attrib data type %d, skipping batch")
                return None

            if attribs[i].attrib == 0:
                dst.attribs.hasMatrixIndices = True
            elif attribs[i].attrib == 9:
                dst.attribs.hasPositions = True
            elif attribs[i].attrib == 0xa:
                dst.attribs.hasNormals = True
            elif attribs[i].attrib == 0xb or attribs[i].attrib == 0xc:
                dst.attribs.hasColors[(attribs[i].attrib - 0xb)] = True # fixed
            elif attribs[i].attrib == 0xd or\
                 attribs[i].attrib == 0xe or\
                 attribs[i].attrib == 0xf or\
                 attribs[i].attrib == 0x10 or\
                 attribs[i].attrib == 0x11 or\
                 attribs[i].attrib == 0x12 or\
                 attribs[i].attrib == 0x13 or\
                 attribs[i].attrib == 0x14:
                dst.attribs.hasTexCoords[(attribs[i].attrib- 0xd)] = True  # fixed
            else:
                print("Warning: shp1, dumpBatch(): unknown attrib %d in batch, it might not display correctly")
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
