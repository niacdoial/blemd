import bpy
import sys
import os.path
input_path=sys.argv[-1]  # path to the bmd file
name = os.path.splitext(os.path.basename(input_path))[0]
basedir = os.path.dirname(input_path)


#### here are some parameters that need to be changed manually
one_file_per_action = False


bpy.data.objects.remove(bpy.data.objects['Cube'])
bpy.data.meshes.remove(bpy.data.meshes['Cube'])

bpy.data.objects.remove(bpy.data.objects['Light'])
bpy.data.lights.remove(bpy.data.lights['Light'])

bpy.data.objects.remove(bpy.data.objects['Camera'])
bpy.data.cameras.remove(bpy.data.cameras['Camera'])

try:
    bpy.ops.blemd.importer(filepath=input_path)
except AttributeError:  # module not loaded: do it manually
    import blemd
    temp = blemd.BModel.BModel()
    # current_dir = OSPath.abspath(OSPath.split(__file__)[0])  # automatically find where we are
    temp.SetBmdViewExePath(os.path.split(blemd.__file__)[0]+os.path.sep)  # add backslash for good measure
    temp.Import(input_path,
        boneThickness=5,
        frc_cr_bn=False,
        import_anims=True,
        # I'm pretty sure nla tracks don't fully work when exporting to fbx
        import_anims_type= ('SEPARATE' if one_file_per_action else 'CHAINED'),
        no_rot_cv=True,
        tx_pck='DO',
        ic_sc=True,
        imtype='TGA'
    )
    # actual model importing

def do_export(override_name=None):
    if override_name is not None:
        path = os.path.join(basedir, override_name + '.fbx')
    else:
        path = input_path[:-4]+'.fbx'
    # this line (below) is the export command. feel free to change it to whatever you want
    bpy.ops.export_scene.fbx(filepath=path, axis_forward='-Z', axis_up='Y', path_mode='COPY', embed_textures=True)


if one_file_per_action:
    # note: this RELIES on "import_anims_type='CHAINED'" from earlier
    animdata = bpy.data.objects[name + '_armature'].animation_data
    #print([action.name for action in bpy.data.actions])
    #actions = [action for action in bpy.data.actions if action.name.startswith(name)]
    print(animdata, len(animdata.nla_tracks), animdata.use_nla)
    #animdata.nla_tracks.update()
    actions = [strip.action for strip in animdata.nla_tracks[0].strips]
    for action in actions:
        animdata.action = action
        do_export(override_name=action.name)
else:
    do_export()

bpy.ops.wm.quit_blender()  # quit blender the clean way
