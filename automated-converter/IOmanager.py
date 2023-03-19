import bpy
import sys
import os.path
path=sys.argv[-1]  # path to the bmd file

print("importing path", path, sys.argv)

bpy.data.objects.remove(bpy.data.objects['Cube'])
bpy.data.meshes.remove(bpy.data.meshes['Cube'])

bpy.data.objects.remove(bpy.data.objects['Light'])
bpy.data.lights.remove(bpy.data.lights['Light'])

bpy.data.objects.remove(bpy.data.objects['Camera'])
bpy.data.cameras.remove(bpy.data.cameras['Camera'])

try:
    bpy.ops.blemd.importer(filepath=path)
except AttributeError:  # module not loaded: do it manually
    import blemd
    temp = blemd.BModel.BModel()
    # current_dir = OSPath.abspath(OSPath.split(__file__)[0])  # automatically find where we are
    temp.SetBmdViewExePath(os.path.split(blemd.__file__)[0]+os.path.sep)  # add backslash for good measure
    temp.Import(path,
        boneThickness=5,
        frc_cr_bn=False,
        import_anims=True,
        import_anims_type='CHAINED',
        no_rot_cv=True,
        tx_pck='DO',
        ic_sc=True,
        imtype='TGA'
    )
    # actual model importing


# this line (below) is the export command. feel free to change it to whatever you want
bpy.ops.export_scene.fbx(filepath=path[:-3]+'fbx', axis_forward='-Z', axis_up='Y', path_mode='COPY', embed_textures=True)

bpy.ops.wm.quit_blender()  # quit blender the clean way
