This subfolder contains what is necessary to rebuild the image extracting executable,
as well as old versions of it (in case the one in the main folder breaks)

The source code can be edited and re-compiled, there is no dependencies.
To be reached by the main part fo the add-on, it must be renamed "bmdview.exe" and put in the main folder, overwriting the default executable.

Caution: this means the add-on *only works on windows* for now.

To adapt it for other platforms, you will need to recompile the executable, but you will need to edit the main folder's "maxheader.py"
The function to edit is labeled as such.