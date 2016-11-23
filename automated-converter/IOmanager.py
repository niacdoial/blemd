import bpy
import sys
path=' '.join(sys.argv[4:])

bpy.data.objects.remove(bpy.data.objects['Cube'],True)
bpy.data.meshes.remove(bpy.data.meshes['Cube'],True)

bpy.data.objects.remove(bpy.data.objects['Lamp'],True)
bpy.data.lamps.remove(bpy.data.lamps['Lamp'],True)

bpy.data.objects.remove(bpy.data.objects['Camera'],True)
bpy.data.cameras.remove(bpy.data.cameras['Camera'],True)

try:
    bpy.ops.blemd.importer(filepath=path)
except AttributeError:  # module not here
    import blemd
    temp = blemd.BModel()
    temp.SetBmdViewExePath('C:\\Users\\Liam\\Bureau\\MaxBMD-multi-texcoords\\')
    temp.Import(path, 5, True, False, True, True, 'XFILE', False, False)

bpy.ops.export_scene.fbx(filepath=path[:-3]+'fbx', axis_forward='Y', axis_up='Z')

bpy.ops.wm.quit_blender()
