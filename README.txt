welcome to BleMD.
this project was for goal to import nintendo GC/Wii ".bmd" 3D models,
using blender (blender.org)
HOW TO USE:
first, get a game iso (dumping a baught game is THE legal way to proceed: you can use this https://code.google.com/archive/p/cleanrip/downloads to do it(you will need an actual Wii))
then, extract it in a proper directory (dolphin emulator at dolphin-emu.org does the job just fine,
but you'll need the 2015 64-bit version of Visual c++ redistribuable microsoft libraries (https://www.microsoft.com/en-us/download/details.aspx?id=48145)
if you don't want to have to install it using admin rights.
afterwards, extract the .arc/.rarc archives with this: http://www.amnoid.de/gc/szstools.zip (a full program with docs there!)

you will also need the 32 bit system  Microsoft Visual C++ 2005 Redistributable Package (x86).  (http://go.microsoft.com/fwlink/?linkid=65127)
then, grab blender and unzip it in "<path to blender>/2.XX/scripts/addons_contrib/blemd"
from there, you will be able to enable it  in the add-ons tab of the settings(it is in the "testing" category),
and use it in file->import->nintendo BMD


HISTORY:
His history is long, and incredibly hard to trace.

It started with BMD Vewer and BMDview2, from YAZ0(just where is this guy-s home page?), in C++

it has a copy on the google code server (http://code.google.com/p/bmdview2/)

Originally it came from this discussion thread:
http://www.emutalk.net/threads/54262-BMDView2-Linux?p=447701
And that had this download link:
http://dl.dropbox.com/u/21757902/bmdview2.tar.gz
An older Readme.txt file that was found from a file BMDview2.rar said:
"""
latest version of BMD View 2 at
http://emutalk.net/showthread.php?t=26919&page=18
[...]
The official emutalk thread for this program can be found at
http://www.emutalk.net/showthread.php?t=26062 (part 1), and at
http://emutalk.net/showthread.php?t=26919 (part 2).
"""
Oh, and it is here too (http://www.vg-resource.com/thread-21121.html) too.

then, because the exportation really lost data, there was MaxBMD, a MaxScript varient that used 3dsMax from Autodesk.
It was based on bmdview2pre3 by thakis (homepage at http://amnoid.de/gc/ download source at http://www.emutalk.net/showthread.php?t=26919&page=39)
it still had a lot of bugs, and a HELL lot of different branches. Plus this software is eefing expensive. And it was really uneasy to debug.
the discution is here: http://www.emutalk.net/threads/44490

It was then adapted by Niacdoial (me) from Avatarud-One's version on Github(https://github.com/Avatarus-one/MaxBMD/)
and a bit of the latest BMDView2 program
to use blender instead (plus, it is a python plug-in, so that language is far easyer to debug)

Did I ever mentionned that it is totally admin-free?


people from the internet. adapted for blender by Niacdoial, from Avatarus-One's version (see github) full explanation in README
