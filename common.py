"""
A common function module for BleMD.
Mostly used by BModel, but can be expanded further

"""

import bpy
import os
import re
from time import sleep
import subprocess
import sys
from contextlib import contextmanager
import logging

log = logging.getLogger('bpy.ops.import_mesh.bmd.maxH')

IDE = False  # is changed by test launcher

if sys.platform[:3].lower()=='win':
    SEP = '\\'
elif sys.platform=='linux':
    SEP = '/'
else:
    log.error('Your platform (%s) is not supported. images will not be imported')
    SEP = '/'  # a decent default

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
        rev.append(inputArray[i-1])  # corrected!
        i -= 1
    # -- inputArray = rev doesn't work
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
        exefile = os.path.abspath(startpath + exefile)

    # if ' ' in exefile:  # whitespace: quotes needed
    #    exefile = '"' + exefile + '"'

    # args = ['"' + com + '"' for com in args]
    # do not change original data, and add quotes on args
    temp = subprocess.run([exefile] + args, shell=False)
    if temp.stdout:
        log.info ("process output:\n %s", temp.stdout)
    if temp.stderr:
        log.error('process errors:\n %s', temp.stderr)


def getFilenamePath(path):
    return os.path.split(path)[0] + os.path.sep


def newfile(name):
    if not getFiles(name):  # if it doesn't exist
        open(name, 'ab').close()  # create file


def getFilenameFile(path):
    dir, file = os.path.split(path)
    file = os.path.splitext(file)[0]
    return file
    # return os.path.join(dir, file)

# XCX use glob instead
def getFiles(wc_name):
    # assume wild card is in the last part
    path, file = os.path.split(wc_name)
    returnable = []
    if '*' in path:
        raise ValueError('must implement getFiles better')
    try:
        a, dirs, files = next(os.walk(os.path.normpath(path)))
    except StopIteration:
        return returnable
    for com in files:
        if os.path.sep == '/':
            wc_name = wc_name.replace('\\', '/')
        else:
            wc_name = wc_name.replace('/', '\\').replace('\\', r'\\')
            path = path.replace('/', '\\')
        rematcher = wc_name.replace('.', r'\.').\
                            replace('*', '.*').\
                            replace('(', r'\(').\
                            replace(')', r'\)')
        if re.fullmatch(rematcher, path+ os.path.sep + com):
            returnable.append(os.path.join(path, com))
    return returnable

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
    def __init__(self, filename, boneThickness, mir_tx, frc_cr_bn, sv_anim,
                 tx_pck, ic_sc, imtype, dvg=False, nat_bn=False, use_nodes=False, val_msh=False, paranoia=False, no_rot_cv=False):
        self.filename = filename
        self.boneThickness = boneThickness
        self.allowTextureMirror = mir_tx
        self.forceCreateBones = frc_cr_bn
        self.loadAnimations = sv_anim != 'DONT' and not nat_bn
        self.animationType = sv_anim if self.loadAnimations else 'DONT'
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
