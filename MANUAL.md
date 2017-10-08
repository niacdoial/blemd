**how do I extract the model from disk, exactly?**

First, you will need a file that contains the entire game
(you can do it by using this method (http://wiibrew.org/wiki/CleanRip) if you have a Wii and bought a game: it is THE ONLY LEGAL METHOD)

Then, extract it and put the result into a folder Dolphin emulator at dolphin-emu.org does the job just fine,
but you'll need the 2015 64-bit version of Visual c++ redistributable microsoft libraries (https://www.microsoft.com/en-us/download/details.aspx?id=48145)
if you don't want to have to install it using admin rights.

Afterwards, extract the `.arc/.rarc` archives with this: http://www.amnoid.de/gc/szstools.zip (a full program with docs there!)
to run it, you will need the 32 bit system  Microsoft Visual C++ 2005 Redistributable Package (x86).  (http://go.microsoft.com/fwlink/?linkid=65127)
don't panic, most PCs have it.

Then, grab blender and unzip the contents of this repository in `"<path to blender>/2.XX/scripts/addons_contrib/blemd"`
(please note that while another path may also work, `"blemd"` MUST be the name of the last folder, which the one containing all the '.py' files
from there, you will be able to enable it  in the add-ons tab of the settings (it is in the "testing" category yet).
Note that this step in only required the first use of this add-on, and that the use of the "save settings" is needed for the add-on to be enabled in future blender sessions

You can then import the `.bmd` files by using `file->import->nintendo BMD`, and do what you want with it!

**about animations**

the first thing you need to know is that animations are in *separate files* (`.bck` usually)
therefor, this program will only detect them if directory structure of the original `.arc` archives is kept
*animations can be excluded from import* if you move them or change the file extention.
