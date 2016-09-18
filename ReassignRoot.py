#! /usr/bin/python3    -- from ui/macroscripts/Macro_BoneAdjustmentsTools. on ReassignRoot_btn pressed do
def removeIKsolvers(a):
    if  (not IsProperty(a, "pos")) or (not IsProperty(a, "rotation")):
        HDIKSys.RemoveChain(a)


def getEndPoint(a):
    if  type(a) == BoneGeometry:         # XCX what does this code?!
       [a.length,0,0] * a.objectTransform
    else:
       (a.transform).translation


def copyBoneHeightWidth(destination, source):
        

    if  (source is not None) and type(source) == BoneGeometry:
        destination.width = source.width
        destination.height = source.height


def ReassignRoot(currentBone):
        
    # -- messageBox (currentBone as string)
        undo "Reassign Root" on
        (
            with redraw off
            (
                with animate off
                (
                    deleteBoneArr = []
                    # -- local currentBone   = selection[1]
                    selBone    = None
                    chlBone    = None
                    parentBone = currentBone.parent
                    prevBone   = None
                    newBone    = None
                    newBoneArr = []
                    endBone    = None
                    revReset
                    exPrevBone = None
                    i

                    fn isPosSame a b =
                    (
                        posTol = 5
                        v1=a
                        v2=b
                        vi=0
                        if ((v1.x) <= (v2.x  + posTol)) and ((v1.x) >= (v2.x- posTol)) : vi +=1
                        if ((v1.y) <= (v2.y  + posTol)) and ((v1.y) >= (v2.y- posTol)) : vi +=1
                        if ((v1.z) <= (v2.z  + posTol)) and ((v1.z) >= (v2.z- posTol)) : vi +=1

                        if vi > 1 : true else false
                    )

                    append deleteBoneArr currentBone

                    removeIKsolvers currentBone

                    if currentBone.children.count > 0 :
                        chlBone = currentBone.children
                        revReset = true





                    if (classOf(currentBone) == BoneGeometry) and (currentBone.length == 10) and (currentBone.children.count == 0) :
                        currentBone = parentBone
                        parentBone = currentBone.parent
                        append deleteBoneArr currentBone




                    if parentBone != undefined :
                        do   # -- bone creation loop
                        (
                            removeIKsolvers currentBone

                            if  classOf(currentBone) == BoneGeometry  :
                                newBone = boneSys.createBone (getEndPoint currentBone) currentBone.transform.translation currentBone.dir
                                copyBoneHeightWidth newBone currentBone
                                newBone.name = currentBone.name
                                newBone.wirecolor=currentBone.wirecolor
                                newBone.parent = prevBone
                                newBone.resetBoneStretch()


if (parentBone.children.count > 1) and (parentBone.parent != undefined) :        
                                    parentBone.children.parent =  newBone





if (newBone.children == 0) and (newBone.length == 10) :        
                                    delete newBone





if chlBone != undefined :        
                                    chlBone.parent=newBone





if prevBone == undefined :        
                                    selBone = newbone





                                prevBone = newBone
                                currentBone = parentBone
                                parentBone = currentBone.parent


if ( classOf(currentBone) == BoneGeometry ) : append deleteBoneArr currentBone
                                append newBoneArr newBone



                            else  :

if (parentBone.children.count > 1) and (parentBone.parent != undefined) :        
                                  local siblings =
[]    

    for b in n parentBone.children  :
                

        if b != currentBone :                        
                                      append siblings b


        


    

    for i in range( 1 , d+ 1) :






if chlBone != undefined :        
                                    chlBone.parent=currentBone





if prevBone == undefined :        
                                    selBone = currentBone




                                exPrevBone  = prevBone
                                prevBone    = currentBone
                                currentBone = parentBone
                                parentBone  = currentBone.parent
                                prevBone.parent = exPrevBone

if  classOf(currentBone) == BoneGeometry  : append deleteBoneArr currentBone




                        )
while parentBone != undefined :
- bone creation loop


                        # --removeIKsolvers currentBone


if currentBone.children.count > 1 :        

    if  classOf(currentBone) == BoneGeometry  :                
                                local chlVar =
[]        


        for b in n currentBone.children  :
                        
                                    # --removeIKsolvers b
                                    append chlVar b
                                    b.parent = undefined


        

                                newBone = boneSys.createBone (getEndPoint currentBone)         currentBone.transform.translation currentBone.dir
                                copyBoneHeightWidth newBone currentBone
                                newBone.name = currentBone.name
                                newBone.wirecolor=currentBone.wirecolor
                                newBone.parent = prevBone

                                chlVar.parent=newBone

                                newBone.realignBoneToChild()
                                newBone.resetBoneStretch()
                                append newBoneArr newBone


    

    else  :                
                                currentBone.parent = prevBone
                                append newBoneArr currentBone


    




else  :        

    if  classOf(currentBone) == BoneGeometry  :                
                                newBone = boneSys.createBone (getEndPoint currentBone)         currentBone.transform.translation currentBone.dir
                                copyBoneHeightWidth newBone currentBone
                                newBone.name = currentBone.name
                                newBone.wirecolor=currentBone.wirecolor
                                newBone.parent = prevBone
                                append newBoneArr newBone

                                parentBone = newBone

                                newBone=BoneSys.createBone parentBone.transform.translation (parentBone.transform.translation+6)         parentBone.dir
                                copyBoneHeightWidth newBone parentBone
                                newBone.rotation=parentBone.rotation
                                newBone.pos=parentBone.transform.translation
                                in coordSys Local move newBone [parentBone.length,0,0]
                                newBone.parent=parentBone
                                newBone.width=parentBone.width
                                newBone.height=parentBone.height
                                newBone.taper=90
                                newBone.length=(parentBone.width+parentBone.height)        /2
                                newBone.wirecolor=parentBone.wirecolor


    

    else  :                
                                currentBone.parent = prevBone


    





for b in n deleteBoneArr  :
        

    if not isDeleted b : delete b





if revReset != true :        

    for i in range(1 , d+ 1) :
1 to newBoneArr.count do
                                (
                                (newBoneArr[i]).resetBoneStretch()
                            )




else  :        

    for i in range(newBoneArr.count , d+ 1) :
newBoneArr.count to 2 by -1 do
                                (
                                (newBoneArr[i]).resetBoneStretch()
                            )





                        select selBone



                )
            )
        )


