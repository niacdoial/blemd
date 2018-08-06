#! /usr/bin/python3
#     -- loads correctly: count=113, offsetToW=20, offsetToD=134 [20 + 113 = 133 (nextBit = offsetToD)]

class Part1Entry:
    def __init__(self, br):
        self.subpart1 = []
        subentry = br.read(5)
        while subentry[0] == 97:  # == b'a'
            self.subpart1.append(subentry)
            subentry = br.read(5)
        
        br.SeekSet(br.Position()-5)
        self.subpart2 = b''
        
        buffer = br.read(4)
        while True:  # break is used to end loop
            if buffer == b'\xff\xff\xff\xff':
                self.subpart2 += buffer
                buf2 = br.read(1)
                while buf2 == b'\xff':
                    self.subpart2 += buf2
                    buf2 = br.read(1)
                if self.subpart2[-8:] == 8 * b'\xff':
                    self.subpart2 += buf2
                    self.subpart2 += br.read(4*16)
                    while br.Position() % 16:
                        # next entry starts at the beginning of a line
                        self.subpart2 += br.read(1)
                    break
                else:
                    self.subpart2 += buf2
            else:
                self.subpart2 += buffer
            buffer = br.read(4)
        
        self.size = 5*len(self.subpart1) + len(self.subpart2)
        

class Part2Entry:
    def __init__(self, br):
        self.w1 = br.ReadWORD()  # 01 then {B1, F2}
        self.w2 = br.ReadWORD()  # 020C or 01CB
        self.w3 = br.ReadWORD()  # 01 then B3 or 9F
        self.d1 = br.ReadDWORD()  # 6E or 5A
        self.w4 = br.ReadDWORD()  # 0159 or 016D
        self.pad = br.ReadDWORD()  # 0xffff in theory
        
class Part3Entry:
    def __init__(self, br):
        self.d1 = br.ReadDWORD()
        self.d2 = br.ReadDWORD()
        # what the heck is it even?
        # 3C X1 X2 00 00 F3 CF 3C
        # known values of X1: {F2, F3}
        # known values of X2: {1F, CF}


class Mdl3Header:
    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        self.tag = br.ReadFixedLengthString(4)
        self.sizeOfSection = br.ReadDWORD()
        
        self.numberOfBones = br.ReadWORD()
        self.pad1 = br.ReadWORD()  # 0xffff
        if self.pad1 != 0xffff:
            print('sounds like mdl3.pad1 isn\'t padding after all')
        
        self.offsettosub1 = br.ReadDWORD()
        # list of offsets? (relative to this section)
        # each thing looks like some 5-bit sequences: a....
        # (terminated by a....[0x10])  , and a footer with some 0xff in it
        self.offsettopart2 = br.ReadDWORD()  # 1460  # some 16-byte sequences, ended with 0xffff
        self.offsettopart3 = br.ReadDWORD()  # 14F0  # 8-byte sections of <......<
        self.offsettopart4 = br.ReadDWORD()  # 1538  # 01 ad infinitum
        self.offsettopart5 = br.ReadDWORD()  # 1544  # range() of words? same enumber as bones
        self.offsettopart6 = br.ReadDWORD()  # 1558  # some stuff : len(4+NOB?)
        # then stringtable
        
        # plus stringtable?
        
        # next is paddung
  

class Mdl3:
    def __init__(self):
        pass

    def LoadData(self, br):
                
        mdl3Offset = br.Position()

        header = Mdl3Header()
        header.LoadData(br)
        
        br.SeekSet(mdl3Offset + header.offsettosub1)
        
        offsets = (header.numberOfBones * 2 +1) * [0]  # the extra slot is here to avoid crashes
        for i in range(header.numberOfBones * 2):
            offsets[i] = br.ReadDWORD()

        self.part1BaseOffset = offsets[0]

        self.unk1 = (header.numberOfBones-1) * [0]
        for i in range(header.numberOfBones-1):
            self.unk1[i] = offsets[2*i+2]


        # need to deal with the big blocks : 
        # each thing looks like some 5-bit sequences: a....
        # (terminated by a....[0x10])  , and a footer with some 0xff in it
        # same number as bones ?
        
        br.SeekSet(mdl3Offset + header.offsettosub1+self.part1BaseOffset)
        pos = br.Position()
        self.part1 = header.numberOfBones * [0]
        for i in range(header.numberOfBones):
            br.SeekSet(pos)
            self.part1[i] = Part1Entry(br)
            pos += offsets[2*i+1]


        br.SeekSet(mdl3Offset + header.offsettopart2)
        self.part2 = header.numberOfBones * [0]
        for i in range(header.numberOfBones):
            self.part2[i] = Part2Entry(br)   # some 16-byte sequences, ended with 0xffff
            
        br.SeekSet(mdl3Offset + header.offsettopart3)
        self.part3 = header.numberOfBones * [0]
        for i in range(header.numberOfBones):
            self.part3[i] = Part3Entry(br)  # 8-byte sections of <......<
            
        br.SeekSet(mdl3Offset + header.offsettopart4)
        self.part4 = header.numberOfBones * [0]
        for i in range(header.numberOfBones):
            self.part4[i] = br.GetByte()  # 01 ad infinitum
            
        br.SeekSet(mdl3Offset + header.offsettopart5)
        self.part5 = header.numberOfBones * [0]
        for i in range(header.numberOfBones):
            self.part5[i] = br.ReadWORD()  # range() so far
        
        self.stringtable = br.ReadStringTable(mdl3Offset + header.offsettopart6)
