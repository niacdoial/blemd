#! /usr/bin/python3
from mathutils import Vector
import mathutils
import logging
from . import common
import math
log = logging.getLogger('bpy.ops.import_mesh.bmd.vtx1')


class VertColor:
    # -- unsigned char 
    # <variable r>
    # <variable g>
    # <variable b>
    # <variable a>
    # -- all params are floats, must cast to char
    # <function>

    def __init__(self):  # GENERATED!
        pass

    def SetRGBA(self, ri, gi, bi, ai):
        log.debug("useless func!")
        # -- TODO
        # --self.r = (unsigned char)(ri + .5f);
        # --self.g = (unsigned char)(gi + .5f);
        # --self.b = (unsigned char)(bi + .5f);
        # --self.a = (unsigned char)(ai + .5f);


class TexCoord:
    # <variable s>
    # <variable t>
    # -- float 
    # <function>

    def __init__(self):  # GENERATED!
        pass

    def SetST(self, si, ti):
        self.s = si
        self.t = ti
  

class ArrayFormat:
    """# -- see ogc/gx.h for a more complete list of these values:
    # <variable arrayType>
    # -- u32 9: coords, a: normal, b: color, d: tex0 (gx.h: "Attribute")
    # <variable componentCount>
    # -- u32 meaning depends on dataType (gx.h: "CompCount")
    # <variable dataType>
    # -- u32 3: s16, 4: float, 5: rgba8 (gx.h: "CompType")
    # -- values i've seem for this: 7, e, 8, b, 0
    # ---> number of mantissa bits for fixed point numbers!
    # -- (position of decimal point)
    # <variable decimalPoint>
    # -- u8 
    # <variable unknown3>
    # -- u8 seems to be always 0xff
    # <variable unknown4>
    # -- u16 seems to be always 0xffff
    # <function>"""

    def __init__(self):  # GENERATED!
        pass

    def LoadData(self, br):
        self.arrayType = br.ReadDWORD()
        self.componentCount = br.ReadDWORD()
        self.dataType = br.ReadDWORD()
        self.decimalPoint = br.GetByte()
        self.unknown3 = br.GetByte()
        self.unknown4 = br.ReadWORD()
  

class Vtx1Header:
    # <variable tag>
    # -- char[4] 'VTX1'
    # <variable sizeOfSection>
    # -- u32 
    # <variable arrayFormatOffset>
    # -- u32 for each offsets[i] != 0, an ArrayFormat
    # -- is stored for that offset
    # -- offset relative to Vtx1Header start
    #
    #    content is described by ArrayFormat - for each offset != 0,
    #    an ArrayFormat struct is stored at Vtx1Header.arrayFormatOffset
    #      # <variable offsets>
    # -- u32[13]  offsets relative to Vtx1Header start
    # <function>

    # <function>

    def __init__(self):  # GENERATED!
        self.offsets= []

    def LoadData(self, br):
        self.tag = br.ReadFixedLengthString(4)
        self.sizeOfSection = br.ReadDWORD()
        self.arrayFormatOffset = br.ReadDWORD()
        for _ in range(13):
            self.offsets.append(br.ReadDWORD())

    def GetLength(self, offsetIndex):
        startOffset = self.offsets[offsetIndex]
        for i in range(offsetIndex + 1, 13):
            # --  for(int i = k + 1; i < 13; ++i)
            if self.offsets[i] != 0:
                return self.offsets[i] - startOffset
        return self.sizeOfSection - startOffset


class Vtx1:
    """# <variable positions>
    # -- std::vector<Vector3f> 
    # <variable normals>
    # -- std::vector<Vector3f>
    # <variable colors>
    # -- std::vector<Color> colors[2] 
    # <variable texCoords>
    # -- std::vector<TexCoord> texCoords[8]  
    # -- pass in floats. Round up?
    # <function>

    # --void readVertexArray(Vtx1& arrays, const bmd::ArrayFormat& af, int length,
    # --                  FILE* f, long offset)
    # <function>

    # <function>"""

    def __init__(self, UVoffset=0):  # GENERATED!
        self.positions= []
        self.colors= []
        self.texCoords= [[],[],[],[],[],[],[],[]]
        self.normals= []
        self.UVoffset = UVoffset  # DEBUG OPTION

    def GetColor(self, ri, gi, bi, ai):
                
        #r = (ri + 0.5)
        #g = (gi + 0.5)
        #b = (bi + 0.5)
        #a = (ai + 0.5)
        return (ri/255, gi/255, bi/255, ai/255)
        # return color r g b a # XCX need color format
  

    def ReadVertexArray(self, af, length, br, offset):
        br.SeekSet(offset)
        # ----------------------------------------------------------------------
        # -- convert array to float (so we have n + m cases, not n*m)
        data = []
        # -- vector<float>

         # -- print ("af.dataType=" + (af.dataType as string) + ": af.arrayType=" + (af.arrayType as string)  )

        if af.dataType == 3:  # u16
            tmp = []
            # -- size = length/2
            count = length/2
            if int(count) != count:
                if common.GLOBALS.PARANOID:
                    raise ValueError('invalid count (length not even)')
                else:
                    log.error('invalid array length. last point will use whatever is neext in file')
            count = int(count)
            scale = 1/(2**af.decimalPoint)
            tmp = [-1] * count
            data = tmp.copy()
            for i in range(count):
                tmp[i] = br.GetSHORT()
                data[i] = tmp[i]*scale
            # --throw "TODO: testing"
            # --messageBox "3"

        elif af.dataType == 4:  # f32
            count = length/4
            if int(count) != count:
                if common.GLOBALS.PARANOID:
                    raise ValueError('invalid count (length not *4)')
                else:
                    log.error('invalid array length. last point will use whatever is neext in file')
            count = int(count)
            for _ in range(count):
                data.append(br.GetFloat())
            # --throw "TODO: testing2"
            # --print (format "ZZZ % %" length count )

        elif af.dataType == 5:  # rgb(a)
            tmp = []
            # -- size = length
            for _ in range(length):
                data.append(br.GetByte())
            # --messageBox "Vtx1: af.dataType == 5. NYI"

        else:
            if common.GLOBALS.PARANOID:
                raise ValueError('unknown array type %d' % af.dataType)
            else:
                log.warning("unknown array data type %d", af.dataType)

        # --print "DATA: "
        # --print data
        # ----------------------------------------------------------------------
        # -- stuff floats into appropriate vertex array
        if af.arrayType == 9:  # -- positions
            if af.componentCount == 0 :  # -- xy [Needs testing]
                self.positions = []
                posCount = len(data) / 2
                if int(posCount) != posCount:
                    if common.GLOBALS.PARANOID:
                        raise ValueError('invalid posCount (length not even)')
                    else:
                        log.error('invalid array posCount. last point will use whatever is neext in file')
                    
                posCount = math.ceil(posCount)
                k = 0
                for j in range(posCount):
                    pos = Vector((data[k], data[k+1], 0))
                    self.positions.append(pos)
                    k += 2
                log.info("DT %d %d. Needs testings", af.dataType, af.componentCount)

            elif af.componentCount == 1:  # -- xyz

                self.positions = []
                posCount = len(data) / 3
                if int(posCount) != posCount:
                    log.info("amount of position coordinates (%d) is not //3", len(data))
                    for com in range(int(posCount - int(posCount)*3)):
                        data.append(None)
                #raise ValueError('invalid posCount (length not *3)')
                posCount = int(posCount)
                k = 0
                for _ in range(posCount):
                    pos = Vector((data[k], data[k+1], data[k+2]))
                    self.positions.append(pos)
                    # pos.setXYZFlip(data[k], data[k+1], data[k+2])
                    k += 3
                if len(data) - posCount*3 == 1:
                    pos = Vector((data[-2], data[-1], max(data) * 2))
                    self.positions.append(pos)

                if len(data) - posCount*3 == 2:
                    pos = Vector((data[-1], max(data)*2, max(data)*2))
                    self.positions.append(pos)
            # --
            # --print (format "LEN %. COUNT %" length (data.count / 3))
            # --print self.positions

            # --messagebox (format "DT % %" af.dataType af.componentCount)

            else:
                log.warning("unsupported componentCount for self.positions array")
                # --messageBox (format "vtx1: unsupported componentCount for self.positions array: %" af.componentCount)

        elif af.arrayType == 0xa:  # -- normals TODO: Test [0xa=10]
            if af.componentCount == 0:  # -- xyz
                normalsCount = len(data) // 3
                if normalsCount != len(data):
                    log.info("length of normal coordinates (%d) is not //3", len(data))
                self.normals = []
                # -- arrays.self.normals.resize(data.size()/3);
                k = 0
                for _ in range(normalsCount):
                    utmp = Vector((data[k], data[k+1], data[k+2]))
                    self.normals.append(utmp)
                    k += 3

                if len(data) - normalsCount*3 == 1:
                    pos = Vector((data[-2], data[-1], max(data) * 2))
                    self.normals.append(pos)

                if len(data) - normalsCount*3 == 2:
                    pos = Vector((data[-1], max(data)*2, max(data)*2))
                    self.normals.append(pos)
                    # --for(int j = 0, k = 0; j < arrays.self.normals.size(); ++j, k += 3)
                    # --  arrays.self.normals[j].setXYZ(data[k], data[k + 1], data[k + 2]);
            else:
                if common.GLOBALS.PARANOID:
                    raise ValueError("vtx1: unsupported componentCount for normals array")
                else:
                    log.warning("unsupported componentCount for normals array")


        elif af.arrayType == 0xb or af.arrayType == 0xc:  # -- color0 or color1
            index = af.arrayType - 0xb
            if len(self.colors) <= index:
                self.colors.append(list())
            if af.componentCount == 0:  # -- rgb
                # -- self.colors[data.count / 3] = 0 --initialize???
                colorCount = len(data) // 3
                k = 1
                for j in range(colorCount):
                    self.colors[index].append(self.GetColor(data[k], data[k+1], data[k+2], 255))
                    k += 3
            elif af.componentCount == 1:  # -- rgba
                self.colors[index] = []
                colorCount = len(data) // 4
                k = 0  # fixed
                for j in range(colorCount):
                    self.colors[index].append(self.GetColor(data[k], data[k+1], data[k+2], data[k+3]))
                    k += 4

            else:
                if common.GLOBALS.PARANOID:
                    raise ValueError("vtx1: unsupported componentCount for colors array")
                else:
                    log.warning("unsupported componentCount for colors array")
        # -- texcoords 0 - 7 [13]

        elif af.arrayType == 0xd or\
             af.arrayType == 0xe or\
             af.arrayType == 0xf or\
             af.arrayType == 0x10 or\
             af.arrayType == 0x11 or\
             af.arrayType == 0x12 or\
             af.arrayType == 0x13 or\
             af.arrayType == 0x14:
            # -- std::vector<TexCoord> self.texCoords[8] self.texCoords
            index = (af.arrayType - 0xd)
            if af.componentCount == 0:  # --s
                # self.texCoords[index] = []  # DONE BEFORE
                # -- self.texCoords[index].resize(data.size());
                for j in range(len(data)):
                    utmp = TexCoord()
                    utmp.SetST(data[j], 0)
                    self.texCoords[index].append(utmp)

                # --for(int j = 0; j < arrays.self.texCoords[index].size(); ++j)
                # --  arrays.self.texCoords[index][j].setST(data[j], 0);

            elif af.componentCount == 1:  # -- st
                texCount = len(data)//2
                if texCount * 2 != len(data):
                    log.warning("wrong length of UV coords (not even)")
                # self.texCoords[index] = []
                # -- arrays.self.texCoords[index].resize(data.size()/2);

                k = 0  # fixed
                for j in range(texCount):
                    utmp = TexCoord()
                    utmp.SetST(data[k], data[k+1])
                    self.texCoords[index].append(utmp)
                    k += 2
                # --for(int j = 0, k = 0; j < arrays.self.texCoords[index].size(); ++j, k += 2)
                # --   arrays.self.texCoords[index][j].setST(data[k], data[k + 1]);

            else:
                if common.GLOBALS.PARANOID:
                    raise ValueError("vtx1: unsupported componentCount for texcoords array")
                else:
                    log.warning('unsupported componentCount for texcoords array')
        else:
            if common.GLOBALS.PARANOID:
                raise ValueError("WRONG ArrayType in VTX1")
            else:
                log.warning('WRONG ArrayType in VTX1')

    def LoadData(self, br):
                
        vtx1Offset = br.Position()

        header = Vtx1Header()
        header.LoadData(br)  # gets 64 bytes

        # --messageBox "x"
        numArrays = 0
        for i in range(13):
            if header.offsets[i]:
                numArrays += 1
        # -- read vertex array format descriptions
        formats = []
        # -- vector<bmd::ArrayFormat>
        for i in range(numArrays):
            af = ArrayFormat()
            af.LoadData(br)
            formats.append(af)
        # -- read arrays
        br.SeekSet(vtx1Offset + header.arrayFormatOffset)  # ? returns back?

        j = 0
        for i in range(13):
            if header.offsets[i]:
                f = formats[j]
                len = header.GetLength(i)
                # print("Vert "+str(i)+":"+str(len))
                if f.arrayType >= 0xd:  # UV coords
                    self.ReadVertexArray(f, len, br, (vtx1Offset+header.offsets[i]+self.UVoffset))
                else:
                    self.ReadVertexArray(f, len, br, (vtx1Offset+header.offsets[i]))
                j += 1


# small iter-generators to iterate triangles from GL_strips and GL_fans.
def StripIterator(lst):
    if False and common.GLOBALS.no_rot_conversion:
        flip = True
    else:
        flip = False  # odd faces are in reversed index
    for com in range(len(lst)-2):
        if flip:
            yield (lst[com], lst[com+1], lst[com+2])  # correct order to have correct normals
        else:
            yield (lst[com+2], lst[com+1], lst[com])
        flip = not flip


def FanIterator(lst):
    log.warning('This is a fan!')
    if False and common.GLOBALS.no_rot_conversion:
        for com in range(1, len(lst)-1):
            yield (lst[0], lst[com], lst[com+1])  # faces need to be described like this in order to have correct normals
    else:
        for com in range(1, len(lst)-1):
            yield (lst[0], lst[com+1], lst[com])  # faces need to be described like this in order to have correct normals


def findFace(model, facelist, v0, v1, v2, exclude):
    for face in facelist:
        fv0, fv1, fv2 = model.getVerts(face)
        if exclude==2:
            if fv0 == v0 and fv1 == v1 and fv2 != v2:
                return face
        elif exclude == 0:
            if fv0 != v0 and fv1 == v1 and fv2 == v2:
                return face
        else:
            log.critical("findFace wasn't meant to exclude second vert in match. ***report bug***")
            raise ValueError('~the dev is an idiot~')
    return None


def getStrip(model, facelist, startFace, v0, v1, v2):
    stFaces = [startFace]
    stVerts = [v2, v1, v0]  # first face is in reverse order
    stLoops = [model.getLoop(startFace, 2),
               model.getLoop(startFace, 1),
               model.getLoop(startFace, 0)]

    # faces have to be found from the 2->1 edge of the previous triangle (on their 1->2)
    # or from the 1->0 edge of the previous triangle (on their 0->1), alternatively.
    newFace = findFace(model, facelist, v0, v1, v2)  # second face found from 2->1
    flip = False  # odd faces from 1->0 (False), even faces from 2->1 (True)
    while newFace is not None:
        stFaces.append(newFace)
        fv0, fv1, fv2 = model.getVerts(newFace)
        if flip:  # order: 2-1-0. append 0
            stVerts.append(fv0)
            stLoops.append(model.getLoop(newFace, 0))
            flip = False
            newFace = findFace(model, facelist, fv1, fv0, fv2, 2)  # find (odd face) from 1->0 on 0->1
        else:  # order: 0-1-2. append 2
            stVerts.append(fv2)
            stLoops.append(model.getLoop(newFace, 2))
            flip = True
            newFace = findFace(model, facelist, fv0, fv2, fv1, 0)  # find (even face) from 2->1 on 1->2
    return (stFaces, stLoops)


def makestrips(model, facelist):
    # notice : this function operates under the asumption that the faces make a somewhat manifold mesh,
    # but won't crash if otherwise : it will only cause optimisation problems
    strips = []
    while facelist:
        # generate a single strip from the first face of the facelist
        face = facelist[0]
        v0 = model.getLoop(face, 0).vertex
        v1 = model.getLoop(face, 1).vertex
        v2 = model.getLoop(face, 2).vertex

        # starting from a single face, there are three strips that can be made.
        st0 = getStrip(model, facelist, face, v0, v1, v2)
        st1 = getStrip(model, facelist, face, v1, v2, v0)
        st2 = getStrip(model, facelist, face, v2, v0, v1)

        # only get the longest
        if len(st0[0]) >= len(st1[0]):
            st3 = st0
        else:
            st3 = st1
        if len(st3[0]) >= len(st2[0]):
            st = st3
        else:
            st = st2

        strips.append(st)

        # exclude strip faces from future strips
        for face in st[0]:
            facelist.remove(face)

    return strips