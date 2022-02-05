import bpy
import sys
import os.path
path=' '.join(sys.argv[4:])  # path to the bmd file

bpy.data.objects.remove(bpy.data.objects['Cube'])
bpy.data.meshes.remove(bpy.data.meshes['Cube'])

bpy.data.objects.remove(bpy.data.objects['Lamp'])
bpy.data.lamps.remove(bpy.data.lamps['Lamp'])

bpy.data.objects.remove(bpy.data.objects['Camera'])
bpy.data.cameras.remove(bpy.data.cameras['Camera'])

try:
    bpy.ops.blemd.importer(filepath=path)
except AttributeError:  # module not loaded: do it manually
    import blemd
    temp = blemd.BModel.BModel()
    # current_dir = OSPath.abspath(OSPath.split(__file__)[0])  # automatically find where we are
    temp.SetBmdViewExePath(OSPath.split(blemd.__file__)[0]+os.path.sep)  # add backslash for good measure
    temp.Import(path,
        boneThickness=5,
        mir_tx=True,
        frc_cr_bn=False,
        sv_anim='DO',
        tx_pck='PNG',
        ic_sc=True,
        imtype='TGA'
    )
    # actual model importing


# this line (below) is the export command. feel free to change it to whatever you want
bpy.ops.export_scene.fbx(filepath=path[:-3]+'fbx', axis_forward='Y', axis_up='Z', path_mode='COPY', embed_textures=True)

bpy.ops.wm.quit_blender()  # quit blender the clean way
