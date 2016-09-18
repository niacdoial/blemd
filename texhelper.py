import bpy
import bpy_extras
import mathutils
from .maxheader import getFilenameFile


imported = {}
force_names = {}

DIFFUSE = 'DIFFUSE'
ALPHA = 'ALPHA'
SPECULAR = 'SPECULAR'


def getTexImage(mat, fname):
    global imported
    return imported[mat][fname].image


def getTexSlot(mat, fname):
    for com in mat.texture_slots:
        if com is not None:
            if com.texture == imported[mat][fname]:
                return com


def newtex(fname, type, mat):
    global imported
    if mat in imported.keys() and fname in imported[mat].keys():
        tex = imported[mat][fname]
        matslot = getTexSlot(mat, fname)
    else:
        if fname in force_names.keys():
            img = force_names[fname]
        else:
            img = bpy.data.images.load(fname)
            img.pack()
        tex = bpy.data.textures.new(getFilenameFile(fname)+'_texture', type='IMAGE')
        mat.name = getFilenameFile(fname)+'_material'
        tex.image = img
        tex.use_interpolation = True
        tex.filter_type = 'EWA'
        tex.filter_size = 1
        tex.use_alpha = True
        matslot = mat.texture_slots.add()
        matslot.texture = tex
        matslot.texture_coords = 'UV'
        if mat not in imported.keys():
            imported[mat] = {}
        imported[mat][fname] = tex
    if type == DIFFUSE:
        matslot.diffuse_color_factor = 1
        matslot.use_map_color_diffuse = True
    elif type == ALPHA:
        matslot.alpha_factor = 1
        matslot.use_map_alpha = True
    elif type == SPECULAR:
        matslot.specular_color_factor = 1
        matslot.use_map_color_spec = True


def showTextureMap(mat):
    for num, com in enumerate(mat.texture_slots):
        if com is not None:
            if com.texture.type == 'IMAGE':
                mat.use_textures[num] = True


def newUVlayer(mesh, tverts, tfaces, Faces):
    # probably one of the hardest functions to fathom.
    #it's goal is to set the right UV coords to the right UV point.
    # with the fact that most verts had changed index between steps. gah.

    num = len(mesh.uv_textures)
    mesh.uv_textures.new()
    uvtex = mesh.uv_layers[num]

    # ##--meshop.setNumMapVerts modelMesh uv tverts[uv].count

    # verts in Faces and mesh.polygons are aligned
    # so are the face of Faces and tFaces

    #verts are aligned. are faces too?
    rf_to_f = []  # blender faces index to loaded faces index
    for com in mesh.polygons:
        rf_to_f.append(Faces.index(list(com.vertices)))

    #for f, rf in enumerate(rf_to_f):
    #    f_to_l[f] = rf_to_l[rf]
    #    rf_to_tf[rf] = f  # f_to_tf[f]
        # rf_to_v = [com.vertices for com in mesh.polygons]
    v_f_to_l = []
    for com in range(len(mesh.vertices)):
        v_f_to_l.append({})
    for num, com in enumerate(mesh.polygons):
        for com2 in com.loop_indices:
            l_id = mesh.loops[com2].index
            v_f_to_l[mesh.loops[com2].vertex_index][num] = l_id

    for num, com in enumerate(tfaces):
        for com2 in Faces:
            uvtex.data[v_f_to_l[com2[0]] [rf_to_f[num]]].uv = mathutils.Vector((tverts[com[0]][:2]))
            uvtex.data[v_f_to_l[com2[1]] [rf_to_f[num]]].uv = mathutils.Vector((tverts[com[1]][:2]))
            uvtex.data[v_f_to_l[com2[2]] [rf_to_f[num]]].uv = mathutils.Vector((tverts[com[2]][:2]))



    # must make correspond faces and UV faces, so must associate UV_verts to 3D_verts.
    #rf_to_l = []  # blender faces index to loop indexES
    #for com in mesh.polygons:
    #    rf_to_l.append([com2 for com2 in com.loop_indices])

    #tf_to_tv = []  # is that part useless?
    #for com in tfaces:
    #    tf_to_tv.append((com[0], com[1], com[2]))

    ## TODO: check orientation:
    #tv_to_v = [-1]*(3*len(tf_to_tv))  # loaded texvert index to loaded vert index (is that identity?)
    #for num, com in enumerate(tf_to_tv):
    #    tv_to_v[com[0]] = Faces[num][0]
    #    tv_to_v[com[1]] = Faces[num][1]
    #    tv_to_v[com[2]] = Faces[num][2]

    #l_to_v = [com.vertex_index for com in mesh.loops]
    #v_to_l = [None]*len(mesh.vertices)  # blender vertex index to loop loop index(ES?)
    #for com in mesh.loops:
    #    v_to_l[com.vertex_index] = com.index

    #for i in range(len(tverts)):
    #    if tverts[i] is not None:
    #        uvtex.data[v_to_l[tv_to_v[i]]].uv = mathutils.Vector(tverts[i][:2])
    #    else:
    #        raise ValueError('must implement unused UV verts')

    ## ##--meshop.buildMapFaces modelMesh uv

    #for i in range(len(tfaces)):  # auto-set by blender. but undefined faces are definite sources of complere chaos in UVs
    #    if tfaces[i] is not None:  # -- TODO: should never have undefined texture faces
    #        pass
    #        #meshop.setMapFace(modelMesh, uv, i, tFaces[i]) # XCX
    #    else:
    #        raise ValueError("must implement unused UV faces")


def addforcedname(real, fake):
    global force_names
    if fake in force_names.keys():
        return
    img = bpy.data.images.load(real)
    img.pack()
    force_names[fake] = img

