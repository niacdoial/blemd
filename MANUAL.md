<h4>How to use BleMD?</h4>
summary:
- How to install?
- How to obtain a `.bmd` file from a game (with the use of other tools)?
- How are the the animations handled?
- How are the imaged handled?
- Settings and misc. troubleshooting



**how to install?**

To install BleMD, you first need to have blender itself installed (from blender.org).
I recommend version 2.77 or better, but there is *no* support for version 2.80 for now.

Once blender is installed (or at least unzipped), you will need to put the contents of BleMD in the correct place yourself.

For this, download the contents of the repository in a zip file, and put the folder inside it into one of the following paths:
- `"<path to blender>/2.XX/scripts/addons_contrib/"`
- `"<path to blender>/2.XX/scripts/addons/"`
- `"C:/Users/<name>/AppData/Roaming/Blender Foundation/blender/2.XX/scripts/addons_contrib/"`
- `"C:/Users/<name>/AppData/Roaming/Blender Foundation/blender/2.XX/scripts/addons/"`

(note : you might need to run blender to access those two last paths.)

Then, ensure that the folder you just moved, containing the addon (which might be called `blemd-master`),
**must** be called `"blemd"`.

From there, you will be able to enable it in the add-ons tab of the settings (`file->user settings->addons`).
For now to enable it, you need to first find it (click on the `testing` category, and scroll down to find it),
then enable it using the checkbox to the right of the tile representing the addon.

Finally, click on `save user settings` for the addon to be loaded in future blender utilisations.



**How to obtain a `.bmd` file from a game (with the use of other tools)?**

First, you will need a file that contains the entire game
(you can do it by using this method (http://wiibrew.org/wiki/CleanRip) if you have a Wii and bought a game: it is
*the only legal method, to my knowledge*)

Then, extract the contents of the game and put the result into a folder.
Dolphin emulator (at dolphin-emu.org) does the job just fine, but you have to find this option first.
If you are not your PC's admin, you will need to already have the 2015 64-bit version of
Visual c++ redistributable microsoft libraries (https://www.microsoft.com/en-us/download/details.aspx?id=48145)
(most recent (2015+) PCs have it)

Afterwards, extract the `.arc/.rarc` archives (at `/res/Object` in the game folder) with this: http://www.amnoid.de/gc/szstools.zip (a full program with docs there!)
to run it, you will need the 32 bit Microsoft Visual C++ 2005 Redistributable Package (x86).  (http://go.microsoft.com/fwlink/?linkid=65127)
don't panic, quite a lot of PCs have it.

Then, with blender on your PC, and BleMD 'installed', you have two methods:
- You can open blender, and use `file->import->nintendo BMD`. Then select the correct file with the file explorer 
and, if you want to, change the options in the bottom-left corner.
- Otherwise, you can use the automated-converter. More instructions are given in the corresponding subfolder.



**How are the the animations handled**

The first thing you need to know is that animations are *not stored in the `.bmd` file,
and there might be multiple animation files.* (`.bck` usually).

Therefor, this program will only detect them if directory structure of the original `.arc` archives is respected:

```
-Main_folder/
 |-bmd/
 | |-foo.bmd
 | |-bar.bmd
 | |...
 |
 |-bck/
 | |-animation.bck
 | |-another animation.bck
```
(while `main_folder/`, `bmd/` and the files can have any name, the `bck/` folder must be named "bck", "bcks" or "scrn")

*animations can be excluded from import* if you move them from this spot or change the file extention.



**How are the imaged handled?**
Unlike everything else in the `bmd` file, images first have to be written elsewhere to be used, and this is done by
a small program, included with the BleMD "core". However, this small program is an exe file, meaning that it only works on windows.

the `image importing subprocess` subfolder contains a couple versions of this file (V1 and V2 are older and might be broken),
plus the source code, so the program can be recompiled for other platforms.
To change the used executable, you will need to replace the one in the main folder (called `bmdview.exe`).

Moreover, this small program is not aware of what exact image formats (such as dds:I8 or tga:palette8:rgba8) blender can use,
but offers you the possibility to use `.tga` or `.dds` as an image container:
switching from one to the other help fix some problems.



**Misc. troubleshooting**

There are two logging systems put in place:
- one will only record warnings and errors, and will show up as a pop-up when the plugin finishes.
- the other is much more verbose, and wil show up on the system console.

Please include a screenshot of the console (and the blender viewport if necessary) when reporting any kind of error.