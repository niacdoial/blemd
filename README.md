# Welcome to BleMD.
This project goal is to import Nintendo Gamecube/Wii ".bmd" and ".bdl" 3D models,
using [Blender](https://blender.org).


## project structure, and advice for anyone willing to tinker with the code: see dev_notes.md

## HISTORY: *moved to HISTORY.md*

# FAQ:

### Help, BleMD freezes when I import a file

First, make sure you are trying to import a file from a gamecube/wii game.
There are other kinds of `.bmd`/`.bdl` files, but those other files cannot be imported by BleMD
in particular, *BleMD cannot import files from minecraft mods such as pixelmon* (…mentioning this here because it's the only other file encountered in this project's issues)

Then, know that importing a lot of animations (which is done by default) is really slow. You can disable this in the options that show up in the import dialog, and it should be faster. If it still takes more than 5min (for very large models on ancient hardware), then you can try and contact us.

# How to use BleMD?
summary:
- How to install?
- How to obtain a `.bmd` file from a game (with the use of other tools)?
- How are the the animations handled?
- How are the imaged handled?
- Misc. troubleshooting.

## how to install?

To install BleMD, you first need to have Blender itself installed. (It is recommended to install from [The official site](https://blender.org or your [Package manager](https://en.wikipedia.org/wiki/Package_manager)).
The version of BleMD distributed with this manual works for Blender versions from 2.8 onwards, and was tested with 2.83, 3.0.1 and 3.1.0.

Once blender is installed (or at least unzipped), you will need to put the contents of BleMD in the correct place yourself.

For this, download the contents of the repository in a zip file, and put the folder inside it into one of the following paths:
- `"<path to blender>/<version>/scripts/addons_contrib/"`
- `"<path to blender>/<version>/scripts/addons/"`
- `~/.config/blender/<version>/scripts/addons_contrib/"` (GNU/Linux)
- `~/.config/blender/<version>/scripts/addons/"` (GNU/Linux)
- `"C:/Users/<username>/AppData/Roaming/Blender Foundation/blender/<version>/scripts/addons_contrib/"` (Windows)
- `"C:/Users/<username>/AppData/Roaming/Blender Foundation/blender/<version>/scripts/addons/"` (Windows)

(Notes: you might need to run Blender at least once to create some of theses paths, and the `<version>` might be truncated: for example `3.0` for blender 3.0.1.)

Then, ensure that the folder you just moved, containing the addon (which might be called `blemd-master`),
**must** be called `"blemd"`.

From there, you will be able to enable it in the add-ons tab of the settings (`file->user settings->addons`).
For now to enable it, you need to first find it (click on the `testing` category, and scroll down to find it),
then enable it using the checkbox to the right of the tile representing the addon.

## How to obtain a `.bmd` file from a game (with the use of other tools)?

First, you will need a file that contains the entire game
(you can do it by using this method (http://wiibrew.org/wiki/CleanRip) if you have a Wii or Gamecube and bought a game:
*to my knowledge, it is the only legal method, if/where it even is.*)

Then, extract the contents of the game and put the result into a folder.
Dolphin emulator (at https://dolphin-emu.org) does the job just fine, but you have to find the procedure to do it.
Note: If you are not your PC's admin and your PC's OS is Windows, you will need to already have the 2015-2019 64-bit version of
[Microsoft Visual C++ redistributable libraries](https://www.microsoft.com/en-us/download/details.aspx?id=48145)
(most recent PCs have it)

Afterwards, extract the `.arc/.rarc/.szs` archives (at `/res/Object`, `/data` or `/ObjectData` in the game folder) with [SZS Tools](http://www.amnoid.de/gc/szstools.zip) (Full program with docs there!) or [Switch Toolbox](https://github.com/KillzXGaming/Switch-Toolbox)
to run SZS Tools, you will need the 32 [bit Microsoft Visual C++ 2005 Redistributable Package (x86)](http://go.microsoft.com/fwlink/?linkid=65127). 
Don't panic, quite a lot of PCs have it.
If you're not using Windows, use [this](https://github.com/tpwrules/ARCTool) instead: 
to run it, you will need the [Python 2](https://www.python.org/downloads/release/python-278/).
```bash
# Extract .arc/.rarc
python2 ARCTool.py <.arc/.rarc> [-o OutputDirectoryName]
# If you didn't specify output name, it will extract to <original.(r)arc>.extracted/
```

Then, with blender on your PC, and BleMD 'installed', you have two methods:
- You can open Blender, and use `File->Import->Nintendo BMD/BDL`. Then select the correct file with the file explorer
and, if you want to, change the options in the right pane.
- Otherwise, you can use `automated-converter`. More instructions are given in the corresponding subfolder.

## How are the the animations handled?

The first thing you need to know is that animations are *not stored in the* `.bmd` *file,
and there might be multiple animation files.* (`.bck` usually).

Therefor, this program will only detect them if directory structure of the original `.arc` archives is respected:

```
root/
 |bmd/
 | |foo.bmd
 | |bar.bmd
 | |...
 |
 |bck/
 | |animation.bck
 | |another animation.bck
 | |
```,

```
root/
 |bmd/
 | |foo.bmd
 | |bar.bmd
 | |...
 |
 |bcks/
 | |animation.bck
 | |another animation.bck
 | |
```
or
```
root/
 |foo.bmd
 |bar.bmd
 |animation.bck
 |another animation.bck
```
(While the `root/` abd `bmd/` folders and the files can have any name, the `bck/` folder must be named "bck", "bcks" or "scrn")

*Animations can be excluded from import* If you move them from this spot or change the file extention.

## How are the images handled?
Unlike everything else in the `bmd` file, images first have to be written elsewhere to be used, and this is done by
a small program, included with the BleMD "core". However, this small program is an native executable, making it hard to get working for Mac OS.

The `image importing subprocess` subfolder contains a couple versions of this file (V1 and V2 are older and might be broken),
plus the source code, so the program can be recompiled for other platforms.
To change the used executable, you will need to replace the one in the main folder (called `bmdview.exe` or `bmdview.lin`).

Moreover, this small program is not aware of what exact image formats (such as `dds file/8-bit greyscale` or `tga file/256 color palette/32bit rgb+alpha`) blender can use,
but offers you the possibility to use `.tga` or `.dds` as an image container:
switching from one to the other help fix some problems.



## Misc. troubleshooting.

There are two systems put in place to look at the program's logs:
- one will only record warnings and errors, and will show up as a pop-up when the plugin finishes.
- the other is much more verbose, and wil show up on the system console.

Please include a screenshot of the console (and the blender viewport if necessary) when reporting any kind of error.
