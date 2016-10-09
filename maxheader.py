import bpy
import os
import re
from time import sleep
import subprocess
import sys

IDE = True

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
    subprocess.check_output(cmd)


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
        if re.match(rematcher, os.path.join(path.replace('/', '\\'), com)):
            returnable.append(os.path.join(path, com))
    return returnable

if __name__ == '__main__':
    while 1:
        exec(input('>>> '))