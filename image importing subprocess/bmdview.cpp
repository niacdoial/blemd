// some classic VS BS here. do not use it if you can.
// (it doesn't do much)
//#include "stdafx.h"

//by thakis
//updated (by niacdoial) with code from BMDView2 (also by Thakis?)
#include <string.h>

#include <locale>  // needed for string conversion
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <cassert>
#include <map>
#include <set>
#include <iosfwd>
using namespace std;

typedef unsigned char u8;
typedef unsigned short u16;
typedef short s16;
typedef unsigned int u32;
typedef int s32;

using std::endl;

/*
* On my Intel OS X, BIG_ENDIAN is defined for some reason when <sys/types.h>
* is included (which it is by <vector> for example), so don't check for it.
*/

#if defined __BIG_ENDIAN__ || (defined __APPLE__ && defined __POWERPC__)
#define GC_BIG_ENDIAN
#endif

//sanity check
#if (defined __LITTLE_ENDIAN__ || defined LITTLE_ENDIAN) && defined GC_BIG_ENDIAN
#error Unable to determine endianness
#endif


//linux port stuff (apparently some functions have to get redefined)
void* memcpy(void *s1, const void *s2, size_t n);


#ifdef WIN32
#define memcpy_s2(dest, maxsz, src, sz) \
	(memcpy_s(dest, maxsz, src, sz))
#define FILEPATH(str) (to_wstr(str))
#define pathstr_t std::wstring
#define Xcout wcout
#define SEP '\\'
#define SEP_STR "\\"
#else
#define memcpy_s2(dest, maxsz, src, sz) \
	(memcpy(dest, src, sz))
#define FILEPATH(str) str
#define pathstr_t std::string
#define Xcout cout
#define SEP '/'
#define SEP_STR "/"
#endif


enum IMAGETYPE
{
	DDS,
	TGA
};

inline void toWORD(u16& w)
{
#ifndef GC_BIG_ENDIAN
	u8 w1 = w & 0xFF;
	u8 w2 = w >> 8;
	w = (w1 << 8) | w2;
#endif
}

inline void toDWORD(u32& d)
{
#ifndef GC_BIG_ENDIAN
	u8 w1 = d & 0xFF;
	u8 w2 = (d >> 8) & 0xFF;
	u8 w3 = (d >> 16) & 0xFF;
	u8 w4 = d >> 24;
	d = (w1 << 24) | (w2 << 16) | (w3 << 8) | w4;
#endif
}

inline void readWORD(istream& f, u16& dest)
{
	f.read((char*)&dest, 2);
	toWORD(dest);
}

inline void readDWORD(istream& f, u32& dest)
{
	f.read((char*)&dest, 4);
	toDWORD(dest);
}

inline u16 memWORD(const u8* where)
{
	return (where[0] << 8) | where[1];
}

inline u32 memDWORD(const u8* where)
{
	return (where[0] << 24) | (where[1] << 16) | (where[2] << 8) | where[3];
}

inline u16 memWORD_le(const u8* where)
{
	return where[0] | (where[1] << 8);
}

inline u32 memDWORD_le(const u8* where)
{
	return (where[0] | (where[1] << 8) | (where[2] << 16) | (where[3] << 24));
}

inline void toWORD_le(u16& w)
{
#ifdef GC_BIG_ENDIAN
	u8 w1 = w & 0xFF;
	u8 w2 = w >> 8;
	w = (w1 << 8) | w2;
#endif
}

inline void toSHORT_le(s16& w)
{
	toWORD_le(*(u16*)&w);
}

inline void toDWORD_le(u32& d)
{
#ifdef GC_BIG_ENDIAN
	u8 w1 = d & 0xFF;
	u8 w2 = (d >> 8) & 0xFF;
	u8 w3 = (d >> 16) & 0xFF;
	u8 w4 = d >> 24;
	d = (w1 << 24) | (w2 << 16) | (w3 << 8) | w4;
#endif
}

inline void writeWORD_le(FILE* f, u16 v)
{
	toWORD_le(v);
	fwrite(&v, 2, 1, f);
}

inline void writeSHORT_le(ostream& f, s16 v)
{
	toSHORT_le(v);
	f.write((char*)&v, 2);
}

inline void writeDWORD_le(ostream& f, u32 v)
{
	toDWORD_le(v);
	f.write((char*)&v, 4);
}

inline std::wstring to_wstr(const std::string str)
{
	std::wstringstream sstr;
	const char *temp = str.c_str();
	sstr << temp;
	//delete[] temp;
	return sstr.str();
}

inline std::string to_unwstr(const std::wstring& str, char dfault = '?',
                      const std::locale& loc = std::locale::classic() )
{
	const wchar_t *s = str.c_str();
	std::ostringstream stm;

	while( *s != L'\0' ) {
		stm << std::use_facet< std::ctype<wchar_t> >( loc ).narrow( *s++, dfault );
	}
	return stm.str();
}

struct Tex1Header
{
	char tag[4]; //'TEX1'
	u32 sizeOfSection;
	u16 numImages;
	u16 unknown; //padding, usually 0xffff
	u32 textureHeaderOffset; //numImages bti image headers are stored here (see bti spec)
	//note: several image headers may point to same image data
	//offset relative to Tex1Header start

	u32 stringTableOffset;   //stores one filename for each image (TODO: details on stringtables)
	//offset relative to Tex1Header start  
	u8 padding[12];
};


const int I4 = 0;
const int I8 = 1;
const int A4_I4 = 2;
const int A8_I8 = 3;
const int R5_G6_B5 = 4;
const int A3_RGB5 = 5;
const int ARGB8 = 6;
const int INDEX4 = 8;
const int INDEX8 = 9;
const int INDEX14_X2 = 10;
const int S3TC1 = 14;

const int PAL_A8_I8 = 0;
const int PAL_R5_G6_B5 = 1;
const int PAL_A3_RGB5 = 2;

struct TextureHeader
{
	//0 - i4
	//1 - i8
	//2 - a4i4
	//3 - a8i8
	//4 - r5g6b5
	//5 - rgb5a3
	//6 - argb8
	//
	//8 - index4
	//9 - index8
	//10 -index14x2
	//
	//14 - dxt1 compressed
	//(see tpl's format in yagcd for more details)
	u8 format;
	u8 unknown; //0 or cc, 1, 2 (geostar (texmatrix).bmd)
	u16 width;
	u16 height;

	/*
	from gx.h:
	0: clamp to edge
	1: repeat
	2: mirror
	*/
	u8 wrapS;
	u8 wrapT;

	u8 unknown3; // 0, 1 (gnd)


	//0 - a8i8
	//1 - r5g6b5
	//2 - rgb5a3
	//(see tpl's palette format in yagcd for more details)
	u8 paletteFormat;
	u16 paletteNumEntries;
	u32 paletteOffset; //palette data


	u32 unknown5; //sometimes 0x1_00_0000 when mipmapCount > 1

	//0 - nearest
	//1 - linear
	//2 - near_mip_near
	//3 - lin_mip_near
	//4 - near_mip_lin
	//5 - lin_mip_lin
	u8 minFilter;
	u8 magFilter; //??

	u16 unknown7; //0 most of the time,
	//sometimes 0x10, 0x18 (mariocap), 0x20, 0x28
	u8 mipmapCount;
	u8 unknown8; //0 (nomips), 1 (nomips), d, 48, 4d, 56 (nomips),
	//58, 61, 8f, da or ff (hmm...0-ff ;-) )
	u16 unknown9; //0 (nomips), 7, 20, 74 (in airport.bmd), ffee, ffe3 (sea.bmd)

	u32 dataOffset; //image data

	//some of the unknown data could be render state?
	//(lod bias, transparent color (? could be in shader as well...), ...)
	/*
	void GX_InitTexObj(GXTexObj *obj,void *img_ptr,u16 wd,u16 ht,u8 fmt,u8 wrap_s,u8 wrap_t,u8 mipmap);
	void GX_InitTexObjCI(GXTexObj *obj,void *img_ptr,u16 wd,u16 ht,u8 fmt,u8 wrap_s,u8 wrap_t,u8 mipmap,u32 tlut_name);
	void GX_InitTexObjLOD(GXTexObj *obj,u8 minfilt,u8 magfilt,f32 minlod,f32 maxlod,f32 lodbias,u8 biasclamp,u8 edgelod,u8 maxaniso);
	void GX_SetTexCoorScaleManually(u8 texcoord,u8 enable,u16 ss,u16 ts);
	void GX_SetTexCoordBias(u8 texcoord,u8 s_enable,u8 t_enable);
	*/
};

struct Image
{
	int format;
	int width, height;

	std::vector<u8*> mipmaps; //points into imageData
	std::vector<int> sizes; //image data size for each mipmap
	std::vector<u8> imageData;

	//NOTE: palettized images are converted
	//to non-palettized images during load time,
	//i4 is converted to i8, a4i4 and a8i8 is converted to i8a8.
	//r5g5b5a3 and r5g6b5 are converted to rgba8.
	//(that is, only formats 1 (i8), 3* (i8a8), 6 (rgba8)
	//and 14 (dxt1) are used after conversion)

	//TODO: gl image conversions (rgba -> abgr, ai -> ia
	//somewhere else?)

	//TODO: this is temporary and belongs somewhere else:
	unsigned int texId;

	int originalFormat, paletteFormat;
};

void readdumbarray(std::vector<u8>& vect, int size, std::istream& is)
{
	u16 temp;
	//vect.resize(2 * size);
	for (int i = 0; i < size; i++)
	{
		is.read((char*)&temp, sizeof(u16));
		vect[2 * i] = temp & 0xff;
		vect[2 * i + 1] = temp >> 8;
	}
}

std::string getString(int pos, istream& f)
{
	std::streamoff t = f.tellg();
	f.seekg(pos);

	std::string ret;
	char c;
	while ((c = f.get()) != '\0')
		ret.append(1, c);

	f.seekg(t);

	return ret;
}

std::vector<std::string> dumpStringtable(const Tex1Header& h, const std::vector<TextureHeader>& texHeaders, istream& f)
{
	vector<string> ret;

	f.seekg(h.stringTableOffset + f.tellg());
	std::streamoff fp = f.tellg();

	u16 numNames, unknown;
	f.read((char*)&numNames, sizeof(u16));
	f.read((char*)&unknown, sizeof(u16));
	toWORD(numNames);
	toWORD(unknown);

	assert(numNames == texHeaders.size());

	cout << endl << "Image names:" << endl;
	for (int i = 0; i < numNames; ++i)
	{
		u16 unknown2, nameOffset;
		readWORD(f, unknown2);
		readWORD(f, nameOffset);

		string s = getString(fp + nameOffset, f);
		const TextureHeader& th = texHeaders[i];
		//cout << hex << unknown2 << " " << s << endl;
		//cout << dec << "  Width: " << th.width << ", Height: " << th.height << ", format " << (int)th.format << ", "
		//	<< (int)th.mipmapCount << " mipmaps, offset: " << th.dataOffset << " = 0x" << hex << th.dataOffset << endl;
		//cout << hex << "  " << (int)th.unknown << " " << th.wrapS << " " << th.wrapT << " " << th.unknown3 << " "
		//	<< th.paletteFormat << " " << th.paletteNumEntries << " " << th.paletteOffset << " " << th.unknown5 << " "
		//	<< th.minFilter << " " << th.magFilter << " " << th.unknown7 << " " << (int)th.unknown8 << " " << th.unknown9 << endl;
		ret.push_back(s);
	}
	return ret;
}

void r5g6b5ToRgba8(u16 srcPixel, u8* dest);

void decompressDxt1(u8* dest, const u8* src, int w, int h)
{
	const u8* runner = src;
	for (int y = 0; y < h; y += 4)
	{
		for (int x = 0; x < w; x += 4)
		{
			u16 color1 = memWORD_le(runner);
			u16 color2 = memWORD_le(runner + 2);
			u32 bits = memDWORD_le(runner + 4);
			runner += 8;

			//prepare color table
			u8 colorTable[4][4];
			r5g6b5ToRgba8(color1, colorTable[0]);
			r5g6b5ToRgba8(color2, colorTable[1]);
			if (color1 > color2)
			{
				colorTable[2][0] = (2 * colorTable[0][0] + colorTable[1][0] + 1) / 3;
				colorTable[2][1] = (2 * colorTable[0][1] + colorTable[1][1] + 1) / 3;
				colorTable[2][2] = (2 * colorTable[0][2] + colorTable[1][2] + 1) / 3;
				colorTable[2][3] = 0xff;

				colorTable[3][0] = (colorTable[0][0] + 2 * colorTable[1][0] + 1) / 3;
				colorTable[3][1] = (colorTable[0][1] + 2 * colorTable[1][1] + 1) / 3;
				colorTable[3][2] = (colorTable[0][2] + 2 * colorTable[1][2] + 1) / 3;
				colorTable[3][3] = 0xff;
			}
			else
			{
				colorTable[2][0] = (colorTable[0][0] + colorTable[1][0] + 1) / 2;
				colorTable[2][1] = (colorTable[0][1] + colorTable[1][1] + 1) / 2;
				colorTable[2][2] = (colorTable[0][2] + colorTable[1][2] + 1) / 2;
				colorTable[2][3] = 0xff;

				//only the alpha value of this color is important...
				colorTable[3][0] = (colorTable[0][0] + 2 * colorTable[1][0] + 1) / 3;
				colorTable[3][1] = (colorTable[0][1] + 2 * colorTable[1][1] + 1) / 3;
				colorTable[3][2] = (colorTable[0][2] + 2 * colorTable[1][2] + 1) / 3;
				colorTable[3][3] = 0x00;
			}

			//decode image
			for (int iy = 0; iy < 4; ++iy)
				for (int ix = 0; ix < 4; ++ix)
				{
					if (x + ix < w && y + iy < h)
					{
						u32 di = 4 * ((y + iy)*w + x + ix);
						u32 si = bits & 0x3;
						dest[di + 0] = colorTable[si][0];
						dest[di + 1] = colorTable[si][1];
						dest[di + 2] = colorTable[si][2];
						dest[di + 3] = colorTable[si][3];
					}
					bits >>= 2;
				}
		}
	}
}

void readTex1Header(istream& f, Tex1Header& h)
{
	f.read((char*)&h, sizeof(h));
	//f.read(h.tag, 4);
	toDWORD(h.sizeOfSection);
	toWORD(h.numImages);
	toWORD(h.unknown);
	toDWORD(h.textureHeaderOffset);
	toDWORD(h.stringTableOffset);
}

void readTextureHeader(istream& f, TextureHeader& texHeader)
{
	f.read((char*)&texHeader, sizeof(TextureHeader));
	//f.read((char*)&texHeader.format, 1);
	//f.read((char*)&texHeader.unknown, 1);
	toWORD(texHeader.width);
	toWORD(texHeader.height);
	//f.read((char*)&texHeader.wrapS, 1);
	//f.read((char*)&texHeader.wrapT, 1);
	//f.read((char*)&texHeader.unknown3, 1);
	//f.read((char*)&texHeader.paletteFormat, 1);
	toWORD(texHeader.paletteNumEntries);
	toDWORD(texHeader.paletteOffset);
	toDWORD(texHeader.unknown5);
	//f.read((char*)&texHeader.minFilter, 1);
	//f.read((char*)&texHeader.magFilter, 1);
	toWORD(texHeader.unknown7);
	//f.read((char*)&texHeader.mipmapCount, 1);
	//f.read((char*)&texHeader.unknown8, 1);
	toWORD(texHeader.unknown9);
	toDWORD(texHeader.dataOffset);
}

//returns how many bytes an image of given format
//and dimensions needs in the file (NOT counting mipmaps)
int getCompressedBufferSize(u8 format, int w, int h)
{
	int w8 = w + (8 - w % 8) % 8;
	int w4 = w + (4 - w % 4) % 4;
	int h8 = h + (8 - h % 8) % 8;
	int h4 = h + (4 - h % 4) % 4;

	switch (format)
	{
	case I4:
		return w8*h8 / 2;
	case I8:
		return w8*h4;
	case A4_I4:
		return w8*h4;
	case A8_I8:
		return w4*h4 * 2;
	case R5_G6_B5:
		return w4*h4 * 2;
	case A3_RGB5:
		return w4*h4 * 2;
	case ARGB8:
		return w4*h4 * 4;
	case INDEX4:
		return w8*h8 / 2;
	case INDEX8:
		return w8*h4;
	case INDEX14_X2:
		return w4*h4 * 2;
	case S3TC1:
		return w4*h4 / 2;
	default:
		return -1;
	}
}

u8 getUncompressedBufferFormat(u8 format, u8 paletteFormat)
{
	switch (format)
	{
	case I4:
	case I8:
		return I8;
	case A4_I4: //a4i4 -> i8a8
	case A8_I8: //a8i8 -> i8a8
		return A8_I8;  // actually I8A8
	case R5_G6_B5:
	case A3_RGB5:
	case ARGB8:
		return ARGB8;  // actually RGBA8

	case INDEX4:
	case INDEX8:
	case INDEX14_X2:
		switch (paletteFormat)
		{
		case PAL_A8_I8: //a8i8 -> i8a8
			return A8_I8;  // actually I8A8
		case PAL_R5_G6_B5: //r5g6b5 -> rgba8
		case PAL_A3_RGB5: //rgb5a3 -> rgba8
			return ARGB8;  // actually RGBA8
		default:
			return -1;
		}

	case S3TC1:
		return S3TC1;  // DTX1
	default:
		return -1;
	}
}

//returns how many bytes an image of given format
//and dimensions needs in memory after uncompression etc
int getUncompressedBufferSize(u8 format, int w, int h, u8 paletteFormat)
{
	int w4 = w + (4 - w % 4) % 4;
	int h4 = h + (4 - h % 4) % 4;

	switch (getUncompressedBufferFormat(format, paletteFormat))
	{
	case I8:
		return w*h;
	case A8_I8:  //I8A8
		return w*h * 2;
	case ARGB8:  // RGBA8
		return w*h * 4;
	case S3TC1:  // DTX1
		return w4*h4 / 2;
	default:
		return -1;
	}
}

//new, fixed version
void fix8x8Expand(u8* dest, const u8* src, int w, int h)
{
	//convert to i8 during block swapping
	int si = 0;
	for (int y = 0; y < h; y += 8)
		for (int x = 0; x < w; x += 8)
			for (int dy = 0; dy < 8; ++dy)
				for (int dx = 0; dx < 8; dx += 2, ++si)
					if (x + dx < w && y + dy < h)
					{
						//http://www.mindcontrol.org/~hplus/graphics/expand-bits.html
						u8 t = src[si] & 0xf0;
						dest[w*(y + dy) + x + dx] = t | (t >> 4);
						t = (src[si] & 0xf);
						dest[w*(y + dy) + x + dx + 1] = (t << 4) | t;
					}
}


void fix8x8NoExpand(u8* dest, const u8* src, int w, int h)
{
	//convert to i8 during block swapping
	int si = 0;
	for (int y = 0; y < h; y += 8)
		for (int x = 0; x < w; x += 8)
			for (int dy = 0; dy < 8; ++dy)
				for (int dx = 0; dx < 8; dx += 2, ++si)
					if (x + dx < w && y + dy < h)
					{
						//http://www.mindcontrol.org/~hplus/graphics/expand-bits.html
						u8 t = src[si] & 0xf0;
						dest[w*(y + dy) + x + dx] = (t >> 4);
						t = (src[si] & 0xf);
						dest[w*(y + dy) + x + dx + 1] = t;
					}
}


void fix8x4(u8* dest, const u8* src, int w, int h)
{
	int si = 0;
	for (int y = 0; y < h; y += 4)
		for (int x = 0; x < w; x += 8)
			for (int dy = 0; dy < 4; ++dy)
				for (int dx = 0; dx < 8; ++dx, ++si)
					if (x + dx < w && y + dy < h)
						dest[w*(y + dy) + x + dx] = src[si];
}

void fix8x4Expand(u8* dest, const u8* src, int w, int h)
{
	int si = 0;
	for (int y = 0; y < h; y += 4)
		for (int x = 0; x < w; x += 8)
			for (int dy = 0; dy < 4; ++dy)
				for (int dx = 0; dx < 8; ++dx, ++si)
					if (x + dx < w && y + dy < h)
					{
						u8 lum = src[si] & 0xf;
						lum |= lum << 4;
						u8 alpha = src[si] & 0xf0;
						alpha |= (alpha >> 4);
						dest[2 * (w*(y + dy) + x + dx)] = lum;
						dest[2 * (w*(y + dy) + x + dx) + 1] = alpha;
					}
}

void fix4x4(u8* dest, const u8* src, int w, int h)
{
	int si = 0;
	for (int y = 0; y < h; y += 4)
		for (int x = 0; x < w; x += 4)
			for (int dy = 0; dy < 4; ++dy)
				for (int dx = 0; dx < 4; ++dx, si += 2)
					if (x + dx < w && y + dy < h)
					{
						//without byte swapping the result looks wrong. do tex1 blocks
						//store ai8 instead of ia8?
						int di = 2 * (w*(y + dy) + x + dx);
						dest[di + 0] = src[si + 1];
						dest[di + 1] = src[si + 0];
					}
}

void r5g6b5ToRgba8(u16 srcPixel, u8* dest)
{
	u8 r, g, b;
	r = (srcPixel & 0xf100) >> 11;
	g = (srcPixel & 0x7e0) >> 5;
	b = (srcPixel & 0x1f);

	//http://www.mindcontrol.org/~hplus/graphics/expand-bits.html
	r = (r << (8 - 5)) | (r >> (10 - 8));
	g = (g << (8 - 6)) | (g >> (12 - 8));
	b = (b << (8 - 5)) | (b >> (10 - 8));

	dest[0] = r;
	dest[1] = g;
	dest[2] = b;
	dest[3] = 0xff;
}

void fixR5G6B5(u8* dest, const u8* src, int w, int h)
{
	//convert to rgba8 during block swapping
	//4x4 tiles
	int si = 0;
	for (int y = 0; y < h; y += 4)
		for (int x = 0; x < w; x += 4)
			for (int dy = 0; dy < 4; ++dy)
				for (int dx = 0; dx < 4; ++dx, si += 2)
					if (x + dx < w && y + dy < h)
					{
						u16 srcPixel = memWORD(src + si);
						r5g6b5ToRgba8(srcPixel, &dest[4 * (w*(y + dy) + x + dx)]);
					}
}

void fixRGBA8(u8* dest, const u8* src, int w, int h)
{
	//2 4x4 input tiles per 4x4 output tile, first stores AR, second GB
	int si = 0;
	for (int y = 0; y < h; y += 4)
		for (int x = 0; x < w; x += 4)
		{
			int dy;

			//to have the texture in the format wanted by opengl,
			//we have to convert from argb to rgba

			//this is AR
			for (dy = 0; dy < 4; ++dy)
				for (int dx = 0; dx < 4; ++dx, si += 2)
					if (x + dx < w && y + dy < h)
					{
						//convert ar to rXXa
						u32 di = 4 * (w*(y + dy) + x + dx);
						dest[di + 0] = src[si + 1];
						dest[di + 3] = src[si + 0];
					}

			//this is GB
			for (dy = 0; dy < 4; ++dy)
				for (int dx = 0; dx < 4; ++dx, si += 2)
					if (x + dx < w && y + dy < h)
					{
						//convert gb to XgbX and or with previous value
						u32 di = 4 * (w*(y + dy) + x + dx);
						dest[di + 1] = src[si + 0];
						dest[di + 2] = src[si + 1];
					}
		}
}

void rgb5a3ToRgba8(u16 srcPixel, u8* dest)
{
	u8 r, g, b, a;

	//http://www.mindcontrol.org/~hplus/graphics/expand-bits.html
	if ((srcPixel & 0x8000) == 0x8000) //rgb5
	{
		a = 0xff;

		r = (srcPixel & 0x7c00) >> 10;
		r = (r << (8 - 5)) | (r >> (10 - 8));

		g = (srcPixel & 0x3e0) >> 5;
		g = (g << (8 - 5)) | (g >> (10 - 8));

		b = srcPixel & 0x1f;
		b = (b << (8 - 5)) | (b >> (10 - 8));
	}
	else //a3rgb4
	{
		a = (srcPixel & 0x7000) >> 12;
		a = (a << (8 - 3)) | (a << (8 - 6)) | (a >> (9 - 8));

		r = (srcPixel & 0xf00) >> 8;
		r = (r << (8 - 4)) | r;

		g = (srcPixel & 0xf0) >> 4;
		g = (g << (8 - 4)) | g;

		b = srcPixel & 0xf;
		b = (b << (8 - 4)) | b;
	}

	dest[0] = r;
	dest[1] = g;
	dest[2] = b;
	dest[3] = a;
}

void fixRgb5A3(u8* dest, const u8* src, int w, int h)
{
	//convert to rgba8 during block swapping
	//4x4 tiles
	int si = 0;
	for (int y = 0; y < h; y += 4)
		for (int x = 0; x < w; x += 4)
			for (int dy = 0; dy < 4; ++dy)
				for (int dx = 0; dx < 4; ++dx, si += 2)
					if (x + dx < w && y + dy < h)
					{
						u16 srcPixel = memWORD(src + si);
						rgb5a3ToRgba8(srcPixel, &dest[4 * (w*(y + dy) + x + dx)]);
					}
}

void s3tc1ReverseByte(u8& b)
{
	u8 b1 = b & 0x3;
	u8 b2 = b & 0xc;
	u8 b3 = b & 0x30;
	u8 b4 = b & 0xc0;
	b = (b1 << 6) | (b2 << 2) | (b3 >> 2) | (b4 >> 6);
}

void fixS3TC1(u8* dest, const u8* src, int w, int h)
{
	int s = 0;

	for (int y = 0; y < h / 4; y += 2)
		for (int x = 0; x < w / 4; x += 2)
			for (int dy = 0; dy < 2; ++dy)
				for (int dx = 0; dx < 2; ++dx, s += 8)
					if (4 * (x + dx) < w && 4 * (y + dy) < h)
						memcpy(&dest[8 * ((y + dy)*w / 4 + x + dx)], &src[s], 8);

	//s3tc1 on the cube is a bit different from s3tc1 on pc graphic cards:
	for (int k = 0; k < w*h / 2; k += 8)
	{
		swap(dest[k], dest[k + 1]);
		swap(dest[k + 2], dest[k + 3]);

		s3tc1ReverseByte(dest[k + 4]);
		s3tc1ReverseByte(dest[k + 5]);
		s3tc1ReverseByte(dest[k + 6]);
		s3tc1ReverseByte(dest[k + 7]);
	}
}

int getUnpackedPixSize(u8 paletteFormat)
{
	if (paletteFormat == PAL_A8_I8)
		return 2;
	return 4;
}

void unpackPixel(int index, u8* dest, const u8* palette, u8 paletteFormat)
{
	switch (paletteFormat)
	{
	case PAL_A8_I8: //a8i8 -> i8a8
		dest[0] = palette[2 * index + 1];
		dest[1] = palette[2 * index + 0];
		break;

	case PAL_R5_G6_B5: //r5g6b5 -> rgba8
		r5g6b5ToRgba8(memWORD(palette + 2 * index), dest);
		break;

	case PAL_A3_RGB5: //rgb5a3 -> rgba8
		rgb5a3ToRgba8(memWORD(palette + 2 * index), dest);
		break;
	}
}

void unpack8(u8* dst, const u8* src, int w, int h,
	const u8* palette, u8 paletteFormat)
{
	int pixSize = getUnpackedPixSize(paletteFormat);
	u8* runner = dst;

	for (int y = 0; y < h; ++y)
		for (int x = 0; x < w; ++x, runner += pixSize)
			unpackPixel(src[y*w + x], runner, palette, paletteFormat);
}

void unpack16(u8* dst, const u8* src, int w, int h,
	const u8* palette, u8 paletteFormat)
{
	int pixSize = getUnpackedPixSize(paletteFormat);
	u8* runner = dst;

	for (int y = 0; y < h; ++y)
		for (int x = 0; x < w; ++x, runner += pixSize)
		{
			//fix4x4() swaps words to little endian...
			u16 index = memWORD_le(src + 2 * (y*w + x));
			unpackPixel(index & 0x3fff, runner, palette, paletteFormat);
		}
}

//returns new format
u8 readImage(istream& f, int w, int h, u8 format, u8* palette, u8 paletteFormat, u8* dest)
{
	int srcBufferSize = getCompressedBufferSize(format, w, h);
	vector<u8> srcVec(srcBufferSize);
	u8* src = &srcVec[0];
	f.read((char*)src, srcBufferSize);

	//do format conversions, unpack blocks
	switch (format)
	{
	case I4: //i4 -> i8
		fix8x8Expand(dest, src, w, h);
		return I8;

	case I8: //i8
		fix8x4(dest, src, w, h);
		return I8;

	case A4_I4: //i4a4 -> i8a8
		fix8x4Expand(dest, src, w, h);
		return A8_I8;  // actually I8A8

	case A8_I8: //i8a8
		fix4x4(dest, src, w, h);
		return A8_I8;  // actually I8A8

	case R5_G6_B5: //r5g6b5 -> rgba8
		fixR5G6B5(dest, src, w, h);
		return ARGB8;  // actually RGBA8

	case A3_RGB5: //rgb5a3 -> rgba8
		fixRgb5A3(dest, src, w, h);
		return ARGB8;  // actually RGBA8

	case ARGB8: //argb8 -> rgba8
		fixRGBA8(dest, src, w, h);
		return ARGB8;  // actually RGBA8


	case INDEX4:
	case INDEX8:
	case INDEX14_X2:
	{
		//needed for palette conversions
		//(*2 for expaned i4->i8 case)
		vector<u8> tmpVec(2 * srcBufferSize);
		u8* tmp = &tmpVec[0];

		switch (format)
		{
		case INDEX4:
			fix8x8NoExpand(tmp, src, w, h);
			unpack8(dest, tmp, w, h, palette, paletteFormat);
			break;

		case INDEX8:
			fix8x4(tmp, src, w, h);
			unpack8(dest, tmp, w, h, palette, paletteFormat);
			break;

		case INDEX14_X2:
			fix4x4(tmp, src, w, h);
			unpack16(dest, tmp, w, h, palette, paletteFormat);
			break;
		}

		switch (paletteFormat)
		{
		case PAL_A8_I8:
			return A8_I8;  // actually I8A8
		case PAL_R5_G6_B5:
		case PAL_A3_RGB5:
			return ARGB8;  // actually RGBA8
		default:
			//warn("tex1: unsupported palette format %d", paletteFormat);
			return 0xff; //TODO: ?
		}
	}


	case S3TC1:
		fixS3TC1(dest, src, w, h);
		return S3TC1; // actually DXT1

	default:
		//warn("unsupported image format %d", format);
		return 0xff; //TODO: ?
	}
}

void loadAndConvertImage(istream& f, const TextureHeader& h, long baseOffset,
	Image& curr)
{
	int i;

	curr.width = h.width;
	curr.height = h.height;
	curr.format = h.format;

	//if ((h.format == 8 || h.format == 9 || h.format == 10)
	//	&& (h.paletteFormat != 1 && h.paletteFormat != 2)) //never tested such an image,
		//but yagcd says theres also a palette format 0
	//	warn("found format %d, palette format %d", h.format, h.paletteFormat);


	vector<u8> palette;
	if (h.paletteNumEntries != 0)
	{
		//read palette
		palette.resize(h.paletteNumEntries * 2);
		f.seekg(baseOffset + h.paletteOffset);
		readdumbarray(palette, h.paletteNumEntries, f);
		//fread(&palette[0], 2, h.paletteNumEntries, f);
	}

	//calculate required image size
	int totalRequiredSize = 0;
	int wid = h.width, hyt = h.height;
	for (i = 0; i < h.mipmapCount; ++i)
	{
		totalRequiredSize += getUncompressedBufferSize(h.format, wid, hyt, h.paletteFormat);
		wid /= 2; hyt /= 2;
	}

	//get memory for image, set mipmap pointers and load image

	//if (h.dataOffset == 0) //TODO: twilight princess does that
	//	warn("What to do, what to do? (data offset in image is 0)\n");

	f.seekg(baseOffset + 0x20 + h.dataOffset);
	curr.imageData.resize(totalRequiredSize);
	totalRequiredSize = 0;
	wid = h.width; hyt = h.height;
	curr.mipmaps.resize(h.mipmapCount);
	curr.sizes.resize(h.mipmapCount);
	for (i = 0; i < h.mipmapCount; ++i)
	{
		curr.mipmaps[i] = &curr.imageData[totalRequiredSize];

		curr.sizes[i] =
			getUncompressedBufferSize(h.format, wid, hyt, h.paletteFormat);

		//read image
		if (h.dataOffset != 0)
		{
			if (palette.size() == 0)
				palette.push_back('\x0');
			curr.format = readImage(f, wid, hyt, h.format,
				&palette[0], h.paletteFormat, curr.mipmaps[i]);
		}
		else
		{
			//this texture is probably rendered at runtime. for now, fill it with
			//white
			curr.format = getUncompressedBufferFormat(h.format, h.paletteFormat);
			if (curr.format != S3TC1)  // actually DTX1
				memset(curr.mipmaps[i], 0xff, curr.sizes[i]);
			else
			{
				const u8 whiteBlock[] = { 0xff, 0xff, 0x00, 0x00,
					0x00, 0x00, 0x00, 0x00 };
				for (int c = 0; c < curr.sizes[i] / 8; ++c)
					memcpy(curr.mipmaps[i] + 8 * c, whiteBlock, 8);
			}
		}

		totalRequiredSize += getUncompressedBufferSize(h.format, wid, hyt, h.paletteFormat);
		wid /= 2; hyt /= 2;
	}

	curr.originalFormat = h.format;
	curr.paletteFormat = h.paletteFormat;
}

///////////////////////////////////////////////////////////
// following structures and functions for exporting


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

struct TgaHeader
{
	u8  identsize;          // size of ID field that follows 18 uint8 header (0 usually)
	u8  colourmaptype;      // type of colour map 0=none, 1=has palette
	u8  imagetype;          // type of image 0=none,1=indexed,2=rgb,3=grey,+8=rle packed

	s16 colourmapstart;     // first colour map entry in palette
	s16 colourmaplength;    // number of colours in palette
	u8  colourmapbits;      // number of bits per palette entry 15,16,24,32

	s16 xstart;             // image x origin
	s16 ystart;             // image y origin
	s16 width;              // image width in pixels
	s16 height;             // image height in pixels
	u8  bits;               // image bits per pixel 8,16,24,32
	u8  descriptor;         // image descriptor bits (vh flip bits)
	TgaHeader(s16 w, s16 h) :
		identsize(0),
		colourmaptype(0),
		imagetype(2),
		colourmapstart(0),
		colourmaplength(0),
		colourmapbits(0),
		xstart(0),
		ystart(0),
		width(w),
		height(h),
		bits(32),
		descriptor(0){}
};

void writeColorCaps(ostream& f, const ColorCaps& cc)
{
	writeDWORD_le(f, cc.size);
	writeDWORD_le(f, cc.flags);
	f.write(cc.fourCC, 4);
	writeDWORD_le(f, cc.rgbBitCount);
	writeDWORD_le(f, cc.rBitMask);
	writeDWORD_le(f, cc.gBitMask);
	writeDWORD_le(f, cc.bBitMask);
	writeDWORD_le(f, cc.aBitMask);
}

void writeDdsHeader(ostream& f, const DdsHeader& h)
{
	f.write(h.type, 4);
	writeDWORD_le(f, h.size);
	writeDWORD_le(f, h.flags);
	writeDWORD_le(f, h.height);
	writeDWORD_le(f, h.width);
	writeDWORD_le(f, h.linearSize);
	writeDWORD_le(f, h.depth);
	writeDWORD_le(f, h.numMips);
	for (int i = 0; i < 11; ++i)
		writeDWORD_le(f, h.unused[i]);
	writeColorCaps(f, h.colorCaps);
	writeDWORD_le(f, h.caps);
	for (int j = 0; j < 4; ++j)
		writeDWORD_le(f, h.unused2[j]);
}

void writeTgaHeader(ostream& f, const TgaHeader& h)
{
	f.write((char*)&h.identsize, 1);
	f.write((char*)&h.colourmaptype, 1);
	f.write((char*)&h.imagetype, 1);

	writeSHORT_le(f, h.colourmapstart);
	writeSHORT_le(f, h.colourmaplength);
	f.write((char*)&h.colourmapbits, 1);

	writeSHORT_le(f, h.xstart);
	writeSHORT_le(f, h.ystart);
	writeSHORT_le(f, h.width);
	writeSHORT_le(f, h.height);
	f.write((char*)&h.bits, 1);
	f.write((char*)&h.descriptor, 1);
}

void i8a8ToRgba8(u8* dest, const u8* src, int w, int h)
{
	for (int y = 0; y < h; ++y)
	{
		for (int x = 0; x < w; ++x)
		{
			u8 i8 = src[2 * x + 0];
			u8 a8 = src[2 * x + 1];
			dest[4 * x + 0] = i8;
			dest[4 * x + 1] = i8;
			dest[4 * x + 2] = i8;
			dest[4 * x + 3] = a8;
		}

		src += 2 * w;
		dest += 4 * w;
	}
}

void flipVertical(std::vector<u8>& vec, int w, int h, int bpp)
{
	assert(w*h*bpp == (int)vec.size());
	std::vector<u8> tmpLine(w*bpp);
	u8* up = &vec[0], *down = &vec[w*(h - 1)*bpp];
	for (int y = 0; y < h / 2; ++y)
	{
		memcpy_s2(&tmpLine[0], tmpLine.size(), up, w*bpp);
		//std::copy(up, up + w*bpp, tmpLine.begin());
		memcpy_s2(up, w*bpp, down, w*bpp);
		//std::copy(down, down + w*bpp, up);
		memcpy_s2(down, w*bpp, &tmpLine[0], tmpLine.size());
		//std::copy(tmpLine.begin(), tmpLine.end(), down);

		up += w*bpp;
		down -= w*bpp;
	}
}

DdsHeader createDdsHeader(int w, int h, int numMips)
{
	DdsHeader ret;
	memset(&ret, 0, sizeof(ret));

	memcpy(ret.type, "DDS ", 4);  // memcpy, not strncpy because of the terminating \0
	ret.size = 124;
	ret.flags = 0x21007; //mipmapcount + pixelformat + width + height + caps
	ret.width = w;
	ret.height = h;
	ret.numMips = numMips;
	ret.colorCaps.size = 32;
	ret.caps = 0x401000; //mipmaps + texture
	return ret;
}

void saveTextureDds(const pathstr_t& filename, const Image& img)
{
	DdsHeader h = createDdsHeader(img.width, img.height, img.mipmaps.size());
	switch (img.format)
	{
	case I8:
		h.colorCaps.flags = 0x20000; //luminance
		h.colorCaps.rgbBitCount = 8;
		h.colorCaps.rBitMask = 0xff;
		break;
	case A8_I8:  // I8A8
		h.colorCaps.flags = 0x20001; //luminance + alpha
		h.colorCaps.rgbBitCount = 16;
		h.colorCaps.rBitMask = 0xff;
		h.colorCaps.aBitMask = 0xff00;
		break;
	case ARGB8:  // RGBA8
		h.colorCaps.flags = 0x41; //rgb + alpha
		h.colorCaps.rgbBitCount = 32;
		h.colorCaps.rBitMask = 0xff;
		h.colorCaps.gBitMask = 0xff00;
		h.colorCaps.bBitMask = 0xff0000;
		h.colorCaps.aBitMask = 0xff000000;
		break;
	case S3TC1:  // DTX1
		h.colorCaps.flags = 0x4; //fourcc
		memcpy(h.colorCaps.fourCC, "DXT1", 4);  // memcpy to not copy a \0
		break;
	}

	ofstream file(filename, ios::binary);
	if (!file.good())
	{
		return;
	}

	writeDdsHeader(file, h);
	file.write((char*)&img.imageData[0], img.imageData.size());
	file.close();
}

void saveTextureTga(const pathstr_t& filename, const Image& img)
{
	TgaHeader h(img.width, img.height);

	ofstream file(filename, ios::binary);
	if (!file.good())
	{
		return;
	}

	if (img.format == I8)
	{
		//greyscale
		h.imagetype = 3;
		h.bits = 8;
		writeTgaHeader(file, h);

		//flip vertical
		//std::vector<u8> data(h.width*h.height);
		std::vector<u8> data(img.imageData.begin(), img.imageData.begin() + h.width * h.height);
		//data = img.imageData;
		//std::copy(img.imageData.begin(), img.imageData.begin() + data.size(),
		//	data.begin());
		flipVertical(data, h.width, h.height, 1);
		file.write((char*)&data[0], data.size());
	}
	else
	{
		//convert to rgba8, save
		writeTgaHeader(file, h);

		std::vector<u8> data(h.width*h.height * 4);
		switch (img.format)
		{
		case A8_I8: //convert i8a8 to rgba8
			i8a8ToRgba8(&data[0], &img.imageData[0], h.width, h.height);
			break;
		case ARGB8: //rgba8 - write directly
			memcpy(&data[0], &img.imageData[0], data.size());
			break;
		case S3TC1: //convert dxt1 to rgba8
			decompressDxt1(&data[0], &img.imageData[0], h.width, h.height);
			break;
		}

		//data is rgba8, targa stores bgra8, convert:
		for (size_t i = 0; i < data.size(); i += 4)
			std::swap(data[i + 0], data[i + 2]);

		//data is top-down, targa stores bottom up
		flipVertical(data, h.width, h.height, 4);

		file.write((char*)&data[0], data.size());
	}

	file.close();
}

void saveTexture(IMAGETYPE imgType, const Image& img,
	const pathstr_t& filename, bool doMirrorX, bool doMirrorY)
{
	Image tmp, tmp2;
	const Image* imageToUse = &img;

	//if (doMirrorX)
	//	imageToUse = mirrorX(tmp, *imageToUse);
	//if (doMirrorY)
	//	imageToUse = mirrorY(tmp2, *imageToUse);

	switch (imgType)
	{
	case DDS:
		saveTextureDds(filename + ".dds", *imageToUse);
		break;
	case TGA:
		saveTextureTga(filename + ".tga", *imageToUse);
		break;
	}
}


pathstr_t g_name;
pathstr_t g_folder;
IMAGETYPE im_type;



void readBmd(std::istream& f)
{
	int i;

	//skip file header
	f.seekg(0x20);
	u32 size = 0;
	char tag[4];
	std::streamoff t;  // BaseOffset
	do
	{
		f.seekg(size + f.tellg());
		t = f.tellg();
		f.read(tag, 4);
		readDWORD(f, size);
		f.seekg(t);

		cout << "Read " << string(tag, 4) << endl;
		if (size == 0)
			throw runtime_error("corrupted .bmd file: sizeless sections don't exist");
		if (f.eof())
			// no tex section, no images to extract. peace out.
			exit(EXIT_SUCCESS);
	} while (strncmp(tag, "TEX1", 4) != 0);
	f.seekg(t);

	//read textureblock header
	Tex1Header h;
	readTex1Header(f, h);

	//read texture headers
	vector<TextureHeader> texHeaders;
	for (i = 0; i < h.numImages; ++i)
	{
		TextureHeader texHead;
		readTextureHeader(f, texHead);
		if (texHead.dataOffset != 0)  // null offset means it has to be rendered later
			texHead.dataOffset += 0x20 * i;
		texHeaders.push_back(texHead);
	}

	//go to stringtable
	f.seekg(t);
	vector<string> strings = dumpStringtable(h, texHeaders, f);

	for (int k = 0; k < h.numImages; ++k)
	{
		TextureHeader& tx = texHeaders[k];

		int s = getUncompressedBufferSize(tx.format, tx.width, tx.height, tx.paletteFormat);

		if (s == -1) //unsupported format
		{
			cout << endl << "UNSUPPORTED FORMAT " << (int)tx.format << "!!!" << endl << endl;

			//create dummy file to make sure everybody sees the failure:
			//sprintf_s<2048>(filename, "%s %d FAILED: %s %d.dds", g_name, k, strings[k].c_str(), tx.format);
			pathstr_t filename = g_folder + FILEPATH(strings[k]+ string(".ERROR"));

			ofstream outF;
			outF.open(filename, ios::binary);
			outF.close();

			continue;
		}

		//sprintf_s<2048>(filename, "%s %d %s %d.dds", g_name, k, strings[k].c_str(), tx.format);
		pathstr_t filename = g_folder + FILEPATH(strings[k]);

		Image tempImage;
		loadAndConvertImage(f, tx, t, tempImage);
		saveTexture(im_type, tempImage, filename, false, false);

	}
}

//it's supposed to be:
int main(int argc, char* argv[])
//int _tmain(int argc, wchar_t* argv[])
{
	for (int k = 0; k < argc; k++)
	{
		Xcout << argv[k];
		cout << "   " << /*ToStr(argv[k]) <<*/ endl;
	}
	if (argc < 3)// || (f = fopen(argv[1], "rb")) == NULL)
	{
		cout << "wrong arg count" << endl;
		cout << argc << endl;
		switch (argc)
		{
		case 2:
			Xcout << "1 : " << argv[1] << endl;
			// do not break here
		case 1:
			//cout << "0 : " << argv[0] << endl;
			//g_name = L"C:\\Users\\Liam\\Downloads\\kmdl\\archive\\bmwr\\al.bmd";
			//g_folder = L"C:\\Users\\Liam\\Downloads\\kmdl\\archive\\bmwr\\al\\Textures\\";
			//im_type = TGA;
			//break;
			return EXIT_FAILURE;
		}
	}
	else
	{
		g_name = argv[1]; //"C:\\ZeldaModels\\appTest\\henna.bmd"; // argv[1];
		g_folder = argv[2];
		im_type = DDS;
	}
	pathstr_t g_folder2 = g_folder;  // this is a "ghost" for debugging purposes

	if (argc >= 4)
	{
		pathstr_t temp(argv[3]);
		if (temp.size()>=3 &&
			temp[0] == 'T' &&
			temp[1] == 'G' &&
			temp[2] == 'A')   // THIS IS HIDEOUS!
			im_type = TGA;
	}
	if (g_folder[g_folder.size() - 1] == '\"')
	{
		//cout << "g_folder: " << g_folder2;
		g_folder.erase(g_folder.end() - 1);
		Xcout << "g_folder: " << g_folder;
	}
	if (g_folder[g_folder.size() - 1] != SEP)
	{
		g_folder += FILEPATH(string(SEP_STR));
	}
	Xcout << "textures: " << g_folder << endl;

	std::ifstream is(g_name, ios_base::binary);
	if (!(is.is_open() || is.good()))
	{
		Xcout << "cannot open file " << g_name << endl;
		return EXIT_FAILURE;
	}

	try
	{
		readBmd(is);
	}
	catch (exception& err)
	{
		cout << endl << err.what() << endl;
	}
	is.close();

	//system("pause");

	return EXIT_SUCCESS;
}
