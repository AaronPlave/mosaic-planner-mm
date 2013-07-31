from MM_AT import *
import numpy as np
import Image
import time


def sixteen2eightB(img16):
    """Converts 16 bit PIL image to 8 bit PIL image"""
    a = img16[0]
    b=256.0*a/a.max()
    array8= np.reshape(b,(img16[2],img16[1]))
    img8 = Image.fromarray(array8)
    
    return img8


### Waiting for devices to finish is generally iffy. Sometimes it works,
### other times it doesn't. 

def wait_Zstage(): #could also do a while getXYZ != target, pass?
##    while mmc.deviceBusy('ZeissFocusAxis'):
    time.sleep(.2)
def wait_XYstage():
##    while mmc.deviceBusy('ZeissXYStage'):
##        pass
    time.sleep(.2)
    
def get(pos,auto=False,steps=False,rough_size=False,fine_size=False): #hmm, have get calling auto and auto calling get. bad.
    """sets pos, snaps image at pos"""
    setXY(pos[0],pos[1])
    curr = (getXYZ()[0],getXYZ()[1])
    if curr != (pos[0],pos[1]):
        wait_XYstage()
    if auto:
        z = autofocus(pos,steps,rough_size,fine_size)
        setZ(z[0][2])
        wait_Zstage()
        return z
    else:
        im = sixteen2eightB(snapImage())
        return im

#Unused function but could use for predicting next position, same as PosList guess
def guess_next_linear(p1,p2): #eventually modify to include a real Z guess?
    dx,dy = p2[0]-p1[0],p2[1]-p1[1]
    p3 = (p2[0]+dx,p2[1]+dy,p2[2]) #just using last Z for current Z
    return p3


#DETERMINES SCORE OF IMAGE BASED ON MAX HISTOGRAM VALUE
def sharpness(image):
    hist = image.histogram()
    score = max(hist)
    return score


def autofocus(pos,steps,rough_step,fine_step):
    """
    Basic autofocus, improve later, use MM if possible?
    """
    start = time.clock()
    print "pos,steps,rough_step,fine_step = ",pos,steps,rough_step,fine_step
    #set initial position
    setXY(pos[0],pos[1])
    wait_XYstage() #add check for curr pos == set pos here if it hangs
    setZ(pos[2])
    wait_Zstage()

    xyz = getXYZ()
    im = get(xyz)
    best = (xyz,sharpness(im),im)
    
    #rough focus list######
    z = xyz[2]
    plus_r = [z + step*rough_step for step in range(1,steps+1)]
    minus_r = [z - step*rough_step for step in range(1,steps+1)]
    roughs = plus_r+minus_r

    streak = 0
    found = False
    for i in roughs:
        setZ(i)
        wait_Zstage()
        pos = getXYZ()
        im = get(pos)
        score = sharpness(im)
        if score > best[1]:
            best = (pos,score,im)
            streak = +1
            found = True

        else:
            if found == True:
                if streak == 3:
                    break 
                else:
                    streak += 1


    #fine focus list#########
    z = best[0][2]
    plus = [z + step*fine_step for step in range(1,steps+1)]
    minus = [z - step*fine_step for step in range(1,steps+1)]
    fines = plus+minus

    streak = 0
    found = False
    for i in fines:
        setZ(i)
        wait_Zstage()
        pos = getXYZ() 
        im = get(pos)
        score = sharpness(im)
        if score > best[1]:
            best = (pos,score,im)
            streak = +1
            found = True

        else:
            if found == True:
               ##        print "current pos is best"
                if streak == 3:
                    break 
                else:
                    streak += 1

    end = time.clock()
    
    
    if found == False:
        setZ(best[0][2])
    time.sleep(.1)
    return best



		
