import bpy
import mathutils
import os
from .texhelper import newtex_tslot, getTexImage, showTextureMap, getTexSlot
from mathutils import Color
from . import matpipeline as MPL


def add_material(obj, mat):
    is_in = False
    for m2 in obj.data.materials:
        if mat == m2:
            is_in = True
            break
    if not is_in:
        obj.data.materials.append(mat)
    for num, com in enumerate(obj.material_slots):
        if com.material == mat:
            return num
    raise ValueError("material not successfully added")

def add_err_material(obj):
    mat = bpy.data.materials.new("ERROR MATERIAL")
    mat.diffuse_color = (0,0,1,1)  # WHY are those different types of objects?
    mat.specular_color = mathutils.Color((1,1,1))
    add_material(obj, mat)
    return mat


def build_material_legacy(mIndex, mat1, tex, texpath, ext):
    material = mat1.materialbases[mIndex]
    
    currMaterial = None  # materials may not be defined
    stage = material.texStages[0]  # simplified material: ONE texture

    if stage != 0xffff:  # TODO better reproduce the original behavior when that is not the case
        currMaterial = bpy.data.materials.new("dummy_temp_name-function_v1")

        v2 = mat1.texStageIndexToTextureIndex[stage]
        textureName = tex.stringtable[v2]

        fileName = os.path.join(texpath, textureName + ext)
        bmpFound = os.path.isfile(fileName)

        newtex_tslot(fileName, 'DIFFUSE', currMaterial)
        img = getTexImage(currMaterial, fileName)

        bmp = None
        hasAlpha = False
        if bmpFound:
            # for p in range(3, len(img.pixels), 4):  # pixels stored as individual channels
            #     if img.pixels[p] != 1:  # only get alpha
            #         hasAlpha = True
            #         break
            # else:
            #     hasAlpha = False
            hasAlpha=True
        else:
            # make it easier to see invalid/missing textures
            currMaterial.diffuse_color = (1,0,0,1)

        if hasAlpha:
            # self._currMaterial.twoSided = True # -- anything with alpha is always two sided?
            newtex_tslot(fileName, 'ALPHA', currMaterial)

        showTextureMap(currMaterial)  # -- display texture in view

        # NOTE: check ash.bmd for case when wrapS=2 and wrap=2. u_offset = 0.5 and V_offset = -0.5 [note negative on v]
        if bmpFound:
            if tex.texHeaders[v2].wrapS == 0:
                # clamp to edge? Needs testing. Cannot use .U_Mirror = False and .U_Tile = False. If WrapS == 0 then has Alpha?
                pass
            elif tex.texHeaders[v2].wrapS == 1:  # - repeat (default)
                pass
            elif tex.texHeaders[v2].wrapS == 2:
                # add suffix to let the modeler know where mirror should be used
                currMaterial.name += "_U"
                getTexSlot(currMaterial, fileName).scale[0] = -1
                # self._currMaterial.diffusemap.coords.U_Tile = False
                # self._currMaterial.diffusemap.coords.U_offset = 0.5
                # self._currMaterial.diffusemap.coords.U_Tiling = 0.5
            else:
                raise ValueError("Unknown wrapS " + str(tex.texHeaders[v2].wrapS))
            
            if tex.texHeaders[v2].wrapT == 0:
                # clamp to edge? Needs testing
                pass
            elif tex.texHeaders[v2].wrapT == 1:
                # repeat (default)
                pass
            elif tex.texHeaders[v2].wrapT == 2:
                # add suffix to let the modeler know where mirror should be used
                currMaterial.name += "_V"
                getTexSlot(currMaterial, fileName).scale[1] = -1
                # self._currMaterial.diffusemap.coords.V_Tile = False
                # self._currMaterial.diffusemap.coords.V_offset = 0.5
                # self._currMaterial.diffusemap.coords.V_Tiling = 0.5
            else:
                raise ValueError("Unknown wrapT " + str(tex.texHeaders[v2].wrapS))

    return currMaterial

def build_material_v3(mIndex, mat1, tex1, texpath, ext):
    mbase = mat1.materialbases[mIndex]
    material = bpy.data.materials.new('dummy_temp_name-function_v3')
    material.use_nodes = True
    MPL.createMaterialSystem(mbase, mat1, tex1, texpath, ext, material.node_tree)
    return material
    # mat1.materials[mIndex] = msys

def build_material_simple(mIndex, mat1, tex1, texpath, ext):
    mbase = mat1.materialbases[mIndex]
    material = bpy.data.materials.new('dummy_temp_name-function_simple')
    material.use_nodes = True
    MPL.create_simple_material_system(mbase, mat1, tex1, texpath, ext, material.node_tree)
    return material
    # mat1.materials[mIndex] = msys


def add_vcolor(mesh, representation, layerID):
    """copies vertex colors (layer `layerID`) from the representation to the blender mesh"""

    vx_layer = mesh.vertex_colors.new(name="v_color_"+str(layerID))
    # some really recent, unstable versions of blender 2.79 have alpha support in vertex colors.
    # detect this and react accordingly (or an exception will be raised)
    try:
        vx_layer.data[0].color = (1,0,0,0)
        alpha_support = True
    except:
        alpha_support = False
        vx_layer_a = mesh.vertex_colors.new(name="v_color_alpha_"+str(layerID))
    # alpimg = bpy.data.images.new(mesh.name+'_vcol_alpha_'+str(layerID), 256, 256)
    # XCX image method buggy -> disabled

    if alpha_support:
        for num, com in enumerate(representation.loops):
            if com.VColors[layerID] is not None:
                vx_layer.data[num].color = com.VColors[layerID]
    else:
        for num, com in enumerate(representation.loops):
            if com.VColors[layerID] is not None:
                vx_layer.data[num].color = mathutils.Color(com.VColors[layerID][:3])
                vx_layer_a.data[num].color = mathutils.Color((com.VColors[layerID][3],)*3)
            # else, will be white
