import bpy
import bpy_extras
import mathutils
from .maxheader import getFilenameFile


imported_tslots = {}
imported_textures = {}
force_names = {}

DIFFUSE = 'DIFFUSE'
ALPHA = 'ALPHA'
SPECULAR = 'SPECULAR'

# used to set mode before calls
MODE = 'PACKED'

def getTexImage(mat, fname):
    global imported_tslots
    return imported_tslots[mat][fname].image


def getTexSlot(mat, fname):
    for com in mat.texture_slots:
        if com is not None:
            if com.texture == imported_tslots[mat][fname]:
                return com

def newtex_tex(fname, _loaded_images=[], export_function=(lambda: None)):
    global forced_names
    global imported_textures
    global MODE
    if fname in imported_textures.keys():
        return imported_textures[fname]

    if fname in force_names.keys():
        img = force_names[fname]
    else:
        # if fname not in _loaded_images:  # XCX is this useless?
        #    export_function(force=True)
        img = bpy.data.images.load(fname)
    if MODE == 'PACKED':
        img.pack()
    elif MODE == 'AS_PNG':
        img.pack(as_png=True)
    elif MODE == 'TARGA':
        tgaconvert(img)
    tex = bpy.data.textures.new(getFilenameFile(fname) + '_texture', type='IMAGE')

    tex.image = img
    tex.use_interpolation = True
    tex.filter_type = 'EWA'
    tex.filter_size = 1
    tex.use_alpha = True

    imported_textures[fname] = tex
    return tex

def newtex_tslot(fname, type, mat, _loaded_images=[], export_function=(lambda: None)):
    global imported_tslots
    if mat in imported_tslots.keys() and fname in imported_tslots[mat].keys():
        tex = imported_tslots[mat][fname]
        matslot = getTexSlot(mat, fname)
    else:
        mat.name = getFilenameFile(fname)+'_material'
        tex = newtex_tex(fname, _loaded_images, export_function)
        matslot = mat.texture_slots.add()
        matslot.texture = tex
        matslot.texture_coords = 'UV'
        if mat not in imported_tslots.keys():
            imported_tslots[mat] = {}
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


def tgaconvert(img):
    img.pack()
    img.filepath_raw = img.filepath_raw[:-3]+'tga'
    img.file_format = 'TARGA'
    img.packed_files[0].filepath = img.packed_files[0].filepath[:-3]+'tga'
    img.unpack(method='WRITE_ORIGINAL')


def showTextureMap(mat):
    for num, com in enumerate(mat.texture_slots):
        if com is not None:
            if com.texture.type == 'IMAGE':
                mat.use_textures[num] = True


def newUVlayer_old(mesh, tverts, tfaces, Faces, tv_to_f_v):
    # probably one of the hardest functions to fathom.
    #it's goal is to set the right UV coords to the right UV point.
    # with the fact that most verts had changed index between steps. gah.

    num = len(mesh.uv_textures)
    mesh.uv_textures.new()
    uvtex = mesh.uv_layers[num]
    uvtex.name = 'UV '+str(len(mesh.uv_layers)-1)
    # '-1' because count takes the new layer in account and index starts at 0

    # ##--meshop.setNumMapVerts modelMesh uv tverts[uv].count

    # verts in Faces and mesh.polygons are aligned
    # so are the face of Faces and tFaces

    #verts are aligned. are faces too?
    f_to_rf = [None]*len(mesh.polygons)  # blender faces index to loaded faces index
    for num, com in enumerate(mesh.polygons):  # will be identity _MOST_ of the time
        index = Faces.index(tuple(com.vertices))
        while f_to_rf[index] is not None:
            index = Faces.index(tuple(com.vertices), index+1)
        f_to_rf[index] = num
    # -- TODO: should never have undefined texture faces
    #for f, rf in enumerate(f_to_rf):
    #    f_to_l[f] = rf_to_l[rf]
    #    rf_to_tf[rf] = f  # f_to_tf[f]
        # rf_to_v = [com.vertices for com in mesh.polygons]
    v_rf_to_l = []
    for com in range(len(mesh.vertices)):
        v_rf_to_l.append({})
    for num, com in enumerate(mesh.polygons):
        for com2 in com.loop_indices:
            l_id = mesh.loops[com2].index
            v_rf_to_l[mesh.loops[com2].vertex_index][num] = l_id

    # those lines are a new method.
    for num, com0 in enumerate(tv_to_f_v):
        for com in com0:
            if f_to_rf[com[0]] is not None:
                for com2 in mesh.polygons[f_to_rf[com[0]]].loop_indices:
                    if mesh.loops[com2].vertex_index == com[1]:
                        uvtex.data[com2].uv = mathutils.Vector(tverts[num][:2])


def newUVlayer(mesh, representation, uv_id):
    """copy UV coordinates from layer `uv_id`, from `representation` to the actual blender mesh"""

    num = len(mesh.uv_textures)
    mesh.uv_textures.new()
    uvtex = mesh.uv_layers[num]
    uvtex.name = 'UV '+str(len(mesh.uv_layers)-1)
    # '-1' because count takes the new layer in account and index starts at 0

    for num, com in enumerate(representation.loops):
        uvtex.data[num].uv = com.UVs[uv_id][0:2]


def addforcedname(real, fake):
    global force_names
    if fake in force_names.keys():
        return
    img = bpy.data.images.load(real)
    img.pack()
    force_names[fake] = img

