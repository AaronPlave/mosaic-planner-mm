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

print "Current stage position: ",getXYZ()

##p1 = (5232.75, -503.25, -35.209)
##p2 =(5232.75, -503.25, -35.209)


def wait_Zstage(): #could also do a while getXYZ != target, pass?
##    while mmc.deviceBusy('ZeissFocusAxis'):
    time.sleep(.2)
def wait_XYstage():
##    while mmc.deviceBusy('ZeissXYStage'):
##        pass
    time.sleep(.2)
    
def get(pos,auto=False): #hmm, have get calling auto and auto calling get. bad.
    """sets pos, snaps image at pos"""
    setXY(pos[0],pos[1])
    curr = (getXYZ()[0],getXYZ()[1])
    if curr != (pos[0],pos[1]):
        wait_XYstage()
    if auto:
        z = autofocus(pos,4,10,2)
        setZ(z[0][2])
        wait_Zstage()
        return z
    else:
        im = sixteen2eightB(snapImage())
        return im

def guess_next_linear(p1,p2): #should eventually modify to include a real Z guess
    dx,dy = p2[0]-p1[0],p2[1]-p1[1]
    p3 = (p2[0]+dx,p2[1]+dy,p2[2]) #just using last Z for current Z
    print p3,"p3 guess"
    return p3

def main(num_pos):
##    p1 = (74.25, -34.0, -72.57900000000001)
##    p2 = (-907.75, 266.75, -72.57900000000001)
    setXY(p2[0],p2[1])

    #All the positions
    positions = [p1,p2]
    
    #and go!
    for i in range(num_pos):
        p3 = guess_next_linear(positions[-2],positions[-1])
        get(p3,True)
        positions.append(p3)
        
    return positions

def sharpness(image):
    hist = image.histogram()
    score = max(hist)
    return score


def autofocus(pos,steps,rough_step,fine_step):
    """
    Basic autofocus, improve later, use MM if possible?
    """
    start = time.clock()

    #set initial position
    setXY(pos[0],pos[1])
    wait_XYstage() #add check for curr pos == set pos here if it hangs
    setZ(pos[2])
    wait_Zstage()

    #get pos, current image, and current sharpness
    print "AUTOFOCUS STARTED AT POSITION --> ",getXYZ()
    xyz = getXYZ()
    im = get(xyz)
    best = (xyz,sharpness(im),im)
    print "original score to beat --> ",best[1]
    
    #rough focus list######
    z = xyz[2]
    plus_r = [z + step*rough_step for step in range(1,steps+1)]
    minus_r = [z - step*rough_step for step in range(1,steps+1)]
    roughs = plus_r+minus_r
    print roughs,"roughs"

    streak = 0
    found = False
    print "rough focusing"
    for i in roughs:
        setZ(i)
##        print "SHOULD BE AT Z POS",i
        wait_Zstage()
        pos = getXYZ()
        print pos
##        print "Z POS IS ",pos
        im = get(pos)
##        im.show()
        score = sharpness(im)
        if score > best[1]:
            best = (pos,score,im)
            print "better score at pos: ", pos, " score: ",score
            streak = +1
            found = True

        else:
            if found == True:
                if streak == 3:
                    break 
                else:
                    streak += 1
    print found,streak     

    print "best rough pos --> ", best[0]

    #fine focus list#########
    z = best[0][2]
    print "score to beat --> ",best[1]
    plus = [z + step*fine_step for step in range(1,steps+1)]
    minus = [z - step*fine_step for step in range(1,steps+1)]
    fines = plus+minus
    print fines

    streak = 0
    found = False
    print "fine focusing"
    for i in fines:
        setZ(i)
        wait_Zstage()
        pos = getXYZ() 
        print pos
        im = get(pos)
        score = sharpness(im)
##        print score
        if score > best[1]:
            best = (pos,score,im)
            print "better score at pos: ", pos, " score: ",score
            streak = +1
            found = True

        else:
            if found == True:
                if streak == 3:
                    break 
                else:
                    streak += 1

    ##finished##
    print "sharpest image --> ", best

    end = time.clock()
    
##    best[2].show()
    print "Run time = ",end-start
    
    if found == False:
        print "current pos is best"
    setZ(best[0][2])
    return best

##
##
##mmc.setAutoShutter(0)
##mmc.setShutterOpen(1)
setExposure(150)
##x = get(getXYZ(),True)
####main(1)
##mmc.setShutterOpen(0)
##
##





		
