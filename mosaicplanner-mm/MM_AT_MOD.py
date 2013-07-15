#Micromanager Array Tomography

import MMCorePy
mmc = MMCorePy.CMMCore()
info = mmc.getVersionInfo()
print info,"\n"

def loadsysconf(conf="AT_without_CAM.cfg"):
     mmc.loadSystemConfiguration(conf)
     mmc.loadDevice("cam","DemoCamera","DCam")
     mmc.initializeDevice("cam")

loadsysconf()
def setExposure(exposure_ms):
    mmc.setExposure(exposure_ms)

def snapImage():
    #snaps image and returns image, image properties
    mmc.snapImage()
    image = mmc.getImage()
    width = mmc.getImageWidth()
    height = mmc.getImageHeight()
    return image,width,height
    
#Properties
def get_property(prop,element='Zeiss Axiocam'): #prop like binning
    try:
        return mmc.getProperty(element,prop)
    except:
        print "Unable to get %s from  %s" %(prop,element)
        return .6  
def set_property(prop,value,element='Zeiss Axiocam'):
    #set some properties
    mmc.setProperty(element, prop,value)


#print out supported properties
def print_suppported_properties(element="Core"):
    properties = mmc.getDevicePropertyNames(element)
    proplst = []
    for i in range(len(properties)):
        prop = properties[i]
        val = mmc.getProperty(element,prop)
        proplst.append(prop)
        print "Name: " + prop + ", value: " + val

    #Values valid for each property, could return empty which could mean too many
    for i in proplst:
        values = mmc.getAllowedPropertyValues("Core",i)
        print i,values

def setZ(z):
    mmc.setPosition("ZeissFocusAxis",z)

def setXY(x,y): #NOT SURE HOW ACCURATE SET AND GET ARE, MIGHT WANT TO MOVE PLACES TWICE
    mmc.setXYPosition("ZeissXYStage",x,y) #set position

def getXYZ():
    x = mmc.getXPosition('ZeissXYStage')
    y = mmc.getYPosition('ZeissXYStage')
    z = mmc.getPosition('ZeissFocusAxis')
    return (x,y,z)



#set filter, shutter,etc. = mmc.setState("F1",3) or
    #mmc.setProperty("Camera", "Exposure", "55.0")
#mmc.setProperty("ZeissReflectedLightShutter","State","0") - shutter close
##mmc.setXYPosition("ZeissXYStage",0.00,0.00) #set position
####print mmc.getXYPosition("ZeissXYStage")
##import time
##time.sleep(2)
##mmc.setXYPosition("ZeissXYStage",2.00,3.00) #set position
####print mmc.getXYPosition("ZeissXYStage")
##
##time.sleep(2)
##mmc.setXYPosition("ZeissXYStage",100.00,50.00) #set position
####print mmc.getXYPosition("ZeissXYStage")
##time.sleep(2)
##mmc.setXYPosition("ZeissXYStage",100.00,50.00) #set position

