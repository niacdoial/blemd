import bpy
import os
import re
from time import sleep
import subprocess
import sys
from contextlib import contextmanager


IDE = True


@contextmanager
def stdout_redirected(to=os.devnull):
    '''
    import os

    with stdout_redirected(to=filename):
        print("from Python")
        os.system("echo non-Python applications are also supported")
    '''
    fd = sys.stdout.fileno()

    ##### assert that Python and C stdio write using the same file descriptor
    ####assert libc.fileno(ctypes.c_void_p.in_dll(libc, "stdout")) == fd == 1

    def _redirect_stdout(to):
        sys.stdout.close() # + implicit flush()
        os.dup2(to.fileno(), fd) # fd writes to 'to' file
        sys.stdout = os.fdopen(fd, 'w') # Python writes to fd

    with os.fdopen(os.dup(fd), 'w') as old_stdout:
        with open(to, 'w') as file:
            _redirect_stdout(to=file)
        try:
            yield  # allow code to be run with the redirected stdout
        finally:
            _redirect_stdout(to=old_stdout)  # restore stdout.
                                             # buffering and flags such as
                                             # CLOEXEC may be different


def MessageBox(string):
    if IDE:
        print(string, file=sys.stderr, end='')
        input()
        return
    drawer = (lambda obj, context : obj.layout.label(string))
    bpy.context.window_manager.popup_menu(drawer, 'message box', icon='ERROR')
    sleep(5)


def HiddenDOSCommand(cmd, startpath=os.getcwd()):
    if os.path.isabs(cmd):
        DosCommand(cmd)
    else:
        DosCommand(startpath+cmd)


def DosCommand(cmd):
    if not os.path.isabs(cmd):
        cmd = os.path.abspath(cmd)
    print(subprocess.check_output(cmd,stderr=subprocess.STDOUT))


def getFilenamePath(path):
    return os.path.split(path)[0] + os.path.sep


def getFilenameFile(path):
    dir, file = os.path.split(path)
    file = os.path.splitext(file)[0]
    return file
    # return os.path.join(dir, file)


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
        rematcher = wc_name.replace('/', '\\').replace('\\', '\\\\').\
                            replace('.', '\\.').\
                            replace('*', '.*').\
                            replace('(', '\\(').\
                            replace(')', '\\)')
        if re.match(rematcher, path.replace('/', '\\')+ '\\' + com):
            returnable.append(os.path.join(path, com))
    return returnable