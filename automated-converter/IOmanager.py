import bpy
import sys
import os.path
input_path=sys.argv[-1]  # path to the bmd file
name = os.path.splitext(os.path.basename(input_path))[0]
basedir = os.path.dirname(input_path)


#### here are some parameters that need to be changed manually

# export multiple fbx files, one per imported animation
one_file_per_action = True

# forcefully concatenate all animations into one large animation
# not recommended, but might be necessary on earlier versions of blender, depending on how good the fbx exporter was
force_fuse_animations = False

if force_fuse_animations and one_file_per_action:
    print("ERROR: you asked for two mutually exclusive options when editing IOmanager.py")
    bpy.ops.wm.quit_blender()


#### and now the code itself

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
        import_anims_type= ('CHAINED' if force_fuse_animations else 'SEPARATE'),
        no_rot_cv=True,
        tx_pck='DO',
        ic_sc=True,
        imtype='TGA'
    )
    # actual model importing

def do_export(override_name=None, **kw):
    if override_name is not None:
        path = os.path.join(basedir, override_name + '.fbx')
    else:
        path = input_path[:-4]+'.fbx'
    # this line (below) is the export command. feel free to change it to whatever you want
    bpy.ops.export_scene.fbx(filepath=path, axis_forward='-Z', axis_up='Y', path_mode='COPY', embed_textures=True, **kw)


if one_file_per_action:
    # note: this RELIES on "import_anims_type='SEPARATE'" from earlier
    armature = bpy.data.objects[name + '_armature']
    actions = [strip.action for strip in armature.animation_data.nla_tracks[0].strips]
    armature.animation_data_clear()
    armature.animation_data_create()
    armature.animation_data.use_nla = False
    
    for action in actions:
        armature.animation_data.action = action
        do_export(override_name=action.name, bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False)
else:
    do_export()

bpy.ops.wm.quit_blender()  # quit blender the clean way
