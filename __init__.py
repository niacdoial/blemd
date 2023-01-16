#!/usr/bin/env python3

bl_info = {
    "name": "Import gc/wii bmd format (.bmd, .bdl)",
    "author": "people from the internet. adapted for blender by Niacdoial, from Avatarus-One's version (see github) full explanation in README",
    "version": (1, 1, 0),
    "blender": (2, 83, 0),
    "location": "File > Import > Nintendo BMD",
    "description": "Import files in the gc/wii BMD format (.bmd, .bdl)",
    "wiki_url": "https://github.com/niacdoial/blemd",
    "warning": "still in devlopement",
    "tracker_url": "https://github.com/niacdoial/blemd/issues",
    "category": "Import-Export",
}
__version__ = '.'.join([str(s) for s in bl_info['version']])


# ##################################
# base imports and beginning of file

if "bpy" in locals():  # trick to reload module on f8-press in blender
    LOADED = True
else:
    LOADED = False
    log_out = None
import bpy

IDE_DEBUG = False


import logging.config
import io, os
# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator


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
                'level': 'DEBUG',
                'stream': 'ext://sys.stderr'},
            'pipe': {
                'class': 'logging.StreamHandler',
                'formatter': 'short',
                'level': 'WARNING',
                'stream': log_out}},
        'root': {
            'level': 'DEBUG',
            'handlers': ['console', 'pipe']}
    })


if LOADED:
    from importlib import reload
    reload(BModel)
    reload(common)
    #log_out = log.handlers[1].stream  # kinda hacky, but it works (?)
else:
    if not logging.root.handlers:
        # if this list is not empty, logging is configured.
        # here, it isn't
        config_logging()
    from . import common, BModel
del LOADED

log = logging.getLogger('bpy.ops.import_mesh.bmd')


class ImportBmd(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_mesh.bmd"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import BMD"

    # ImportHelper mixin class uses this
    filename_ext = ".bmd"

    filter_glob: StringProperty(
        default="*.bmd;*.bdl",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    import_anims: BoolProperty(
        name="Import animations",
        description="",
        default=True
    )
    
    import_anims_type: EnumProperty(
        name="Animation Mode",
        description="If you choose to import animations, you can choose to chain them or put them in individual actions",
        items=(('SEPARATE', "Separate", 'Animations will be imported into individual actions inside an NLA Track'),
               ('CHAINED', "Chained", 'Animations will be imported one after another into a single action'),
               ),
        default='SEPARATE'
    )

    use_nodes: BoolProperty(
        name="Use complete materials",
        description="Use complete GLSL materials converted into nodes."
                    "More precise, but impossible to export for now.",
        default=True
    )

    frc_cr_bn: BoolProperty(
        name="Force bone creation",
        description="",
        default=False
    )

    nat_bn: BoolProperty(
        name="Use natural bone placement",
        description="Make any animation bone with a single child animation bone point towards it.\n(WARNING: discards animations)",
        default=False
    )

    no_rot_cv: BoolProperty(
        name="Disable axis conversion",
        description="Disable converting the Y-up BMD space into the Z-up blender space. (Reinforced compatibility with other BMD import tools)",
        default=False
    )

    val_msh: BoolProperty(
        name="Validate mesh [!]",
        description="Use this ONLY if blender crashes otherwise.\nMesh WILL be very inaccurate for material mapping.\n"
        "If you are forced to use this option, start an issue on github and please include the console log.",
        default=False
    )

    tx_pck: EnumProperty(
        name="Pack textures",
        description="Choose if textures should be inside the blender file or referenced by it",
        items=(('DONT', 'Reference external files', ''),
               ('DO', 'Pack images in blender file', '')),
        default='DO'
    )

    imtype: EnumProperty(
        name="Image format",
        description="The Format at which to store the image.\n"
                    "If an image is missing, try changing this setting",
        items=(('TGA', "targa files", ""),
               ('DDS', "dds files", '(this format has less support from Blender)')),
        default='TGA'
    )

    ic_sc = BoolProperty(
        name="Include scaling",
        description="This will help make some models look right, bur has the opposite effect on others.",
        default=True
    )

    boneThickness: IntProperty(
        name="Bone length",
        description="the length of what represents bones in blender Only affects visibility. usually from 5 to 100.",
        min=1,
        max=1000,
        soft_min=5,
        soft_max=100,
        default=10
    )

    dvg: BoolProperty(
        name="DEBUG vertex groups",
        description="This is a debugging option.\n"
                    "Creates Vgroups to show the original BMD structure (warning: ram-intensive)",
        default=False
    )

    paranoia: BoolProperty(
        name="DEBUG crashes",
        description="This is a dubugging option.\n"
                    "Produces cleaner crashes",
        default=False
    )

    ALL_PARAMS = ['use_nodes', 'imtype', 'tx_pck', 'import_anims', 'import_anims_type',
                  'nat_bn', 'ic_sc', 'frc_cr_bn', 'boneThickness', 'dvg', 'val_msh', 'paranoia', 'no_rot_cv']

    def execute(self, context):
        global log_out
        retcode = 'FINISHED'
        
        temp = BModel.BModel()
        path = os.path.abspath(os.path.split(__file__)[0])  # automatically find where we are
        
        print(__file__)
        
        try:
            temp.SetBmdViewExePath(path + os.sep)  # add 'backslash' for good measure
            temp.Import(filename=self.filepath, **{x: getattr(self, x) for x in self.ALL_PARAMS})
        except Exception as err:
            log.critical('An error happened. If it wasn\'t reported before, here it is: %s', err)
            retcode = 'ERROR'
            raise
        finally:
            try:
                message = log_out.getvalue()
                message = common.dedup_lines(message)
                
                log_out.truncate(0)
            except:
                message = "warning: logging glitched out. see system console for a more complete result"
                
            if message:
                if retcode == 'ERROR':
                    self.report({'ERROR'}, message)
                else:
                    self.report({'WARNING'}, message)
                    
        return {retcode}
        
    def draw(self, context):
        pass


class BMD_PT_import_options(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Options"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "IMPORT_MESH_OT_bmd"
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator
        
        layout.prop(operator, 'no_rot_cv')
        layout.prop(operator, 'use_nodes')


class BMD_PT_import_animation(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Animation"
    bl_parent_id = "BMD_PT_import_options"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "IMPORT_MESH_OT_bmd"
        
    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        self.layout.enabled = getattr(operator, 'nat_bn') != True
        self.layout.prop(operator, "import_anims", text="")
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator
        
        layout.enabled = operator.import_anims and not operator.nat_bn
        layout.prop(operator, 'import_anims_type')


class BMD_PT_import_armature(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Armature"
    bl_parent_id = "BMD_PT_import_options"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "IMPORT_MESH_OT_bmd"
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator
        
        layout.prop(operator, 'frc_cr_bn')
        layout.prop(operator, 'nat_bn')
        layout.prop(operator, 'boneThickness')


class BMD_PT_import_texture(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Texture"
    bl_parent_id = "BMD_PT_import_options"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "IMPORT_MESH_OT_bmd"
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator
        
        layout.prop(operator, 'tx_pck')
        layout.prop(operator, 'imtype')
        

class BMD_PT_import_debug(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "DEBUG"
    bl_parent_id = "BMD_PT_import_options"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "IMPORT_MESH_OT_bmd"
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator
        
        layout.prop(operator, 'dvg')
        layout.prop(operator, 'paranoia')
        layout.prop(operator, 'val_msh')
    

class ACTION_UL_animentry(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        else:
            layout.label(text="", translate=False, icon_value=icon)


class AnimationPropertyPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "BCK Properties"
    bl_idname = "OBJECT_PT_animationproperties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    
    def __init__(self):
        self.active_action = 0
    
    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if obj.animation_data is None or len(obj.animation_data.nla_tracks) == 0:
            layout.label(text="No animation data to edit!")
            pass
        
        # This is the list of strips that are currently part of the selected object's first NLA track.
        layout.template_list("ACTION_UL_animentry", "", obj.animation_data.nla_tracks[0], "strips", obj, "active_action_index")
        
        layout.row().prop(obj.animation_data.nla_tracks[0].strips[obj.active_action_index], "name")
        layout.row().prop(obj.animation_data.nla_tracks[0].strips[obj.active_action_index].action, "bck_loop_type")
    

# Only needed if you want to add into a dynamic menu
def import_menu_func(self, context):
    self.layout.operator(ImportBmd.bl_idname, text="Nintendo BMD/BDL")
    

def register():
    bpy.utils.register_class(ImportBmd)
    bpy.utils.register_class(BMD_PT_import_options)
    bpy.utils.register_class(BMD_PT_import_armature)
    bpy.utils.register_class(BMD_PT_import_animation)
    bpy.utils.register_class(BMD_PT_import_texture)
    bpy.utils.register_class(BMD_PT_import_debug)
    
    bpy.types.Object.active_action_index = bpy.props.IntProperty(default=0)
    bpy.types.Action.bck_loop_type = bpy.props.EnumProperty(
        name="Loop Type",
        items=(
               ('ONESHOT', "One-shot", 'Animation plays once, then freezes on the last frame'),
               ('ONESHOT_RESET', "One-shot Reset", 'Animation plays once, then resets to the first frame'),
               ('LOOP', "Loop", 'Animation plays continuously, returning to the start when it ends'),
               ('YOYO_ONCE', "Yoyo One-shot", 'Animation plays once forwards, once backwards, then stops on the first frame'),
               ('YOYO_LOOP', "Yoyo Loop", 'Animation bounces between playing forward and playing backward')
              ),
        default='ONESHOT'
    )
    bpy.utils.register_class(ACTION_UL_animentry)
    bpy.utils.register_class(AnimationPropertyPanel)
    
    bpy.types.TOPBAR_MT_file_import.append(import_menu_func)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(import_menu_func)
    
    bpy.utils.unregister_class(AnimationPropertyPanel)
    bpy.utils.unregister_class(ACTION_UL_animentry)
    del bpy.types.Action.bck_loop_type
    del bpy.types.Object.active_action_index
    
    bpy.utils.unregister_class(BMD_PT_import_debug)
    bpy.utils.unregister_class(BMD_PT_import_texture)
    bpy.utils.unregister_class(BMD_PT_import_animation)
    bpy.utils.unregister_class(BMD_PT_import_armature)
    bpy.utils.unregister_class(BMD_PT_import_options)
    bpy.utils.unregister_class(ImportBmd)



if __name__ == "__main__":
    register()
    if IDE_DEBUG:
        bpy.ops.blemd.importer()
