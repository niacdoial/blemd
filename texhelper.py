import bpy
import bpy_extras
import mathutils
from .common import getFilenameFile, stdout_redirected
import logging
log = logging.getLogger('bpy.ops.import_mesh.bmd.texhelper')


imported_tslots = {}
imported_textures = {}  # 'Texture' objects or images. depents on the run. Probably fully migrating to second

DIFFUSE = 'DIFFUSE'
ALPHA = 'ALPHA'
SPECULAR = 'SPECULAR'

# used to set mode before calls
MODE = 'DO'


def textures_reset():
    global imported_textures  # avoid crashes when data deleted in blender, but still used here
    global imported_tslots
    imported_textures = {}
    imported_tslots = {}

def getTexImage(mat, fname):
    global imported_tslots
    try:
        return imported_tslots[mat][fname].image
    except Exception as err:
        log.warning('Could not find desired image (%s ; %s)  in database', mat, fname)
        return None


def getTexSlot(mat, fname):
    for com in mat.texture_slots:
        if com is not None:
            if com.texture == imported_tslots[mat][fname]:
                return com

def newtex_tex(fname):
    global imported_textures
    global MODE
    if fname in imported_textures.keys():
        return imported_textures[fname]

    tex = bpy.data.textures.new(getFilenameFile(fname) + '_texture', type='IMAGE')
    try:
        img = bpy.data.images.load(fname)
        if MODE == 'DO':
            img.pack()
        elif MODE == 'PNG':
            img.pack(as_png=True)
        #elif MODE == 'TARGA':
        #    tgaconvert(img)
        tex.image = img
    except Exception as err:
        log.warning('Problem with image %s (error is %s)', fname, err)

    tex.use_interpolation = True
    tex.filter_type = 'EWA'
    tex.filter_size = 1
    tex.use_alpha = True

    imported_textures[fname] = tex
    return tex

def newtex_image(fname):
    global imported_textures
    global MODE  # XXX this thing is old. migrate to new glocals philosiphy
    if fname in imported_textures.keys():
        return imported_textures[fname]
    try:
        img = bpy.data.images.load(fname)
        if MODE == 'DO':
            img.pack()
        elif MODE == 'PNG':
            img.pack(as_png=True)
    except Exception as err:
        log.warning('Problem with image %s (error is %s)', fname, err)
        raise

    imported_textures[fname] = img
    return img

MISSING_TEXTURE = None
def newtex_missing():
    global MISSING_TEXTURE
    if MISSING_TEXTURE is None:
        MISSING_TEXTURE = bpy.data.images.new("MISSING",1,1)
        MISSING_TEXTURE.pixels[0] = 1  # set the red channel of the image's only pixel
    return MISSING_TEXTURE

def newtex_tslot(fname, type, mat):
    global imported_tslots
    if mat in imported_tslots.keys() and fname in imported_tslots[mat].keys():
        tex = imported_tslots[mat][fname]
        matslot = getTexSlot(mat, fname)
    else:
        mat.name = getFilenameFile(fname)+'_material'
        tex = newtex_tex(fname)
        matslot = mat.texture_slots.add()
        matslot.texture = tex
        matslot.texture_coords = 'UV'
        imported_tslots.setdefault(mat, {})
        imported_tslots[mat][fname] = tex
    if type == DIFFUSE:
        matslot.diffuse_color_factor = 1
        matslot.use_map_color_diffuse = True
    elif type == ALPHA:
        matslot.alpha_factor = 1
        matslot.use_map_alpha = True
        mat.use_transparency = True
        mat.alpha = 0
        mat.transparency_method = "Z_TRANSPARENCY"
    elif type == SPECULAR:
        matslot.specular_color_factor = 1
        matslot.use_map_color_spec = True


def showTextureMap(mat):
    for num, com in enumerate(mat.texture_slots):
        if com is not None:
            if com.texture.type == 'IMAGE':
                mat.use_textures[num] = True


def newUVlayer(mesh, representation, uv_id):
    """copy UV coordinates from layer `uv_id`, from `representation` to the actual blender mesh"""

    num = len(mesh.uv_layers)
    mesh.uv_layers.new()
    uvtex = mesh.uv_layers[num]
    uvtex.name = 'UV '+str(len(mesh.uv_layers)-1)
    # '-1' because count takes the new layer in account and index starts at 0

    for num, com in enumerate(representation.loops):
        if com.UVs[uv_id] is not None:
            uvtex.data[num].uv = (com.UVs[uv_id][0], 1-com.UVs[uv_id][1])
        # else, will be zero

