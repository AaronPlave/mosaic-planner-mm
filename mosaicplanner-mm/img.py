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

#THIS IS AN UNUSED FUNCTION
def guess_next_linear(p1,p2): #eventually modify to include a real Z guess?
    dx,dy = p2[0]-p1[0],p2[1]-p1[1]
    p3 = (p2[0]+dx,p2[1]+dy,p2[2]) #just using last Z for current Z
##    print p3,"p3 guess"
    return p3

#TEST FUNCTION
def main(num_pos):
    setXY(p2[0],p2[1])

    #All the positions
    positions = [p1,p2]
    
    #and go!
    for i in range(num_pos):
        p3 = guess_next_linear(positions[-2],positions[-1])
        get(p3,True)
        positions.append(p3)
        
    return positions

#DETERMINES SCORE OF IMAGE BASED ON MAX HISTOGRAM VALUE
def sharpness(image):
    hist = image.histogram()
    score = max(hist)
    return score


def autofocus(pos,steps,rough_step,fine_step):
    """
    Basic autofocus, improve later, use MM if possible?
    """
##    print "starting autofocus"
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

    ##finished##
##    print "sharpest image --> ", best

    end = time.clock()
    
##    print "Run time = ",end-start
    
    if found == False:
##        print "current pos is best"
        setZ(best[0][2])
    time.sleep(.1)
    return best


def main2():
    mmc.setAutoShutter(0)
    mmc.setShutterOpen(1)
    start = time.clock()
    a = get(getXYZ(),True)
    stop = time.clock()
    print "Run time = ",stop-start," seconds"
    print a
    a[2].show()
    mmc.setShutterOpen(0)
    return a

##main2()


		
