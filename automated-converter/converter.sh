#!/bin/sh
# note: do update this script by setting the correct path to whatever blender instance you have installed
"blender" -b -P "IOmanager.py" "${@}"
