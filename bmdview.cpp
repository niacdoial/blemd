//version 1.0 (20050215)
//by thakis

#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
#include <cassert>
using namespace std;

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

void toWORD(u16& w)
{
  u8 w1 = w & 0xff;
  u8 w2 = w >> 8;
  w = (w1 << 8) | w2;
}

void toDWORD(u32& d)
{
  u8 w1 = d & 0xff;
  u8 w2 = (d >> 8) & 0xff;
  u8 w3 = (d >> 16) & 0xff;
  u8 w4 = d >> 24;
  d = (w1 << 24) | (w2 << 16) | (w3 << 8) | w4;
}

#pragma pack(push, 1)

struct Tex1Header
{
  char tag[4]; //'TEX1'
  u32 size;
  u16 numImages;
  u16 unknown;
  u32 unknown2; //sizeof(Tex1Header)? Seems to be always 0x00000020
  u32 stringTableOffset;
  u8 padding[12];
};

struct TextureHeader
{
  u8 format;  //seems to match tpl's format (see yagcd)
  u8 unknown;
  u16 width;
  u16 height;
  u16 unknown2; //probably padding
  u32 unknown3;
  u32 unknown4; //probably offset to start of all image data
  u32 unknown5;
  u16 unknown6;
  u16 unknown7;
  u8 mipmapCount;
  u8 unknown8;
  u16 unknown9;
  u32 dataOffset;

  //some of the unknown data could be render state
  //(lod bias, min/mag filter, clamp s/t, ...)
};


//The following structures are for dds file saving...

struct ColorCaps
{
  u32 size;
  u32 flags;
  char fourCC[4];
  u32 rgbBitCount;
  u32 rBitMask;
  u32 gBitMask;
  u32 bBitMask;
  u32 aBitMask;
};

struct DdsHeader
{
  char type[4];
  u32 size;
  u32 flags;
  u32 height;
  u32 width;
  u32 linearSize;
  u32 depth;
  u32 numMips;
  u32 unused[11];
  ColorCaps colorCaps;
  u32 caps;
  u32 unused2[4];
};

#pragma pack(pop)

DdsHeader createDdsHeader(int w, int h, int numMips)
{
  DdsHeader ret;
  memset(&ret, 0, sizeof(ret));

  strncpy(ret.type, "DDS ", 4);
  ret.size = 124;
  ret.flags = 0x21007; //mipmapcount + pixelformat + width + height + caps
  ret.width = w;
  ret.height = h;
  ret.numMips = numMips;
  ret.colorCaps.size = 32;
  ret.caps = 0x401000; //mipmaps + texture
  return ret;
}

char* g_name = "";
std::string g_folder;

string getString(int pos, FILE* f)
{
  int t = ftell(f);
  fseek(f, pos, SEEK_SET);

  string ret;
  char c;
  while((c = fgetc(f)) != '\0')
    ret.append(1, c);

  fseek(f, t, SEEK_SET);

  return ret;
}

vector<string> dumpStringtable(const Tex1Header& h, const vector<TextureHeader>& texHeaders, FILE* f)
{
  vector<string> ret;

  fseek(f, h.stringTableOffset, SEEK_CUR);
  int fp = ftell(f);

  u16 numNames, unknown;
  fread(&numNames, 2, 1, f);
  fread(&unknown, 2, 1, f);
  toWORD(numNames);
  toWORD(unknown);

  assert(numNames == texHeaders.size());

  cout << endl << "Image names:" << endl;
  for(int i = 0; i < numNames; ++i)
  {
    u16 unknown2, nameOffset;
    fread(&unknown2, 2, 1, f);
    fread(&nameOffset, 2, 1, f);
    toWORD(unknown2);
    toWORD(nameOffset);

    string s = getString(fp + nameOffset, f);
    const TextureHeader& th = texHeaders[i];
    cout << hex << unknown2 << " " << s << endl;
    cout << dec << "  Width: " << th.width << ", Height: " << th.height << ", format " << (int)th.format << ", "
         << (int) th.mipmapCount << " mipmaps, offset: " << th.dataOffset << " = 0x" << hex << th.dataOffset << endl;
    cout << hex << "  " << (int)th.unknown << " " << th.unknown2 << " " << th.unknown3 << " " << th.unknown4
         << " " << th.unknown5 << " " << th.unknown6 << " " << th.unknown7 << " " << (int)th.unknown8 << " " << th.unknown9 << endl;
    ret.push_back(s);
  }
  return ret;
}

void s3tc1ReverseByte(u8& b)
{
  u8 b1 = b & 0x3;
  u8 b2 = b & 0xc;
  u8 b3 = b & 0x30;
  u8 b4 = b & 0xc0;
  b = (b1 << 6) | (b2 << 2) | (b3 >> 2) | (b4 >> 6);
}

int getBufferSize(u8 format, int w, int h, ColorCaps& cc)
{
  switch(format)
  {
    case 0: //i4
      //dds files don't support i4 - we convert to i8
      cc.flags = 0x20000; //luminance
      cc.rgbBitCount = 8;
      cc.rBitMask = 0xff;
      return w*h/2; //data is i4 in read buffer nevertheless
    case 1: //i8
      cc.flags = 0x20000; //luminance
      cc.rgbBitCount = 8;
      cc.rBitMask = 0xff;
      return w*h;
    case 2: //i4a4
      cc.flags = 0x20001; //alpha + luminance
      cc.rgbBitCount = 8;
      cc.rBitMask = 0xf;
      cc.aBitMask = 0xf0;
      return w*h;
    case 3: //i8a8
      cc.flags = 0x20001; //alpha + luminance
      cc.rgbBitCount = 16;
      cc.rBitMask = 0xff;
      cc.aBitMask = 0xff00;
      return w*h*2;
    case 4: //r5g6b5
      cc.flags = 0x40; //rgb
      cc.rgbBitCount = 16;
      cc.rBitMask = 0xf800;
      cc.gBitMask = 0x7e0;
      cc.bBitMask = 0x1f;
      return w*h*2;
    case 5: //gc homebrewn (rgb5a3)
      //this is a waste of memory, but there's no better
      //way to expand this format...
      cc.flags = 0x41; //rgb + alpha
      cc.rgbBitCount = 32;
      cc.rBitMask = 0xff0000;
      cc.gBitMask = 0xff00;
      cc.bBitMask = 0xff;
      cc.aBitMask = 0xff000000;
      return w*h*2; //data is rgb5a2 in read buffer nevertheless

    case 0xe: //s3tc1
      cc.flags = 0x4; //fourcc
      strncpy(cc.fourCC, "DXT1", 4);
      return w*h/2;

    default:
      return -1;
  }
}

void fix8x8Expand(u8* dest, const u8* src, int w, int h)
{
  //convert to i8 during block swapping
  int si = 0;
  for(int y = 0; y < h; y += 8)
    for(int x = 0; x < w; x += 8)
      for(int dy = 0; dy < 8; ++dy)
        for(int dx = 0; dx < 8; ++dx, ++si)
        {
          //http://www.mindcontrol.org/~hplus/graphics/expand-bits.html
          u8 t = (src[si/2] & 0xf);
          dest[w*(y + dy) + x + dx] = (t << 4) | t;
          t = src[si/2] & 0xf0;
          dest[w*(y + dy) + x + dx] = t | (t >> 4);
        }
}


void fix8x4(u8* dest, const u8* src, int w, int h)
{
  int si = 0;
  for(int y = 0; y < h; y += 4)
    for(int x = 0; x < w; x += 8)
      for(int dy = 0; dy < 4; ++dy)
        for(int dx = 0; dx < 8; ++dx, ++si)
          dest[w*(y + dy) + x + dx] = src[si];
}

void fix4x4(u16* dest, const u16* src, int w, int h)
{
  int si = 0;
  for(int y = 0; y < h; y += 4)
    for(int x = 0; x < w; x += 4)
      for(int dy = 0; dy < 4; ++dy)
        for(int dx = 0; dx < 4; ++dx, ++si)
          dest[w*(y + dy) + x + dx] = src[si];
  for(int i = 0; i < w*h; ++i)
    toWORD(dest[i]);
}

void fixRgb5A3(u32* dest, const u16* src, int w, int h)
{
  //convert to rgba8 during block swapping
  int si = 0;
  for(int y = 0; y < h; y += 4)
    for(int x = 0; x < w; x += 4)
      for(int dy = 0; dy < 4; ++dy)
        for(int dx = 0; dx < 4; ++dx, ++si)
        {
          u16 srcPixel = src[si];
          toWORD(srcPixel);
          u8 r, g, b, a;

          //http://www.mindcontrol.org/~hplus/graphics/expand-bits.html
          if((srcPixel & 0x8000) == 0x8000) //rgb5
          {
            a = 0xff;

            r = (srcPixel & 0x7c00) >> 10;
            r = (r << (8-5)) | (r >> (10-8));

            g = (srcPixel & 0x3e0) >> 5;
            g = (g << (8-5)) | (g >> (10-8));

            b = srcPixel & 0x1f;
            b = (b << (8-5)) | (b >> (10-8));
          }
          else //rgb4a3
          {
            a = (srcPixel & 0x7000) >> 12;
            a = (a << (8-3)) | (a << (8-6)) | (a >> (9-8));

            r = (srcPixel & 0xf00) >> 8;
            r = (r << (8-4)) | r;

            g = (srcPixel & 0xf0) >> 4;
            g = (g << (8-4)) | g;

            b = srcPixel & 0xf;
            b = (b << (8-4)) | b;
          }

          dest[w*(y + dy) + x + dx] = (a << 24) | (r << 16) | (g << 8) | b;
        }
}

void fixS3TC1(u8* dest, const u8* src, int w, int h)
{
  int s = 0;

  for(int y = 0; y < h/4; y += 2)
    for(int x = 0; x < w/4; x += 2)
      for(int dy = 0; dy < 2; ++dy)
        for(int dx = 0; dx < 2; ++dx, s += 8)
          memcpy(&dest[8*((y + dy)*w/4 + x + dx)], &src[s], 8);

  for(int k = 0; k < w*h/2; k += 8)
  {
    toWORD(*(u16*)&dest[k]);
    toWORD(*(u16*)&dest[k+2]);
    s3tc1ReverseByte(dest[k+4]);
    s3tc1ReverseByte(dest[k+5]);
    s3tc1ReverseByte(dest[k+6]);
    s3tc1ReverseByte(dest[k+7]);
  }
}

void writeData(u8 format, int w, int h, u8* src, int size, FILE* f)
{
  int destSize = size;
  if(format == 0)
    destSize *= 2; //we have to convert from i4 to i8...
  else if(format == 5)
    destSize *= 2; //we have to convert from r5g5b5a3 to rgba8

  u8* dest = new u8[destSize];

  //all these conversion functions assume w, h > 4 (or even 8),
  //they will crash otherwise. TODO: fix! (too lazy right now ;-) )
  switch(format)
  {
    case 0:
      fix8x8Expand(dest, src, w, h);
      break;

    case 1:
    case 2:
      fix8x4(dest, src, w, h);
      break;

    case 3:
    case 4:
      fix4x4((u16*)dest, (u16*)src, w, h);
      break;

    case 5:
      fixRgb5A3((u32*)dest, (u16*)src, w, h);
      break;

    case 0xe:
      fixS3TC1(dest, src, w, h);
      break;

    default:
      break;
  }

  fwrite(dest, destSize, 1, f);
  delete [] dest;
}

void readBmd(FILE* f)
{
  int i;

  //skip file header
  fseek(f, 0x20, SEEK_SET);

  u32 size = 0;
  char tag[4];
  int t;

  do
  {
    fseek(f, size, SEEK_CUR);
    t = ftell(f);

    fread(tag, 1, 4, f);
    fread(&size, 4, 1, f);
    toDWORD(size);
    fseek(f, t, SEEK_SET);

    cout << "Read " << string(tag, 4) << endl;

  } while(strncmp(tag, "TEX1", 4) != 0);
  fseek(f, t, SEEK_SET);

  //read textureblock header
  Tex1Header h;
  fread(&h, sizeof(h), 1, f);
  toDWORD(h.size);
  toWORD(h.numImages);
  toWORD(h.unknown);
  toDWORD(h.unknown2);
  toDWORD(h.stringTableOffset);

  //read texture headers
  vector<TextureHeader> texHeaders;
  for(i = 0; i < h.numImages; ++i)
  {
    TextureHeader texHead;
    fread(&texHead, sizeof(texHead), 1, f);
    toWORD(texHead.width);
    toWORD(texHead.height);
    toWORD(texHead.unknown2);
    toDWORD(texHead.unknown3);
    toDWORD(texHead.unknown4);
    toDWORD(texHead.unknown5);
    toWORD(texHead.unknown6);
    toWORD(texHead.unknown7);
    toWORD(texHead.unknown9);
    toDWORD(texHead.dataOffset);
    texHeaders.push_back(texHead);
  }

  //go to stringtable
  fseek(f, t, SEEK_SET);
  vector<string> strings = dumpStringtable(h, texHeaders, f);

  for(int k = 0; k < h.numImages; ++k)
  {
    TextureHeader& tx = texHeaders[k];
    DdsHeader ddsHead = createDdsHeader(tx.width, tx.height, tx.mipmapCount);
    int s = getBufferSize(tx.format, tx.width, tx.height, ddsHead.colorCaps);

    if(s == -1) //unsupported format
    {
      cout << endl << "UNSUPPORTED FORMAT " << (int)tx.format << "!!!" << endl << endl;

      //create dummy file to make sure everybody sees the failure:
      char filename[2000];
      //sprintf(filename, "%s %d FAILED: %s %d.dds", g_name, k, strings[k].c_str(), tx.format);
	  sprintf(filename, "%s%s.ERROR", g_folder.c_str(), strings[k].c_str());
      
      FILE* outF = fopen(filename, "wb");
      fclose(outF);

      continue;
    }

    fseek(f, t + 0x20, SEEK_SET);

    //"+ k*0x20" is required because the offset is relative to
    //the texture header, but we are at the beginning of all
    //texture headers. The k'th texture header is at +k*0x20
    fseek(f, tx.dataOffset + k*0x20, SEEK_CUR);

    char filename[2000];
    //sprintf(filename, "%s %d %s %d.dds", g_name, k, strings[k].c_str(), tx.format);
	sprintf(filename, "%s%s.dds", g_folder.c_str(), strings[k].c_str());

    FILE* outF = fopen(filename, "wb");
    fwrite(&ddsHead, sizeof(ddsHead), 1, outF);

    //image data
    u8* buff0 = new u8[s];

    int fac = 1;
    for(int j = 0; j < ddsHead.numMips; ++j)
    {
      fread(buff0, 1, s/(fac*fac), f);
      writeData(tx.format, ddsHead.width/fac, ddsHead.height/fac, buff0, s/(fac*fac), outF);
      fac *= 2;
    }

    delete [] buff0;
    fclose(outF);
  }
}

int main(int argc, char* argv[])
{
  FILE* f;
  if(argc < 3)// || (f = fopen(argv[1], "rb")) == NULL)
    return EXIT_FAILURE;

  g_name = argv[1]; //"C:\\ZeldaModels\\appTest\\henna.bmd"; // argv[1];
  if ((f = fopen(g_name, "rb")) == NULL)
    return EXIT_FAILURE;

  g_folder = argv[2];

  readBmd(f);

  fclose(f);

  //system("pause");

  return EXIT_SUCCESS;
}
