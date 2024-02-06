"""
A common function module for BleMD.
Mostly used by BModel, but can be expanded further
"""

import bpy
import os, sys, re, glob
from time import sleep
import subprocess
from contextlib import contextmanager
import logging

log = logging.getLogger('bpy.ops.import_mesh.bmd.maxH')

IDE = False  # is changed by test launcher

if not (sys.platform[:3].lower()=='win' or sys.platform[:3].lower()=='lin'):
    log.error('Your platform (%s) is not supported. images will not be imported', sys.platform[:3].lower())

@contextmanager
def stdout_redirected(to=os.devnull):
    '''
    # curtesy of https://stackoverflow.com/questions/4675728/redirect-stdout-to-a-file-in-python#4675744
    import os

    with stdout_redirected(to=filename):
        print("from Python")
        os.system("echo non-Python applications are also supported")
    '''
    fd = sys.stdout.fileno()

    ##### assert that Python and C stdio write using the same file descriptor
    ####assert libc.fileno(ctypes.c_void_p.in_dll(libc, "stdout")) == fd == 1

    def _redirect_stdout(to):
        sys.stdout.close()  # + implicit flush()
        os.dup2(to.fileno(), fd)  # fd writes to 'to' file
        sys.stdout = os.fdopen(fd, 'w')  # Python writes to fd

    with os.fdopen(os.dup(fd), 'w') as old_stdout:
        with open(to, 'w') as file:
            _redirect_stdout(to=file)
        try:
            yield  # allow code to be run with the redirected stdout
        finally:
            _redirect_stdout(to=old_stdout)  # restore stdout.
                                             # buffering and flags such as
                                             # CLOEXEC may be different


@contextmanager
def active_object(obj):
    act_bk = bpy.context.scene.objects.active
    bpy.context.scene.objects.active = obj
    try:
        yield  # run some code
    finally:
        bpy.context.scene.objects.active = act_bk


def MessageBox(string):
    log.warning(string)
    if IDE:
        input('press any key to continue')
        return
    #drawer = (lambda obj, context: obj.layout.label(string))
    #bpy.context.window_manager.popup_menu(drawer, 'message box', icon='ERROR')
    #sleep(5)


def ReverseArray(inputArray):
    i = 0
    rev = []
    i = len(inputArray)
    while i > 0:
        rev.append(inputArray[i-1])
        i -= 1
    return rev


def dict_get_set(dct, key, default):
    if key not in dct.keys():
        dct[key] = default
    return dct[key]


def SubProcCall(exefile, args, startpath=os.getcwd()):
    # this is the function to edit to adapt the program for non-windows platforms
    # just add an 'elif' to the  if/else block below, in which `exefile` is adapted
    # (from 'path/to/bmdview' to 'path/to/bmdview.exe' in this example)

    if sys.platform[:3].lower() == "win":  # windows: use EXE
        exefile += '.exe'

    elif sys.platform == 'linux':
        exefile += '.lin'
    else:
        raise RuntimeError('For now, image extraction does not support your platform')

    if not os.path.isabs(exefile):
        exefile = os.path.abspath(os.path.join(startpath, exefile))

    # if ' ' in exefile:  # whitespace: quotes needed
    #    exefile = '"' + exefile + '"'

    # args = ['"' + com + '"' for com in args]
    # do not change original data, and add quotes on args
    temp = subprocess.run([exefile] + args, shell=False)
    if temp.stdout:
        log.info ("process output:\n %s", temp.stdout)
    if temp.stderr:
        log.error('process errors:\n %s', temp.stderr)



def newfile(name):
    if not os.exists(name):  # if it doesn't exist
        open(name, 'ab').close()  # create file


def getFilenameFile(path):
    dir, file = os.path.split(path)
    file = os.path.splitext(file)[0]
    return file
    # return os.path.join(dir, file)


def getFiles(*pathparts, basedir=""):
    """get the path of files matching a known globbing pattern, starting with a known base directory"""
    basedir = glob.escape(basedir)
    return glob.glob(os.path.join(basedir, *pathparts))

def dedup_lines(string):
    lines = {}  # dict: {line: count}

    for line in string.split('\n'):
        line = line + ' (x{:d})\n'
        lines[line] = dict_get_set(lines, line, 0) + 1

    dest=""
    for line in lines.keys():
        dest += line.format(lines[line])

    return dest


class Prog_params:
    def __init__(self, filename, boneThickness, frc_cr_bn, import_anims, import_anims_type,
                 tx_pck, ic_sc, imtype, dvg=False, nat_bn=False, use_nodes=False, val_msh=False, paranoia=False, no_rot_cv=False):
        self.filename = filename
        self.boneThickness = boneThickness
        self.forceCreateBones = frc_cr_bn
        self.loadAnimations = import_anims and not nat_bn
        self.animationType = import_anims_type
        self.naturalBones = nat_bn
        self.packTextures = tx_pck
        self.includeScaling = ic_sc
        self.imtype = imtype
        self.DEBUGVG = dvg
        self.PARANOID = paranoia
        self.use_nodes = use_nodes
        self.validate_mesh = val_msh
        self.no_rot_conversion = no_rot_cv
        # secondary parameters (computed later on)
        self.createBones = True

GLOBALS = None  # will hold a Prog_params instance
