#! /usr/bin/python3
#     -- only used during file load


class Inf1Header:
    """# <variable tag>
    # -- char[4] 'INF1'
    # <variable sizeOfSection>
    # -- u32 
    # <variable unknown1>
    # -- u16 
    # <variable pad>
    # -- u16  0xffff
    # <variable unknown2>
    # -- u32 
    # <variable vertexCount>
    # -- u32 number of coords in VTX1 section
    # <variable offsetToEntries>
    # -- u32 offset relative to Inf1Header start
    # <function>"""

    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        self.tag = br.ReadFixedLengthString(4)
        self.sizeOfSection = br.ReadDWORD()
        self.unknown1 = br.ReadWORD()
        self.pad = br.ReadWORD()
        self.unknown2 = br.ReadDWORD()
        self.vertexCount = br.ReadDWORD()
        self.offsetToEntries = br.ReadDWORD()
    # -- only used during file load
    # -- This stores the scene graph of the file


class Inf1Entry:
    # -- 0x10: Joint
    # -- 0x11: Material
    # -- 0x12: Shape (ie. Batch)
    # -- 0x01: Hierarchy down (insert node), new child
    # -- 0x02: Hierarchy up, close child
    # -- 0x00: Terminator
    # <variable type>
    # -- u16 
    # -- Index into Joint, Material or Shape table
    # -- always zero for types 0, 1 and 2
    # <variable index>
    # -- u16 
    # <function>

    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        self.type = br.ReadWORD()
        self.index = br.ReadWORD()


class SceneGraph:
    def __init__(self):
        self.type=0
        self.index=0
        self.children=[]

class Inf1:
    # <variable numVertices>
    # -- int no idea what's this good for ;-)
    # <variable scenegraph>
    # -- std::vector<Inf1Entry> scenegraph;
    # <function>
    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
                
        inf1Offset = br.Position()
        self.scenegraph = []  # -- vector<Inf1Entry>
        header = Inf1Header()
        header.LoadData(br)
        self.numVertices = header.vertexCount

        # -- read scene graph
        br.SeekSet (inf1Offset + header.offsetToEntries)

        entry = Inf1Entry()
        entry.LoadData(br)

        while entry.type != 0:
            self.scenegraph.append(entry)
            entry = Inf1Entry()
            entry.LoadData(br)


        

  

