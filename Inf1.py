#! /usr/bin/python3
#     -- only used during file load


class Inf1Header:
    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        self.tag = br.ReadFixedLengthString(4)
        self.sizeOfSection = br.ReadDWORD()
        self.unknown1 = br.ReadWORD()
        self.pad = br.ReadWORD()  # 0xffff
        self.unknown2 = br.ReadDWORD()
        self.vertexCount = br.ReadDWORD()
        # number of coords in VTX1 section
        self.offsetToEntries = br.ReadDWORD()
        # offset relative to Inf1Header start
    # only used during file load
    # This stores the scene graph of the file


class Inf1Entry:
    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        # 0x10: Joint
        # 0x11: Material
        # 0x12: Shape (ie. Batch)
        # 0x01: Hierarchy down (insert node), new child
        # 0x02: Hierarchy up, close child
        # 0x00: Terminator
        self.type = br.ReadWORD()
        # Index into Joint, Material or Shape table
        # always zero for types 0, 1 and 2
        self.index = br.ReadWORD()


class SceneGraph:
    def __init__(self):
        self.type = 0
        self.index = 0
        self.children = []



class Inf1:
    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
                
        inf1Offset = br.Position()
        self.scenegraph = []  # -- vector<Inf1Entry>
        header = Inf1Header()
        header.LoadData(br)
        self.numVertices = header.vertexCount  # int no idea what's this good for ;-)

        # -- read scene graph
        br.SeekSet(inf1Offset + header.offsetToEntries)

        entry = Inf1Entry()
        entry.LoadData(br)

        while entry.type != 0:
            self.scenegraph.append(entry)
            entry = Inf1Entry()
            entry.LoadData(br)


        

  

