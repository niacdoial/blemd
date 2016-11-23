#! /usr/bin/python3
#     -- loads correctly: count=113, offsetToW=20, offsetToD=134 [20 + 113 = 133 (nextBit = offsetToD)]


class Drw1Header:
    """# <variable tag>
    # -- char[4]
    # <variable sizeOfSection>
    # -- u32 
    # <variable count>
    # -- u16  
    # <variable pad>
    # -- u16 
    # --stores for each matrix if it's weighted (normal (0)/skinned (1) matrix types)
    # <variable offsetToIsWeighted>
    # -- u32 
    # --for normal (0) matrices, this is an index into the global matrix
    # --table (which stores a matrix for every joint). for skinned
    # --matrices (1), I'm not yet totally sure how this works (but it's
    # --probably an offset into the Evp1-array)
    # <variable offsetToData>
    # -- u32 
    # <function>"""

    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        self.tag = br.ReadFixedLengthString(4)
        self.sizeOfSection = br.ReadDWORD()
        self.count = br.ReadWORD()
        self.pad = br.ReadWORD()
        self.offsetToIsWeighted = br.ReadDWORD()
        self.offsetToData = br.ReadDWORD()
  

class Drw1:
    # <variable isWeighted>
    # -- std::vector<bool> isWeighted;
    # <variable data>
    # -- std::vector<u16> data;
    # <function>

    def __init__(self):  # GENERATED!
        self.data= []
        self.isWeighted= []

    def LoadData(self, br):
                
        drw1Offset = br.Position()

        header = Drw1Header()
        header.LoadData(br)

        # -- read bool array
        self.isWeighted = []
        # -- self.isWeighted.resize(h.count);
        br.SeekSet(drw1Offset + header.offsetToIsWeighted)
        for _ in range(header.count):
            v = br.GetByte()  # -- u8 v; fread(&v, 1, 1, f);

            if v == 0:
                self.isWeighted.append(False)
            elif v == 1:
                self.isWeighted.append(True)
            else:
                raise ValueError("drw1: unexpected value in isWeighted array: " + str(v))

        # -- read self.data array
        self.data = []
        # -- dst.self.data.resize(h.count);
        br.SeekSet(drw1Offset + header.offsetToData)
        for _ in range(header.count):
            self.data.append(br.ReadWORD())
