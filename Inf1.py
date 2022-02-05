#! /usr/bin/python3

from math import ceil
import logging
log = logging.getLogger('bpy.ops.import_mesh.bmd.inf1')

class Inf1Header:
    size = 24

    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        self.tag = br.ReadFixedLengthString(4)
        self.sizeOfSection = br.ReadDWORD()
        self.unknown1 = br.ReadWORD()
        self.pad = br.ReadWORD()  # 0xffff
        self.packetCount = br.ReadDWORD()
        self.vertexCount = br.ReadDWORD()
        # number of coords in VTX1 section
        self.offsetToEntries = br.ReadDWORD()
        # offset relative to Inf1Header start
    # only used during file load
    # This stores the scene graph of the file

    def DumpData(self, bw):
        bw.writeString("INF1")
        bw.writeDword(self.sizeOfSection)
        bw.writeWord(self.unknown1)
        bw.writeWord(self.pad)  # 0xffff
        bw.writeDword(self.packetCount)
        bw.writeDword(self.vertexCount)
        # number of coords in VTX1 section
        bw.writeDword(self.offsetToEntries)

class Inf1Entry:
    size = 4
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

    def DumpData(self, bw):
        bw.writeWord(self.type)
        bw.writeWord(self.index)
        # see LoadDate for meaning


class SceneGraph:
    def __init__(self):
        self.type = 0
        self.index = 0
        self.children = []
        # this var is only used as cache for the export process
        self.material = None



class Inf1:
    def __init__(self):  # GENERATED!
        self.rootSceneGraph = SceneGraph()

    def buildSceneGraph(self, sg, j=0):
        """builds sceneGraph tree from inf1 descriptors in an array"""
        i = j
        while i < len(self.entries):
            n = self.entries[i]
            if n.type == 1:
                i += self.buildSceneGraph(sg.children[-1], i+1)
            elif n.type == 2:
                return i - j + 1
            elif n.type == 0x10 or n.type == 0x11 or n.type == 0x12:
                t = SceneGraph()
                t.type = n.type
                t.index = n.index
                sg.children.append(t)
            else:
                log.error("buildSceneGraph(): unexpected node type %d", n.type)
            i += 1

        # note: this code can only be reached by the top level function,
        # AKA the one where the loops end by itself
        # return first "real" node
        if len(sg.children) == 1:
            return sg.children[0]
        else:
            sg.type = sg.index = -1
            log.error("buildSceneGraph(): Unexpected size %d for root SG", len(sg.children))
        return 0

    def extractEntries(self, sg, dest):
        e = Inf1Entry()
        e.type = sg.type
        e.index = sg.index

        dest.append(e)
        relation_e = Inf1Entry()
        relation_e.type = 0x01  # down
        relation_e.index = 0
        for s2 in sg.children:
            self.extractEntries(s2, dest)
        relation_e = Inf1Entry()
        relation_e.type = 0x02  # up
        relation_e.index = 0  # XCX are all the end delimitors here?



    def LoadData(self, br):
                
        inf1Offset = br.Position()
        self.entries = []  # -- vector<Inf1Entry>
        header = Inf1Header()
        header.LoadData(br)
        self.numVertices = header.vertexCount  # int no idea what's this good for ;-)

        # -- read scene graph
        br.SeekSet(inf1Offset + header.offsetToEntries)

        entry = Inf1Entry()
        entry.LoadData(br)

        while entry.type != 0:
            self.entries.append(entry)
            entry = Inf1Entry()
            entry.LoadData(br)

        self.rootSceneGraph = self.buildSceneGraph(self.rootSceneGraph)


    def DumpData(self, bw):
        inf1Offset = bw.Position()
        self.entries = []
        self.extractEntries(self.rootSceneGraph, self.entries)  # vector<Inf1Entry>

        temp_e = Inf1Entry()
        temp_e.type = temp_e.index = 0
        self.entries.append(temp_e)

        header = Inf1Header()
        header.sizeOfSection = 0
        header.unknown1 = 0
        header.pad = 0xffff
        header.packetCount = 0
        header.vertexCount = self.numVertices
        header.offsetToEntries = bw.addPadding(Inf1Header.size)

        header.DumpData(bw)
        bw.writePadding(header.offsetToEntries - Inf1Header.size)

        # -- read scene graph

        if inf1Offset + header.offsetToEntries != bw.Position():
            raise ValueError('something went wrong with the sizes in inf1')

        for entry in self.entries:
            entry.DumpData(bw)

        bw.writePaddingTo16()

        header.sizeOfSection = bw.Position() - inf1Offset
        bw.SeekSet(inf1Offset + 4)
        bw.writeDword(header.sizeOfSection)

        bw.SeekSet(inf1Offset + header.sizeOfSection)
