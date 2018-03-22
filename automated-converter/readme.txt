This subfolder contains tools to make automated conversion jobs:
by default, it will use BleMD to import "path\file.bmd" and export to "path\file.fbx",
"fbx" being a format that is recognizable by most 3D softwares

the contents of this subfolder are not needed for BleMD to run, and thus can be moved anywhere.
you will just want to set the paths correctly in the '.bat' file.

with a little blender knowledge, you will be able to modify the exporting line in IOmanager.py
to use it to export in any format known by blender

In order for it to work, you still have to install the main add-on (put it where blender can reach it)
