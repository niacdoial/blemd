#! /usr/bin/python3#macroscript BMDImporterUI2 category:"MaxBMD" tooltip:"BMD Importer" Icon:#("Maxscript", 2) ButtonText:"MaxBMD"
#(
#	include "BModel.ms"
#
#    -- note that the mactoscript itself defines a scope
#
#	rollout MaxBMDUI_Rollout "BMD Importer"
#	(
#		edittext txtFilePath "BMD File: " enabled:false text:"" width:250 align:#left
#		button btnBrowse "Browse..." width:100 align:#center
#		spinner spnBoneThickness "Bone Thickness:" range:[0,100,5] align:#left fieldwidth:50
#		checkBox chkTextureMirror "Allow mirrored textures " checked:true width:250 align:#left
#		checkBox chkForceBones "Force create bones " checked:false width:250 align:#left
#		checkBox chkSaveAnim "Save Animations " checked:true width:250 align:#left
#		checkBox chkExportTextures "Export textures" checked:true width:250 align:#left
#		checkBox chkIncludeScaling "Include scaling" checked:false width:250 align:#left
#		radiobuttons radExportType labels:#("character export (modeling)", ".X export (games)")
#		button btnImport "Import" width:100 align:#center
#		label lblNotes "" width:250 height:200 align:#left -- IMPORTANT: must unhide all items before exporting .x file.
#		
# 		on btnBrowse pressed do
#		(
#			local f = getOpenFileName types:"BMD (*.bmd)"
#			if f != undefined then
#			(
#				fileType = getFilenameType f
#				if fileType  == ".bmd" OR fileType == ".BMD" OR fileType  == ".bdl" OR fileType == ".BDL" then
#					txtFilePath.text = f
#				else
#					messageBox "Only BMD or BDL files are supported"
#			)
#		)
#
#		on btnImport pressed do
#		(
#			if (txtFilePath.text == undefined OR txtFilePath.text == "") then
#				messageBox "You must select a BMD file to import"
#			else
#			(
#				Undo off 
#				(
#					btnImport.enabled = false
#					bmd = BModel()
#					bmd.SetBmdViewExePath (getDir #maxroot)
#
#					-- UPDATE BMDVIEW.EXE PATH
#					-- bmd.SetBmdViewExePath "C:\\" -- if Max version before 2008 and the path contains spaces the path will have to be manually updated
#					local exportType = case radExportType.state of (
#														1: #CHARACTER
#														2: #XFILE
#													)
#
#					bmd.Import txtFilePath.text spnBoneThickness.value chkTextureMirror.checked chkForceBones.checked chkSaveAnim.checked chkExportTextures.checked exportType chkIncludeScaling.checked
#					btnImport.enabled = true
#				)
#				
#				Undo on (radExportType)
#				
#				DestroyDialog MaxBMDUI_Rollout
#			)
#		)
#	)
#	
#	createDialog MaxBMDUI_Rollout 300 240
#
#)
#