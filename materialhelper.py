import bpy
import mathutils
import os.path as OSPath
from .texhelper import newtex_tslot, getTexImage, showTextureMap, getTexSlot
from mathutils import Color


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
    #act_bk = bpy.context.active_object
    #bpy.context.scene.objects.active = obj
    #num = len(obj.material_slots)
    #bpy.ops.object.material_slot_add()
    #mat_slot = obj.material_slots[num]
    #mat_slot.material = mat
    #bpy.context.scene.objects.active = act_bk

def add_err_material(obj):
    mat = bpy.data.materials.new("ERROR MATERIAL")
    mat.diffuse_color = mathutils.Color((0,0,1))
    mat.specular_color = mathutils.Color((1,1,1))
    mat.diffuse_intensity = 1
    add_material(obj, mat)
    return mat


def build_material(bmodel, mat1, material, tex, _images, ExtractImages):

    currMaterial = None  # materials may not be defined
    stage = material.texStages[0]  # XCX multiples textures
    num = 0
    if stage != 0xffff:
        currMaterial = bpy.data.materials.new("temp_name_whatsoever")  # name will be erased afterwards, in a subcall
    # while stage != 0xffff:  # ONE texture for now
        textureName = ""
        v2 = mat1.texStageIndexToTextureIndex[stage]  # -- undefined if stage = 0xffff

        # -- v2 used latter. value is undefined if stage == 0xffff
        textureName = tex.stringtable[v2]

        # --self.textureName = matName
        fileName = bmodel._texturePath + textureName + ".tga"
        bmpFound = OSPath.exists(fileName) or OSPath.exists(fileName[:-4] + '.dds')  # two image types!

        # -- messageBox fileName
        newtex_tslot(fileName, 'DIFFUSE', currMaterial, _images, ExtractImages)
        img = getTexImage(currMaterial, fileName)

        # --gc()
        bmp = None
        hasAlpha = False
        if bmpFound:
            alp = 0
            for p in range(3, len(img.pixels), 4):  # pixels stored as individual channels
                if True:  # img.pixels[p] != 1:  # only get alpha
                    # alp = img.pixels[p]
                    hasAlpha = True
                    break
                    # hasAlpha = (p == len(img.pixels)-1)
        else:
            # -- make it easier to see invalid textures
            currMaterial.diffuse_color = Color((1, 0, 0))

        if hasAlpha:
            # self._currMaterial.twoSided = True # -- anything with alpha is always two sided?
            newtex_tslot(fileName, 'ALPHA', currMaterial, _images, ExtractImages)

        showTextureMap(currMaterial)  # -- display self.texture in view

        # -- messageBox (matName + (self.tex.self.texHeaders[v2].wrapS as string) + "+" + (self.tex.self.texHeaders[v2].wrapT as string))
        # -- NOTE: check ash.bmd for case when wrapS=2 and wrap=2. u_offset = 0.5 and V_offset = -0.5 [note negative on v]

        if bmpFound:
            if tex.texHeaders[
                v2].wrapS == 0:  # - clamp to edge? Needs testing. Cannot use .U_Mirror = False and .U_Tile = False. If WrapS == 0 then has Alpha?
                pass
            elif tex.texHeaders[v2].wrapS == 1:  # - repeat (default)
                pass
            elif tex.texHeaders[v2].wrapS == 2:
                currMaterial.name += "_U"  # -- add suffix to let the modeler know where mirror should be used
                if bmodel._allowTextureMirror:
                    getTexSlot(currMaterial, fileName).scale[0] = -1
                    # self._currMaterial.diffusemap.coords.U_Tile = False
                    # self._currMaterial.diffusemap.coords.U_offset = 0.5
                    # self._currMaterial.diffusemap.coords.U_Tiling = 0.5
            else:
                raise ValueError("Unknown wrapS " + str(tex.texHeaders[v2].wrapS))
            if tex.texHeaders[v2].wrapT == 0:  # - clamp to edge? Needs testing
                pass
            elif tex.texHeaders[v2].wrapT == 1:  # - repeat (default)
                pass
                #					self._currMaterial.diffusemap.coords.V_Mirror = False
                #					self._currMaterial.diffusemap.coords.V_Tile = True
                #
                #					if (hasAlpha) then
                #					(
                #						self._currMaterial.opacityMap.coords.V_Mirror = False
                #						self._currMaterial.opacityMap.coords.V_Tile = True
                #					)
            elif tex.texHeaders[v2].wrapT == 2:
                currMaterial.name += "_V"  # -- add suffix to let the modeler know where mirror should be used
                if bmodel._allowTextureMirror:
                    getTexSlot(currMaterial, fileName).scale[1] = -1
                    # self._currMaterial.diffusemap.coords.V_Tile = False
                    # self._currMaterial.diffusemap.coords.V_offset = 0.5
                    # self._currMaterial.diffusemap.coords.V_Tiling = 0.5
            else:
                raise ValueError("Unknown wrapT " + str(tex.texHeaders[v2].wrapS))
        num += 1
        stage = material.texStages[num]

    return currMaterial


def add_vcolor_old(mesh, color_layer, cv_to_f_v, Faces, uvlayer, layerID):

    vx_layer = mesh.vertex_colors.new("v_color_"+str(layerID))
    vx_layer_a = mesh.vertex_colors.new("v_color_alpha_"+str(layerID))
    # alpimg = bpy.data.images.new(mesh.name+'_vcol_alpha_'+str(layerID), 256, 256)
    # XCX image method buggy -> disabled

    l_to_v = []
    for com in mesh.loops:
        l_to_v.append(com.vertex_index)

    # verts in Faces and mesh.polygons are aligned
    # so are the face of Faces and tFaces

    #verts are aligned. are faces too?
    f_to_rf = [None]*len(mesh.polygons)  # blender faces index to loaded faces index
    for num, com in enumerate(mesh.polygons):  # will be identity most of the time
        index = Faces.index(tuple(com.vertices))
        while f_to_rf[index] is not None:
            index = Faces.index(tuple(com.vertices), index+1)
        f_to_rf[index] = num
    v_rf_to_l = []
    for com in range(len(mesh.vertices)):
        v_rf_to_l.append({})
    for num, com in enumerate(mesh.polygons):
        for com2 in com.loop_indices:
            l_id = mesh.loops[com2].index
            v_rf_to_l[mesh.loops[com2].vertex_index][num] = l_id

    for num, com0 in enumerate(cv_to_f_v):
        for com in com0:
            if f_to_rf[com[0]] is not None:
                for com2 in mesh.polygons[f_to_rf[com[0]]].loop_indices:
                    if mesh.loops[com2].vertex_index == com[1]:
                        DBG_temp = [list(color_layer[num])[3]]*3
                        vx_layer_a.data[com2].color = mathutils.Color(DBG_temp)

    #for face in range(len(mesh.polygons)):
    #    uvlayer.data[face].image = alpimg
    #mesh.update()  # disabled block that goes with the image

    #for i in range(len(l_to_v)):  # fixed
    #    DBG_temp = list(color_layer[l_to_v[i]])[0]
    #    vx_layer.data[i].color = mathutils.Color(DBG_temp*3)  # use alpha to override everything
    #    # meshop.setVertAlpha(mesh, -2, i, color_layer[i].a)  # XCX

    # baking VC alpha to UV texture

    #bpy.context.scene.render.bake_type = 'VERTEX_COLORS'
    #bpy.context.scene.render.use_bake_to_vertex_color = False
    #alpimg.pack(as_png=True)  # disabled block
    # bpy.ops.object.bake_image()  # forget this yet. XCX crashes
    #alpimg.pack(as_png=True)

    ## RE-setting the correct Vcols
    for num, com0 in enumerate(cv_to_f_v):
        for com in com0:
            if f_to_rf[com[0]] is not None:
                for com2 in mesh.polygons[f_to_rf[com[0]]].loop_indices:
                    if mesh.loops[com2].vertex_index == com[1]:
                        DBG_temp = list(color_layer[num])[:3]
                        vx_layer.data[com2].color = mathutils.Color(DBG_temp)
    #for i in range(len(l_to_v)):  # fixed
    #    vx_layer.data[i].color = mathutils.Color(list(color_layer[l_to_v[i]])[:3])  # remove alpha(supported earlier in this file)

    for face in range(len(mesh.polygons)):
        try:
            uvlayer.data[face].image = mesh.materials[mesh.polygons[face].material_index].texture_slots[0].texture.image
        except AttributeError:
            # in case of undetected material:
            pass

    # return alpimg


def add_vcolor(mesh, representation, layerID):
    """copies vertex colors (layer `layerID`) from the representation to the blender mesh"""

    vx_layer = mesh.vertex_colors.new("v_color_"+str(layerID))
    vx_layer_a = mesh.vertex_colors.new("v_color_alpha_"+str(layerID))
    # alpimg = bpy.data.images.new(mesh.name+'_vcol_alpha_'+str(layerID), 256, 256)
    # XCX image method buggy -> disabled

    for num, com in enumerate(representation.loops):
        vx_layer.data[num].color = mathutils.Color(com.VColors[layerID][:3])
        vx_layer_a.data[num].color = mathutils.Color(tuple(com.VColors[layerID][3])*3)
