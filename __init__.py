#!/usr/bin/env python3

bl_info = {
    "name": "Import gc/wii bmd format (.bmd, .bdl)",
    "author": "people from the internet. adapted for blender by Niacdoial, from Avatarus-One's version (see github) full explanation in README",
    "version": (1, 1, 0),
    "blender": (2, 83, 0),
    "location": "File > Import > Nintendo BMD",
    "description": "Import files in the gc/wii BMD format (.bmd, .bdl)",
    "wiki_url": "https://github.com/niacdoial/blemd",
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
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, PointerProperty
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
    reload(BModel_out)
    reload(Bck)
    reload(common)
    #log_out = log.handlers[1].stream  # kinda hacky, but it works (?)
else:
    if not logging.root.handlers:
        # if this list is not empty, logging is configured.
        # here, it isn't
        config_logging()
    from . import common, BModel, BModel_out, Bck
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
            temp.Import(filepath=self.filepath, **{x: getattr(self, x) for x in self.ALL_PARAMS})
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


def validate_obj_for_anim_export(obj):
    # Validate object
    if obj is None:
        print("Object was None!")
        return False

    obj_anim_data = obj.animation_data

    # Validate animation data
    if obj_anim_data is None:
        print("No anim data!")
        return False
    if len(obj_anim_data.nla_tracks) == 0:
        print("No NLA tracks!")
        return False
    if len(obj_anim_data.nla_tracks[0].strips) == 0:
        print("No NLA strips!")
        return False

    print("valid!")
    return True


def arma_items(self, context):
    obs = []
    for ob in context.scene.objects:
        print(ob.name)
        if validate_obj_for_anim_export(ob):
            obs.append((ob.name, ob.name, ""))

    if len(obs) == 0:
        return [("NONE", "None", "")]

    return obs

def arma_upd(self, context):
    self.anim_export_armatures_collection.clear()

    for ob in context.scene.objects:
        if validate_obj_for_anim_export(ob):
            item = self.anim_export_armatures_collection.add()
            item.name = ob.name

    return None

def action_items(self, context):
    if self.anim_export_armatures == "NONE":
        return [("NONE", "None", "")]

    sce = context.scene

    cur_armature = sce.objects.get(self.anim_export_armatures)
    if cur_armature is None:
        return [("NONE", "None", "")]

    return [(action.name, action.name, "") for action in cur_armature.animation_data.nla_tracks[0].strips]


class ExportBmd(Operator, ExportHelper):
    """Exports the given object to Nintendo's *.BMD format"""
    bl_idname = "export_object.bmd"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export BMD/BDL"

    # ExportHelper mixin class uses this
    filename_ext = ".bmd"

    filter_glob: StringProperty(
        default="*.bmd",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
    export_format: EnumProperty(

        name="Format",
        description="Choose whether to export a BMD or BDL",
        items=(('BMD', "BMD", 'Export a BMD; used in e.g. Super Mario Sunshine, Twilight Princess'),
               ('BDL', "BDL", 'Export a BDL; used in e.g. The Wind Waker, Super Mario Galaxy')),
        default='BMD'
    )
    use_selection: BoolProperty(

        name='Selected Objects',
        description='Export selected objects only',
        default=False
    )

    use_visible: BoolProperty(
        name='Visible Objects',
        description='Export visible objects only',
        default=False
    )

    use_active_scene: BoolProperty(
        name='Active Scene',
        description='Export active scene only',
        default=False
    )
    export_normals: BoolProperty(

        name='Normals',
        description='Export vertex normals with meshes',
        default=True
    )
    export_colors: BoolProperty(

        name='Vertex Colors',
        description='Export vertex colors with meshes',
        default=True
    )
    export_texcoords: BoolProperty(

        name='UVs',
        description='Export UVs (texture coordinates) with meshes',
        default=True
    )
    export_position_compression_enable: BoolProperty(

        name='Position attribute compression',
        description='Compress vertex position data',
        default=False
    )
    export_normal_compression_enable: BoolProperty(

        name='Normal attribute compression',
        description='Compress vertex normal data',
        default=True
    )
    export_texcoord_compression_enable: BoolProperty(

        name='Tex coord attribute compression',
        description='Compress vertex tex coord data',
        default=True
    )

    def execute(self, context):
        global log_out
        retcode = 'FINISHED'

        model_out = BModel_out()
        model_out.export(is_bdl=False)

        return {retcode}

    def draw(self, context):
        pass


class BMD_PT_export_options_main(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = ""
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_OBJECT_OT_bmd"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator
        sce = context.scene

        layout.prop(operator, 'export_format')
        layout.separator()


class BMD_PT_export_options_include(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_OBJECT_OT_bmd"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        col = layout.column(heading = "Limit to", align = True)
        col.prop(operator, 'use_selection')
        col.prop(operator, 'use_visible')
        col.prop(operator, 'use_active_scene')


class BMD_PT_export_options_geometry_compression(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Compression"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_OBJECT_OT_bmd"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        col = layout.column(heading="Compress", align=True)
        col.prop(operator, 'export_position_compression_enable', text="Position")
        col.prop(operator, 'export_normal_compression_enable', text="Normals")
        col.prop(operator, 'export_texcoord_compression_enable', text="UVs")


class ExportBck(Operator, ExportHelper):
    """Exports the given action(s) as Nintendo's *.BCK format"""
    bl_idname = "export_object.bck"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export BCK"

    # ExportHelper mixin class uses this
    filename_ext = ".bck"

    filter_glob: StringProperty(
        default="*.bck",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
    export_anims_mode: EnumProperty(

        name="Export Mode",
        description="Choose whether to export a single animation or multiple",
        items=(('SINGLE', "Single", 'Export a single selected animation'),
               ('BULK', "Bulk", 'Export multiple animations'),
               ),
        default='SINGLE'
    )

    # Options for exporting multiple anims at once
    use_selection: BoolProperty(
        name="Selected armature only",
        description="Export animations from ONLY the selected armature",
        default=True
    )

    def execute(self, context):
        global log_out
        retcode = 'FINISHED'

        out_action = bpy.data.actions.get(context.scene.anim_export_actions)
        anim_armature = bpy.data.objects.get(context.scene.anim_export_armatures)

        ex_bck = Bck.Bck_out()
        ex_bck.dump_action(out_action, anim_armature.pose)

        ex_bck.dump_bck(self.filepath)

        return {retcode}

    def draw(self, context):
        pass


class ACTION_UL_animentry(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        else:
            layout.label(text="", translate=False, icon_value=icon)


class BCK_PT_export_options(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = ""
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_OBJECT_OT_bck"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator
        sce = context.scene

        layout.prop(operator, 'export_anims_mode')
        layout.separator()

        arm_row = layout.row()
        arm_row.enabled = sce.anim_export_armatures != "NONE"
        arm_row.prop(sce, "anim_export_armatures")

        act_row = layout.row()
        act_row.enabled = operator.export_anims_mode == 'SINGLE' and arm_row.enabled
        act_row.prop(sce, "anim_export_actions")


class CreateAnimationOperator(bpy.types.Operator):          
    """Set up a new animation for export"""
    bl_idname = "object.anim_create_operator"
    bl_label = "Create BCK Animation"

    def execute(self, context):
        obj = context.object

        if obj.animation_data is None:
            obj.animation_data_create()

        if len(obj.animation_data.nla_tracks) == 0:
            obj.animation_data.nla_tracks.new()

        if len(obj.animation_data.nla_tracks[0].strips) == 0:
            start_frame = 1
        else:
            start_frame = int(obj.animation_data.nla_tracks[0].strips[-1].frame_end + 5)

        obj.animation_data.nla_tracks[0].strips.new('new_bck_anim', start_frame, bpy.data.actions.new('new_bck_anim'))

        return {'FINISHED'}


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

        if obj.animation_data is not None and len(obj.animation_data.nla_tracks) != 0 and len(obj.animation_data.nla_tracks[0].strips) != 0:
            # This is the list of strips that are currently part of the selected object's first NLA track.
            layout.template_list("ACTION_UL_animentry", "", obj.animation_data.nla_tracks[0], "strips", obj, "active_action_index")

            layout.row().prop(obj.animation_data.nla_tracks[0].strips[obj.active_action_index], "name")
            layout.row().prop(obj.animation_data.nla_tracks[0].strips[obj.active_action_index].action, "bck_loop_type")

            layout.row().separator()

        layout.row().operator(CreateAnimationOperator.bl_idname, text="Create Animation", icon="FILE_NEW")


class TOPBAR_MT_file_export_nintendo(bpy.types.Menu):
    bl_label = "Nintendo J3D (GameCube/Wii)"

    def draw(self, context):
        #self.layout.operator(ExportBmd.bl_idname, text="Model (*.bmd, *.bdl)")
        #self.layout.separator()
        self.layout.operator(ExportBck.bl_idname, text="Joint Animation (*.bck)")
        #self.layout.operator(ExportBca.bl_idname, text="Joint Animation (*.bca)") # TODO

    def menu_draw(self, context):
        self.layout.menu("TOPBAR_MT_file_export_nintendo")


# Only needed if you want to add into a dynamic menu
def import_menu_func(self, context):
    self.layout.operator(ImportBmd.bl_idname, text="Nintendo BMD/BDL")


def export_menu_func(self, context):
    self.layout.operator(ExportBck.bl_idname, text="Nintendo BCK (keyframe animation)")


def register():
    bpy.utils.register_class(ImportBmd)
    bpy.utils.register_class(BMD_PT_import_options)
    bpy.utils.register_class(BMD_PT_import_armature)
    bpy.utils.register_class(BMD_PT_import_animation)
    bpy.utils.register_class(BMD_PT_import_texture)
    bpy.utils.register_class(BMD_PT_import_debug)

    bpy.utils.register_class(ExportBmd)
    bpy.utils.register_class(BMD_PT_export_options_main)
    bpy.utils.register_class(BMD_PT_export_options_include)
    bpy.utils.register_class(BMD_PT_export_options_geometry_compression)
    bpy.utils.register_class(ExportBck)
    bpy.utils.register_class(BCK_PT_export_options)

    bpy.types.Scene.anim_export_armatures = bpy.props.EnumProperty(
        name="Armatures",
        items=arma_items,
        update=arma_upd
    )
    bpy.types.Scene.anim_export_actions = bpy.props.EnumProperty(
        name="Actions",
        items=action_items,
    )
    bpy.types.Scene.anim_export_armatures_collection = bpy.props.CollectionProperty(
        type=bpy.types.PropertyGroup
    )

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
    
    bpy.utils.register_class(TOPBAR_MT_file_export_nintendo)
    
    bpy.types.TOPBAR_MT_file_import.append(import_menu_func)
    bpy.types.TOPBAR_MT_file_export.append(TOPBAR_MT_file_export_nintendo.menu_draw)
    
    bpy.utils.register_class(CreateAnimationOperator)


def unregister():
    bpy.utils.unregister_class(CreateAnimationOperator)
    
    bpy.utils.unregister_class(TOPBAR_MT_file_export_nintendo)
    
    bpy.types.TOPBAR_MT_file_export.remove(TOPBAR_MT_file_export_nintendo.menu_draw)
    bpy.types.TOPBAR_MT_file_import.remove(import_menu_func)
    
    bpy.utils.unregister_class(AnimationPropertyPanel)
    bpy.utils.unregister_class(ACTION_UL_animentry)
    del bpy.types.Action.bck_loop_type
    del bpy.types.Object.active_action_index

    del bpy.types.Scene.anim_export_armatures
    del bpy.types.Scene.anim_export_actions
    del bpy.types.Scene.anim_export_armatures_collection

    bpy.utils.unregister_class(BCK_PT_export_options)
    bpy.utils.unregister_class(ExportBck)
    bpy.utils.unregister_class(BMD_PT_export_options_geometry_compression)
    bpy.utils.unregister_class(BMD_PT_export_options_include)
    bpy.utils.unregister_class(BMD_PT_export_options_main)
    bpy.utils.unregister_class(ExportBmd)

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
