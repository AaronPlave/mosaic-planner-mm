import os
import glob
import OleFileIO_PL
import numpy as np
from xml.dom.minidom import parseString
    
def GetXMLMetaFloatByIndex(dom,index):
        
    xmlTag = dom.getElementsByTagName('V%d'%index)[0].toxml()
    xmlData=xmlTag.replace("<V%d>"%index,'').replace("</V%d>"%index,'')
    xmlData=float(xmlData)
    return float(xmlData)
    
def FindTag(tagnode,tagindex):
    #finds the tagnode which within it has the value of tagindex, then find what the tagnumber (???) is, 
    #so the node of the form <I???>tagindex</???> then look for the
    #corresponding node of the form <V???>value</V???> and return value
    children=tagnode.childNodes
    for node in children:
        if(node.nodeName[0]=='I'):
            index=int(node.nodeName.lstrip('I'))
            xmlTag=node.toxml()
            data=xmlTag.replace("<%s>"%node.nodeName,'').replace("</%s>"%node.nodeName,'')
            data=int(data)
            if data==tagindex:
                value= GetXMLMetaFloatByIndex(tagnode,index)
                return value

            
def LoadAxioVisionXMLMetaData(filename):
         
    #open the xml file for reading:
    file = open(filename,'r')
    #convert to string:
    data = file.read()
    #close file because we dont need it anymore:
    file.close()
    #parse the xml you got from the file
    dom = parseString(data)

    #retrieve the Tags root dom element
    tagroot=dom.getElementsByTagName('Tags')[0]
    #get the value associated with each of these tag index values
    xpos= FindTag(tagroot,2073)
    ypos= FindTag(tagroot,2074)
    ScaleFactorX= FindTag(tagroot,769)
    ScaleFactorY= FindTag(tagroot,772)
    Width= FindTag(tagroot,515)
    Height= FindTag(tagroot,516)
    extent=[xpos-(Width/2)*ScaleFactorX,xpos+(Width/2)*ScaleFactorX,\
                 ypos+(Height/2)*ScaleFactorY,ypos-(Height/2)*ScaleFactorY]
    print "loaded metadata from xml file, extent was detected to be: "
    print extent 
    return extent

def LoadMMMetaData(filename):
    """retrieves and parses metadata from mm folder..."""
##    print "loading MM Metadata"
    file = open(filename,'r')
    data = file.read()
    file.close()
    data = data.replace("false","False")
    data = data.replace("true","True")
    data = data.replace("null","0")
    f = eval(str(data))
    tiles = []
    for i in f.keys():
        if i != "Summary":
            tiles.append(i)
    xpos = f[tiles[0]]["XPositionUm"]
    ypos = f[tiles[0]]["YPositionUm"]
    zpos = f[tiles[0]]["ZPositionUm"] 
    ScaleFactorX= f["Summary"]["PixelSize_um"]
    ScaleFactorY= ScaleFactorX
    Width=f["Summary"]["Width"]
    Height=f["Summary"]["Height"]
    extent=[xpos-(Width/2)*ScaleFactorX,xpos+(Width/2)*ScaleFactorX,\
           ypos-(Height/2)*ScaleFactorY,ypos+(Height/2)*ScaleFactorY] #FOR NOW

        #WHY WAS IT + THEN - FOR Y??
##    print extent, "HERE"
    return extent,zpos
    
def LoadZVIMetaData(filename):
    """function for loading metadata using the OLE zvi reader I developed
    
    keywords:
    filename)a string containing the path of the metadata filename
    
    returns (scalefactor,extent)
    scalefactor: microns/pixel for the image
    extent: a list [minx,maxx,miny,maxy] of the corners of the image.  This will specify the scale of the image, and allow the corresponding point functionality
    to specify how much the movable point should be shifted in the units given by this extent.
    
    """
    print "Loading zvi file metadata..."

    ole = OleFileIO_PL.OleFileIO(filename)
    #ole.dumpdirectory()
    metadata=ole.extract_metadata()
    (channeldict,Width,Height,MosaicSizeX,MosaicSizeY,ScaleFactorX,ScaleFactorY,\
    channels,XPositions,YPositions,FocusPositions,XCoors,YCoors,ExposureTimes)=metadata
    Xpos=np.array(XPositions);
    Ypos=np.array(YPositions);

    extent=[Xpos.min()-(Width/2)*ScaleFactorX,Xpos.max()+(Width/2)*ScaleFactorX,\
                 Ypos.max()+(Height/2)*ScaleFactorY,Ypos.min()-(Height/2)*ScaleFactorY]
    
    return extent

def LoadMetadata(filename):
##    print filename
    globbed=glob.glob(os.path.join(os.path.dirname(filename),'*.zvi'))
    if globbed:
        return LoadZVIMetaData(globbed[0])
    globbed=glob.glob(os.path.join(os.path.dirname(filename),'*.xml'))
    if globbed:
        return LoadAxioVisionXMLMetaData(globbed[0])
    globbed=glob.glob(os.path.join(os.path.dirname(filename),'metadata.txt'))
    if globbed:
        return LoadMMMetaData(globbed[0])
    return None
    #no further valid options, crash horribly
    
