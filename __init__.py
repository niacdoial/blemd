if "bpy" in locals():  # trick to reload module on f8-press in blender
    LOADED = True
else:
    LOADED = False
import bpy
if LOADED:
    unregister()
    from importlib import reload
    del BModel
    reload(BModule)

    from .BModel import BModel
else:
    from importlib import import_module
    from .BModel import BModel
    BModule = import_module('.BModel', "blemd")
del LOADED

import os.path as OSPath
IDE_DEBUG = True

bl_info = {
    "name": "Import gc/wii bmd format (.bmd)",
    "author": "people from the internet. adapted for blender by Niacdoial, from Avatarus-One's version (see github) full explanation in README",
    "version": (0, 5, 0),
    "blender": (2, 77, 0),
    "location": "File > Import > Nintendo BMD",
    "description": "Import files in the gc/wii BMD format (.bmd)",
    "wiki_url": "https://github.com/niacdoial/blemd",
    "warning": "still in devlopement",
    "tracker_url": "???",
    "category": "Import-Export",
}
__version__ = '.'.join([str(s) for s in bl_info['version']])


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator


class ImportBmd(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_mesh.bmd"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import BMD"

    # ImportHelper mixin class uses this
    filename_ext = ".bmd"

    filter_glob = StringProperty(
            default="*.bmd",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    sv_anim = BoolProperty(
        name="Save Animations externally (WIP)",
        description="",
        default=True
        )

    frc_cr_bn = BoolProperty(
        name="force create bones",
        description="",
        default=False
        )

    mir_tx = BoolProperty(
        name="Allow mirrored textures",
        description="",
        default=True
        )

    tx_xp = BoolProperty(
        name="Export textures",
        description="why does this option even exist?",
        default=True
        )

    #ic_sc = BoolProperty(
    #    name="include scaling",
    #    description="DO NOT USE yet",
    #    default=False
    #    )

    dvg = BoolProperty(
        name="DEBUG vertex groups",
        description="DEBUG option. create Vgroups to show the original BMD structure",
        default=False
        )

    #type = EnumProperty(
    #    name="Import Type",
    #   description="Choose between two items",
    #    items=(('XFILE', "x export (games)", ""),),
    #           #('CHARACTER', "character export (animations)", "")),
    #    default='XFILE'
    #    )

    imtype = EnumProperty(
        name="Image use type",
        description="Choose packed images, native format image, or targa converted ones",
        items=(('TARGA', "targa files", ""),
               ('PACKED', "packed dds files", ''),
               ('AS_PNG', "packed dds files as png ones", ''),
               ('NATIVE', 'dds files', '')),
        default='PACKED'
        )

    boneThickness = IntProperty(
        name="bone length",
        description="from 5 to 100 (usually)",
        min=1,
        max=1000,
        soft_min=5,
        soft_max=100,
        default=10
    )

    use_nodes = BoolProperty(
        name="use node materials",
        description="use complete (glsl) materials (converted into nodes), hard to export.",
        default=False
    )

    def execute(self, context):
        temp = BModel()
        path = OSPath.abspath(OSPath.split(__file__)[0])  # automatically find where we are
        temp.SetBmdViewExePath(path+'\\')  # add backslash for good measure
        temp.Import(self.filepath, self.boneThickness, self.mir_tx, self.frc_cr_bn,
                    self.sv_anim, self.tx_xp, 'XFILE', True, self.imtype, self.dvg, self.use_nodes)
        return {'FINISHED'}


# Only needed if you want to add into a dynamic menu
def menu_func(self, context):
    self.layout.operator(ImportBmd.bl_idname, text="Nintendo BMD")


def register():
    print(__name__)
    bpy.utils.register_module(__name__)
    #bpy.utils.register_class(ImportSomeData)
    bpy.types.INFO_MT_file_import.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)
    #bpy.utils.unregister_class(ImportBmd)
    bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == "__main__":
    register()
    if IDE_DEBUG:
        bpy.ops.blemd.importer()
