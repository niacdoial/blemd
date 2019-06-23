# Dev notes: how to maintain and improve BleMD:

For now, BleMD has only been developed by a single person, probably because of a fairly opaque structure and lack of commenting.

This document tries to change that: it will contain notes from any developer to anyone who would want to help (patching issues, adding functionalities, etc...)

It is separated into several sections, with one goal each.

## TODO:
this is a small list of the ongoing/wanted features. The list of the wanted bugfixes is already in the github issue system.

- **Porting to blender 2.8:** this is the big one, and already started with the porting of the materials to cycles in 2.7x
- **Full material and animation comprehension:** this is no surprise, but there is a few features currently missing, even on the GameCube version of the models. Comprehension of the Wii MDL3 section would also be welcome. Inspiration could be taken from [j3dview](https://github.com/RenolY2/j3dview) or other more developed projects (with credit of flipping course)
- **Wii U models:** this one is on low priority right now. Wii U models are a big step after their predecessors, and do not store their textures themselves, which requires either placeholders or the detection of the texture files (apparently it is a simple gzipped (xzipped?) archive)
- **turn BleMD into a full BMD I/O tool for blender:** for now, bmd files can only be read, not written. Changeing that is a (very) long-term goal.

- **Section versionning:** necessary for the two previous items: it is a complete restructure of the lower-level part of BleMD, in order to provide more elegant compatibility. Instead of a `Jnt1.py` file, for instance, there would be a `Jnt.py` file, which could import either `Jnt1` sections, `Jnt2` sections(if they exist), etc... and provide a common interface to the rest of the program. This interface would be modeled on the highest known version of the `Jnt` section
- **Better IO:** ideally, the IO model (BinaryReader and BinaryWriter) would be redesigned to make the lowel-level files shorter and more human-readable. Inspiration could be taken from [j3dview](https://github.com/RenolY2/j3dview)


## Structure:
This part is intended to help newcomers by explaining how the different parts of the program are organised.

### Lower level part:
- **BinaryReader.py, BinaryWriter.py:** handles 'raw' IO with the various files involved, and provide various methods to get specific low-level objects (ex GetByte, GetSHORT, GetDWORD, GetFloat, etc...). More descriptions in file
- **Drw1.py:** Handles reading/writing of a Drw section (version 1) through BinaryReader/BinaryWriter.
I don't completely understand this section, but it is a LUT (LookUpTable) for matrices, used for parts of the mesh that stretch over several bones.
- **Evp1:** The Evp section describes how the various vertices are tied to the various bones, especially in sections of the mesh that act as joints between several bones
- **Inf1:** the Inf section decomposes the mesh into a tree of sorts:
  each branch or leaf or this tree is either:
  - an information on what material should be applied to itself and its children (save for an override down the road),
  - what bone (the bmd standard calls them joints) should be applied (save for an override or an explicit reference to the Evp section),
  - a part of the mesh proper (a batch) See `Shp1` for details on batches
- **Jnt1:** Describes the bones (called joints) of the mesh, their position, rotation (and scale) relative to their parent bone. This position is the *rest position* of the bone. It is to be overridden by Bck animation info.
- **Mat3:** Handles the Mat section, versions 2 and 3. This section describes the various materials in the mesh.
- **Mdl3:** Used for the Wii, the Mdl section has to do with the materials, but I don't understand what it does at all. It is currently completely unused.
- **Shp1:** The Shp1 describes the various batches that make the mesh up. See the file itself for a description of what baches are made of.
- **Tex1:** The Tex1 section holds the textures and texture informations.
Due to severe performance issues, the textures are first exported into .tga or .dds files, by a small C++ program, that was compiled beforehand, and is called bmdview.exe or bmdview.lin depending on the platform (windows/linux)
- **Vtx1:** This section contains the vertices, normal vectors, UV coordinates, vertex colors, etc... referenced by the Shp section
- **bmdview.exe, bmdview.lin** executable files (binaries) to extract the images from the bmd file into tga or dds files. One is a windows executable, the other is a linux executable. the `image importing subprocess` folder contains its source and several older versions of the executables.

### Higher level part:
- **common:** this file contains some various utilities, some of them designed to emulate MaxScript functionalities used in the original MaxBMD code.
- **__init__:** This file handles the plugin's integration with Blender, as well as the GUI and options used to call BleMD proper.
- **Matrix44:** This contains various matrix manipulation utilities.
- **pseudobones:** This file contains a middle ground to handle bones (aka joints) between the BMD format and the internal blender format.
It also contains some bone animation components, that adapt the Bck animations into something blender can use.
- **texhelper:** some utilities to reference the textures correctly.
- **materialhelper:** contains some material creation functions
- **matpipeline:** this one performs the most of the material translations, from the `Mat` format to blender material node format. It also contains code to display the nodes nicely. It should also be able to output some arbitrary code that can be edited and re-outputed (but this is a more long-term goal).
- **BModel:** Contains the main parts of the code: it references everything else. It should probably be more fragmented.
- **BModel_out:** The beginning of an attempt to implement exporting to bmd *very* incomplete.

### Terminology
The terminology isn't completely consistent throughout the project, but here are a few terms:

Blender defines **meshes** (3D geometry data) as a collection of **polygons** (faces), **edges**, **vertices** and **loops**. these **blender edges** are never manipulated directly.
- A **polygon** is a collection of its **vertices**, **edges** and **loops**
- An **edge** is just a pair of **vertices**, shared between **polygons**
- A **vertex** (plural: vertices) is a single point in space. for our purposes, it only has a number (in the list of vertices in the mesh) and spatial coordinates. It is shared between **polygons**
- A **loop** is an abstract structure which is a mix-up of a **vertex** and an **edge**. Every loop links to these two. A **loop** belongs to a *single* **polygon**. It contains data such as (badly named) *vertex colors*, orientation (normal vector), and texture coordinates (UV coordinates).

Blender's **armatures**, used to animate a mesh, are composed of **bones**, which are in a tree-like disposition, with some **bones** being children of one another.
In the mesh, there are **vertex groups**, which dictate which bone's position affects which vertices' positions, and how much.
The blender **bones** are obtained with what are called **joints** in the bmd file.
