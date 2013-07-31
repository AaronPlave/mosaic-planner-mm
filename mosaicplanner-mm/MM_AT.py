#Main Micromanager interface for MosaicPlanner

#imports the python wrapper for the Micromanager core
import MMCorePy

#starts an instance of the core
mmc = MMCorePy.CMMCore()

info = mmc.getVersionInfo()
print info,"\n"

def loadsysconf(conf):
     """Loads a MM microscope configuration file""" 
     mmc.loadSystemConfiguration(conf)

def setExposure(exposure_ms):
    mmc.setExposure(exposure_ms)

def snapImage():
    #snaps image and returns image, image properties
    mmc.snapImage()
    image = mmc.getImage()
    width = mmc.getImageWidth()
    height = mmc.getImageHeight()
    return image,width,height
    

def get_property(prop,element='Zeiss Axiocam'): #prop like binning
    try:
        return mmc.getProperty(element,prop)
    except:
        print "Unable to get %s from  %s" %(prop,element)

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
        
#might want to add wait for device in these set* functions
def setZ(z):
    mmc.setPosition("ZeissFocusAxis",z)

def setXY(x,y):
    mmc.setXYPosition("ZeissXYStage",x,y) #set position

def getXYZ():
    x = mmc.getXPosition('ZeissXYStage')
    y = mmc.getYPosition('ZeissXYStage')
    z = mmc.getPosition('ZeissFocusAxis')
    return (x,y,z)

def setAutoShutter(arg):
     mmc.setAutoShutter(arg)

def setShutter(arg):
     mmc.setShutterOpen(arg)

def getPixelSizeUm():
     return mmc.getPixelSizeUm()

def unload_devices():
     """Must call this at the end of each session or else the devices will
     remain read-only until the process is terminated"""
     mmc.unloadAllDevices()

#'Micro-Manager-1.4_nightly.cfg'
