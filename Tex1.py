#! /usr/bin/python3
class ImageHeader:
    # <variable data>
    # -- Image* 
    # <variable name>
    # -- std::string 
    #
    #    from gx.h:
    #    0: clamp to edge
    #    1: repeat
    #    2: mirror
    #      # <variable wrapS>
    # <variable wrapT>
    # -- u8
    # --TODO: unknow fields
    def __init__(self):  # GENERATED!
        pass
# ------------------------------------------------------------------------------------------------


class Image:
    """# <variable format>
    # -- int
    # <variable width>
    # <variable height>
    # -- int
    # <variable mipmaps>
    # --std::vector<u8*>  points into imageData
    # <variable sizes>
    # -- std::vector<int> image data size for each mipmap
    # <variable imageData>
    # -- std::vector<u8> 
    #
    #  //NOTE: palettized images are converted
    #  //to non-palettized images during load time,
    #  //i4 and i4a4 are converted to i8 and i8a8
    #  //(i8a8 is then converted to a8i8 for opengl),
    #  //r5g5b5a3 and r5g6b5 to rgba8 (actually, to agbr8,
    #  //that is rgba8 backwards - for opengl. rgba8
    #  //is converted to agbr8 as well).
    #  //(that is, only formats 1, 3, 6 and 14 are
    #  //used after conversion)
    #    # --TODO: gl image conversions (rgba -> abgr, ia -> ai
    # --somewhere else?)
    # --TODO: this is temporary and belongs somewhere else:
    # <variable texId>
    # -- unsigned int """
    def __init__(self):  # GENERATED!
        self.mipmaps = []
        self.sizes = []
        self.imageData = []
# ------------------------------------------------------------------------------------------------
# -- header format for 'bmd3' files, seems to be slightly different for 'jpa1'


class Tex1Header:
    """# <variable tag>
    # --char [4]  'TEX1'
    # <variable sizeOfSection>
    # -- u32
    # <variable numImages>
    # -- u16
    # <variable unknown>
    # -- u16 padding, usually 0xffff
    # <variable textureHeaderOffset>
    # -- u32numImages bti image headers are stored here (see bti spec)
    # --note: several image headers may point to same image data
    # --offset relative to Tex1Header start
    # <variable stringTableOffset>
    # -- u32stores one filename for each image (TODO: details on stringtables)
    # --offset relative to Tex1Header start  
    # <function>"""
    def __init__(self):  # GENERATED!
        self.tag = None
        self.sizeOfSection = None
        self.numImages = 0
        self.unknown = None
        self.textureHeaderOffset = None
        self.stringTableOffset = None

    def LoadData(self, br):
        self.tag = br.ReadFixedLengthString(4)
        self.sizeOfSection = br.ReadDWORD()
        self.numImages = br.ReadWORD()
        self.unknown = br.ReadWORD()
        self.textureHeaderOffset = br.ReadDWORD()
        self.stringTableOffset = br.ReadDWORD()
# ------------------------------------------------------------------------------------------------


class TextureHeader:
    """# <variable format>
    # -- u8data format - seems to match tpl's format (see yagcd)
    # <variable unknown>
    # -- u8
    # <variable width>
    # -- u16 
    # <variable height>
    # -- u16
    #
    #    from gx.h:
    #    0: clamp to edge
    #    1: repeat
    #    2: mirror
    #      # <variable wrapS>
    # -- u8
    # <variable wrapT>
    # -- u8 
    # <variable unknown3>
    # --   u8
    # <variable paletteFormat>
    # -- u8 palette format - matches tpl palette format (-> yagcd)
    # <variable paletteNumEntries>
    # -- u16
    # <variable paletteOffset>
    # -- u32 palette data
    # <variable unknown5>
    # -- u32
    # <variable unknown6>
    # -- u16 prolly two u8s, first is 5 or 1, second 1 most of the time
    # <variable unknown7>
    # -- u16 0 most of the time, sometimes 0x10, 0x18, 0x20, 0x28
    # <variable mipmapCount>
    # -- u8
    # <variable unknown8>
    # -- u8
    # <variable unknown9>
    # -- u16
    # <variable dataOffset>
    # -- u32 image data
    # --some of the unknown data could be render state?
    # --(lod bias, min/mag filter, clamp s/t, ...)
    # <function>"""
    def __init__(self):  # GENERATED!
        pass
    def LoadData(self, br):
        self.format = br.GetByte()
        self.unknown = br.GetByte()
        self.width = br.ReadWORD()
        self.height = br.ReadWORD()
        self.wrapS = br.GetByte()
        self.wrapT = br.GetByte()
        self.unknown3 = br.GetByte()
        self.paletteFormat = br.GetByte()
        self.paletteNumEntries = br.ReadWORD()
        self.paletteOffset = br.ReadDWORD()
        self.unknown5 = br.ReadDWORD()
        self.unknown6 = br.ReadWORD()
        self.unknown7 = br.ReadWORD()
        self.mipmapCount = br.GetByte()
        self.unknown8 = br.GetByte()
        self.unknown9 = br.ReadWORD()
        self.dataOffset = br.ReadDWORD()
# ------------------------------------------------------------------------------------------------
class Tex1:
    # --imageHeaders = #(), -- std::vector<ImageHeader> 
    # <variable texHeaders>
    # <variable stringtable>
    # --because several image headers might point to the
    # --same image data, this data is stored
    # --separately to save some memory
    # --(this way only about 1/6 of the memory required
    # --otherwise is used)
    # -- images = #(), -- std::vector<Image > 
    # <function>
    def __init__(self):  # GENERATED!
        self.texHeaders = []

    def LoadData(self, br):
        tex1Offset = br.Position()
        # -- read textureblock header
        h = Tex1Header()
        h.LoadData(br)
        # -- read self.stringtable
        self.stringtable = br.ReadStringTable (tex1Offset + h.stringTableOffset)         # -- readStringtable(tex1Offset + h.stringTableOffset, f, self.stringtable);


        if len(self.stringtable) != h.numImages :
            raise ValueError("tex1: number of strings doesn't match number of images")

          # -- read all image headers before loading the actual image
          # -- data, because several headers can refer to the same data
        br.SeekSet(tex1Offset + h.textureHeaderOffset)
        self.texHeaders = []
        imageOffsets = []

        for _ in range(h.numImages):
            texHeader = TextureHeader()
            texHeader.LoadData(br)
            self.texHeaders.append(texHeader)




