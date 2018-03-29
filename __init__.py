if "bpy" in locals():  # trick to reload module on f8-press in blender
    LOADED = True
else:
    LOADED = False
import bpy

log_out = None

import logging.config
import io


def config_logging():
    global log_out
    log_out = io.StringIO()
    logging.config.dictConfig({
        'version': 1,
        'formatters': {'default': {'format': '%(asctime)-15s %(levelname)8s %(name)s %(message)s'},
                       'short': {'format': '%(levelname)-8s %(name)s %(message)s'}},
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',  # 'logging.ReloadingHandler',
                'formatter': 'default',
                # 'place': 'sys.stdout',
                'stream': 'ext://sys.stderr'},
            'pipe': {
                'class': 'logging.StreamHandler',
                'formatter': 'short',
                'level': 'WARNING',
                'stream': log_out}},
        'root': {
            'level': 'INFO',
            'handlers': ['console', 'pipe']}
    })


if LOADED:
    from importlib import reload
    reload(BModel)
    reload(MaxH)

else:
    if not logging.root.handlers:
        # if this list is not empty, logging is configured.
        # here, it isn't
        config_logging()
    import blemd.maxheader as MaxH
    from blemd import BModel
del LOADED

IDE_DEBUG = False
log = logging.getLogger('bpy.ops.import_mesh.bmd')

bl_info = {
    "name": "Import gc/wii bmd format (.bmd)",
    "author": "people from the internet. adapted for blender by Niacdoial, from Avatarus-One's version (see github) full explanation in README",
    "version": (1, 0, 0),
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
import os.path as OSPath
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

    #sv_anim = BoolProperty(
    #    name="Import animations (WIP)",
    #    description="",
    #    default=True
    #    )
    sv_anim = EnumProperty(
        name="Import animations(WIP)",
        description="if yes, choice to chain them or put them in individual actions",
        items=(('DONT', "do not import animations", ""),
               ('CHAINED', "import all animations in one single Action object", '(messy, but simple to deal with)'),
               ('SEPARATE', "One Action per animation file", '(for advanced blender users)')),
        default='CHAINED'
        )

    use_nodes = BoolProperty(
        name="use complete materials",
        description="use complete (glsl) materials (converted into nodes). Hard to export.",
        default=False
    )

    frc_cr_bn = BoolProperty(
        name="Force create bones",
        description="",
        default=False
        )

    mir_tx = BoolProperty(
        name="Allow mirrored textures",
        description="",
        default=True
        )

    tx_pck = EnumProperty(
        name="Pack textures",
        description="choose if textures should be inside the blender file or referenced by it",
        items=(('DONT', 'reference external files', ''),
               ('DO', 'pack images in blender file', ''),
               ('PNG', 'pack images IN PNG FORMAT', 'conversion is made by blender')),
        default='DO'
        )

    imtype = EnumProperty(
        name="Image use type",
        description="Choose packed images, native format image, or targa converted ones",
        items=(('TGA', "targa files", ""),
               ('DDS', "dds files", 'this format feels legacy')),
        default='TGA'
        )

    ic_sc = BoolProperty(
        name="include scaling",
        description="needed on some models, glitch others",
        default=True
        )

    dvg = BoolProperty(
        name="DEBUG vertex groups",
        description="DEBUG option. create Vgroups to show the original BMD structure",
        default=False
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

    def execute(self, context):
        global log_out
        retcode = 'FINISHED'
        temp = BModel.BModel()
        path = OSPath.abspath(OSPath.split(__file__)[0])  # automatically find where we are
        temp.SetBmdViewExePath(path+'\\')  # add backslash for good measure
        try:
            temp.Import(self.filepath, self.use_nodes, self.imtype, self.tx_pck, self.mir_tx,
                        self.sv_anim, self.ic_sc, self.frc_cr_bn, self.boneThickness, self.dvg)
        except Exception as err:
            log.critical('An error happened. If it wasn\'t reported before, here it is: %s', err)
            retcode = 'ERROR'
            raise
        finally:
            message = log_out.getvalue()
            log_out.truncate(0)
            if message:
                if retcode == 'ERROR':
                    self.report({'ERROR'}, message)
                else:
                    self.report({'WARNING'}, message)
        return {retcode}


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
