#===============================================================================
# 
#  License: GPL
# 
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License 2
#  as published by the Free Software Foundation.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# 
#===============================================================================
 
 
from PIL import Image
import ImageEnhance
import numpy as np
import threading
import os
import Queue
from CenterRectangle import CenterRectangle
from matplotlib.lines import Line2D
import MetadataHandler
#implicity this relies upon matplotlib.axis matplotlib.AxisImage matplotlib.bar 


#my custom 2d correlation function for numpy 2d matrices.. 
def mycorrelate2d(fixed,moved,skip=3):
    """a 2d correlation function for numpy 2d matrices
    
    arguments
    fixed) is the larger matrix which should stay still 
    moved) is the smaller matrix which should move left/right up/down and sample the correlation
    skip) is the number of positions to skip over when sampling, 
    so if skip =3 it will sample at shift 0,0 skip,0 2*skip,0... skip,0 skip,skip...
    
    returns
    corrmat) the 2d matrix with the corresponding correlation coefficents of the data at that offset
    note the 0,0 entry of corrmat corresponds to moved(0,0) corresponding to fixed(0,0)
    and the 1,1 entry of corrmat corresponds to moved(0,0) corresponding to fixed(skip,skip)
    NOTE) the height of corrmat is given by corrmat.height=ceil((fixed.height-moved.height)/skip)
    and the width in a corresonding manner.
    NOTE)the standard deviation is measured over the entire dataset, so particular c values can be above 1.0
    if the variance in the subsampled region of fixed is lower than the variance of the entire matrix
    
    """
    
    (fh,fw)=fixed.shape
    (mh,mw)=moved.shape
    deltah=(fh-mh)
    deltaw=(fw-mw)
    if (deltah<1 or deltaw<1):
        return
    fixed=fixed-fixed.mean()
    fixed=fixed/fixed.std()
    moved=moved-moved.mean()
    moved=moved/moved.std()
    ch=np.ceil(deltah*1.0/skip)
    cw=np.ceil(deltaw*1.0/skip)
    
    corrmat=np.zeros((ch,cw))
    
    #print (fh,fw,mh,mw,ch,cw,skip,deltah,deltaw)
    for shiftx in range(0,deltaw,skip):
        for shifty in range(0,deltah,skip):
            fixcut=fixed[shifty:shifty+mh,shiftx:shiftx+mw]
            corrmat[shifty/skip,shiftx/skip]=(fixcut*moved).sum()
           
    corrmat=corrmat/(mh*mw)
    
    return corrmat


def sixteen2eight(img16):
    """Converts 16 bit PIL image to 8 bit PIL image"""
    a = np.array(img16.getdata(),dtype='uint16')
    b=256.0*a/a.max()
    array8= np.reshape(b,(img16.size[1],img16.size[0]))
    img8 = Image.fromarray(array8)
    return img8

#thread for making a cropped version of the big image... not very efficent    
class ImageCutThread(threading.Thread):
        def __init__(self, queue):
            threading.Thread.__init__(self)
            self.queue = queue        
        def run(self):
            while True:
                #grabs host from queue
                (filename,rect,i) = self.queue.get()
                image=Image.open(filename)
                image=image.crop(rect)
                (path,file)=os.path.split(filename)
                path=os.path.join(path,"previewstack")
                if not os.path.exists(path):
                    os.path.os.mkdir(path)
                cutfile=os.path.splitext(file)[0]+"stack%3d.tif"%i        
                cutfile=os.path.join(path,cutfile)
                image.save(cutfile)
                #signals to queue job is done
                self.queue.task_done()
                     
class MosaicImage():
    """A class for storing the a large mosaic image in a matplotlib axis. Also contains functions for finding corresponding points
    in the larger mosaic image, and plotting informative graphs about that process in different axis"""
    def __init__(self,axis,one_axis,two_axis,corr_axis,imagefile,imagematrix,extent=None,flipVert=False):
        """initialization function which will plot the imagematrix passed in and set the bounds according the bounds specified by extent
        
        keywords)
        axis)the matplotlib axis to plot the image into
        one_axis) the matplotlib axis to plot the cutout of the fixed point when using the corresponding point functionality
        two_axis) the matplotlib axis to plot the cutout of the point that should be moved when using the corresponding point functionality
        corr_axis) the matplotlib axis to plot out the matrix of correlation values found when using the corresponding point functionality
        imagefile) a string with the path of the file which contains the full resolution image that should be used when calculating the corresponding point funcationality
         currently the reading of the image is using PIL so the path specified must be an image which is PIL readable
        imagematrix) a numpy 2d matrix containing a low resolution version of the full resolution image, for the purposes of faster plotting/memory management
        extent) a list [minx,maxx,miny,maxy] of the corners of the image.  This will specify the scale of the image, and allow the corresponding point functionality
        to specify how much the movable point should be shifted in the units given by this extent.  If omitted the units will be in pixels and extent will default to
        [0,width,height,0].
       
        """
        #define the attributes of this class
        self.axis=axis
        self.one_axis=one_axis
        self.two_axis=two_axis
        self.corr_axis=corr_axis
        self.imagefile=imagefile
        self.imagefiles = [imagefile] #need to somehow load more images into this, assume they get added
        self.imageExtents = {imagefile:MetadataHandler.LoadMetadata(imagefile)}
        self.flipVert=flipVert
        self.imagematrix=imagematrix


        
        #read in the full resolution height/width using PIL
        image = sixteen2eight(Image.open(imagefile))
        
        (self.originalwidth,self.originalheight)=image.size
        
        #if extent was not specified default to units of pixels with 0,0 in the upper left
        if extent==None:
            if flipVert:
                self.extent=[0,self.originalwidth,0,self.originalheight]
            else:
                self.extent=[0,self.originalwidth,self.originalheight,0]
        else:
            self.extent=extent
 
        #calculate the width of the image (calling it _um assuming its in units of microns)
        #from now on I will assume the units are in microns, though if they were in some other unit it would just carry through
        width_um=self.extent[1]-self.extent[0]
##        print self.extent
        width_um *= .6     
        
        #height_um=self.extent[2]-self.extent[3]
##        print self.extent
        
        #calculate the pixels/micron of full resolution picture
        self.orig_um_per_pix=width_um/self.originalwidth
##        print "px/micron of full res?",self.orig_um_per_pix
        
        #calculate the pixels/micron of the downsampled matrix 
        (matrix_height,matrix_width)=imagematrix.shape
        self.matrix_scale=matrix_width/width_um

        self.matrix_scale = .6 #because I'm not scaling right now?
##        print "px/Um downsample",self.matrix_scale
        
        
        
        #plot the image using paintImage
        self.paintImage()
        
        #initialize the images for the various subplots as None
        self.oneImage=None
        self.twoImage=None
        self.corrImage=None
        self.set_maxval(self.imagematrix.max(axis=None))
        
        self.axis.set_title('Mosaic Image')

##
##   import Image
##    import MetadataHandler
##    import numpy as np
##
##    def sixteen2eight(img16):
##        """Converts 16 bit PIL image to 8 bit PIL image"""
##        a = np.array(img16.getdata(),dtype='uint16')
##        b=256.0*a/a.max()
##        array8= np.reshape(b,(img16.size[1],img16.size[0]))
##        img8 = Image.fromarray(array8)
##        return img8

##    files = ['G:\\6_17 Test DAPI 10x\\images\\1-Pos_000_000\\img_000000000_DAPI_000.tif',
##                     'G:\\6_17 Test DAPI 10x\\images\\1-Pos_000_001\\img_000000000_DAPI_000.tif',
##                     'G:\\6_17 Test DAPI 10x\\images\\1-Pos_000_002\\img_000000000_DAPI_000.tif',
##                     'G:\\6_17 Test DAPI 10x\\images\\1-Pos_001_000\\img_000000000_DAPI_000.tif',
##                     'G:\\6_17 Test DAPI 10x\\images\\1-Pos_001_001\\img_000000000_DAPI_000.tif',
##                     'G:\\6_17 Test DAPI 10x\\images\\1-Pos_001_002\\img_000000000_DAPI_000.tif',
##                     'G:\\6_17 Test DAPI 10x\\images\\1-Pos_002_000\\img_000000000_DAPI_000.tif',
##                     'd:\User_Data\\Administrator\\Desktop\\mm\\New Folder\\TEST2\\Pos1\\img_000000000_Default_000.tif',
##                     'd:\User_Data\\Administrator\\Desktop\\mm\\New Folder\\TEST2\\Pos2\\img_000000000_Default_000.tif',
##                     'd:\User_Data\\Administrator\\Desktop\\mm\\New Folder\\TEST2\\Pos3\\img_000000000_Default_000.tif']
##    stuff = []
##    for i in files:
##        ext = MetadataHandler.LoadMetadata(i)
##        tile = sixteen2eight(Image.open(i))
##        stuff.append((tile,ext))
##
##    print stuff

    def pad(self,mosaic,tile,mosaic_extent,tile_extent):
##        print mosaic_extent,"me"
##        mosaic.show()
##        tile.show()
##        print tile_extent,"te"
        #takes mosaic and pads based on current extent(in Um) and new extent,
        #returns new mosaic and new extent

        #checking to see whether tile or mosaic has the maximum/min for extent
        if tile_extent[0] <= mosaic_extent[0]:
            minx = tile_extent[0]
        else:
            minx = mosaic_extent[0]
            
        if tile_extent[1] >= mosaic_extent[1]:
            maxx = tile_extent[1]
        else:
            maxx = mosaic_extent[1]
            
        if tile_extent[2] <= mosaic_extent[2]:
            miny = tile_extent[2]
        else:
            miny = mosaic_extent[2]
            
        if tile_extent[3] >= mosaic_extent[3]:
            maxy = tile_extent[3]
        else:
            maxy = mosaic_extent[3]
        
        extent = (minx,maxx,miny,maxy)

        #can I just convert back to pixels here? also are pxUm conversions
        #intoducing error?
        px1,px2 = [i/.6 for i in mosaic_extent],[i/.6 for i in tile_extent]

        #size = tile_extent maxx - mosaic_extent minx..
        #Padding
        size_int = (abs(int(maxx/.6-minx/.6)),abs(int(maxy/.6-miny/.6)))
        
        im = Image.new('L',size_int)
####        print px1,"px1"
##        print px2,"px2"
##        print minx/.6
##        print miny/.6
        im.paste(mosaic,(int(abs(px1[0]-minx/.6)),int(abs(px1[3]-maxy/.6))))
        im.paste(tile,(abs(int(px2[0]-minx/.6)),int(abs(px2[3]-maxy/.6))))
##        print int(px1[0]-minx/.6),int(abs(px1[2]-maxy/.6))
##        print int(px2[0]-minx/.6),int(abs(px2[2]-maxy/.6))
##        print size_int
##        im.show()
        im.save('C:\Users\Aaron\Desktop\mosaic.tif')
##        print extent
        return im,extent
        
    def extendMosaicTiff(self, mosaic, image_file_name, low_res_image_array, old_extent):
        #add new image to image files
        self.imagefiles.append(image_file_name)
        
##        print self.imagefiles,"IMAGEFILES"
        
        #grab image metadata
        tile_extent = MetadataHandler.LoadMetadata(image_file_name)        

        #add image extent to imageExtents dict
        self.imageExtents[image_file_name] = tile_extent
        
        #pad low res
        self.imagematrix,self.extent=self.pad(mosaic,low_res_image_array,old_extent,tile_extent)
        self.imagematrix = np.reshape(self.imagematrix.getdata(),(self.imagematrix.size[1],self.imagematrix.size[0]))
        return self.extent
        

    def findTileExtent(self,tile):
        if len(self.imagefiles) == 1:
            return self.extent
        else:
            return self.imageExtents[tile]        
            
    
    def findHighResImageFile(self,x,y):
        #assume x and y are stage coordinates (in microns)
        
        for img in self.imagefiles: #eventually turn this into a dict instead of parsing each time
            #grab metadata
            
            tile_extent = MetadataHandler.LoadMetadata(img)
            
            if x >= tile_extent[0] and x <= tile_extent[1]:
                if y >= tile_extent[2] and y <= tile_extent[3]:   
                    self.imagefile = img
                    return self.imagefile
                
        return False #did not find HightResImageFile containing x,y coords

     
    def set_extent(self,extent):
        self.extent=extent
        width_um=self.extent[1]-self.extent[0]
        #height_um=self.extent[2]-self.extent[3]
        
        #calculate the pixels/micron of full resolution picture
##        self.orig_um_per_pix=width_um/self.originalwidth    
        #calculate the pixels/micron of the downsampled matrix 
        (matrix_height,matrix_width)=self.imagematrix.shape
        self.matrix_scale=matrix_width/width_um
##        print self.extent,"Eeee"
        self.Image.set_extent(self.extent)
        self.axis.set_xlim(self.extent[0],self.extent[1])
        if self.flipVert:
            self.axis.set_ylim(self.extent[3],self.extent[2])
        else:
            self.axis.set_ylim(self.extent[2],self.extent[3])
        self.axis.set_xlabel('X Position (microns)')
        self.axis.set_ylabel('Y Position (microns)')
        

    def paintImage(self):
        """plots self.imagematrix in self.axis using self.extent to define the boundaries"""
        self.Image=self.axis.imshow(self.imagematrix,cmap='gray',extent=self.extent)
        (minval,maxval)=self.Image.get_clim()
        self.maxvalue=maxval
        #self.axis.canvas.get_toolbar().slider.SetSelection(minval,self.maxvalue)
        self.axis.autoscale(False)
        self.axis.set_xlabel('X Position (pixels)')
        self.axis.set_ylabel('Y Position (pixels)')
        self.Image.set_clim(0,25000)
    
    def set_maxval(self,maxvalue):
        """set the maximum value in the image colormap"""
        self.maxvalue=maxvalue;
        self.repaint()
        
    def repaint(self):
        """sets the new clim for the Image using self.maxvalue as the new maximum value"""
        (minval,maxval)=self.Image.get_clim()
        self.Image.set_clim(minval,self.maxvalue)
        if self.oneImage!=None:
            self.oneImage.set_clim(minval,self.maxvalue)
        if self.twoImage!=None:
            self.twoImage.set_clim(minval,self.maxvalue)
    
    def paintImageCenter(self,cut,theaxis,xc=0,yc=0,skip=1,cmap='gray',scale=1):
        """paints an image and redefines the coordinates such that 0,0 is at the center
        
        keywords
        cut)the 2d numpy matrix with the image data
        the axis)the matplotlib axis to plot it in
        skip)the factor to rescale the axis by so that 1 entry in the cut, is equal to skip units on the axis (default=1)
        cmap)the colormap designation to use for the plot (default 'gray')
        
        """
        theaxis.cla()
        (h,w)=cut.shape
        dh=skip*1.0*(h-1)/2       
        dw=skip*1.0*(w-1)/2
        dh=dh*scale;
        dw=dw*scale;
        if self.flipVert:
            ext=[xc-dw,xc+dw,yc-dh,yc+dh]
        else:
            ext=[xc-dw,xc+dw,yc-dh,yc+dh]
        image=theaxis.imshow(cut,cmap=cmap,extent=ext)
        theaxis.set_xlim(xc-dw,xc+dw) 
        if self.flipVert:
            theaxis.set_ylim(yc-dh,yc+dh)
        else:
            theaxis.set_ylim(yc-dh,yc+dh) #changed this to have cutouts work but it changed the cross correllation, made it negative somewhere 
        theaxis.hold(True)
        print (xc-dw,xc+dw) ,"x vals"
        print (yc-dh,yc+dh),"y vals"
        return image 
    
    def updateImageCenter(self,cut,theimage,theaxis,xc=0,yc=0,skip=1,scale=1):
        """updates an image with a new image
        
        keywords
        cut) the 2d numpy matrix with the image data 
        theimage) the image to update
        theaxis) the axis that the image is in
        skip)the factor to rescale the axis by so that 1 entry in the cut, is equal to skip units on the axis (default=1)

        """
        (h,w)=cut.shape
        dh=skip*1.0*(h-1)/2       
        dw=skip*1.0*(w-1)/2
        dh=dh*scale;
        dw=dw*scale;
        theimage.set_array(cut)
        if self.flipVert:
            ext=[xc-dw,xc+dw,yc-dh,yc+dh]
        else:
            ext=[xc-dw,xc+dw,yc-dh,yc+dh]
        theimage.set_extent(ext)
        theaxis.set_xlim(xc-dw,xc+dw) 
        if self.flipVert:
            theaxis.set_ylim(yc-dh,yc+dh)
        else:
            theaxis.set_ylim(yc-dh,yc+dh) #changed this to have cutouts work 
        print (xc-dw,xc+dw) ,"x vals"
        print (yc-dh,yc+dh),"y vals"
         
    def paintImageOne(self,cut,xy=(0,0),dxy_pix=(0,0),window=0):
        """paints an image in the self.one_axis axis, plotting a box of size 2*window+1 around that point
        
        keywords
        cut) the 2d numpy matrix with the image data
        dxy_pix) the center of the box to be drawn given as an (x,y) tuple
        window)the size of the box, where the height is 2*window+1
        
        """
        (xc,yc)=xy  
        (dx,dy)=dxy_pix
        dx=dx*self.orig_um_per_pix;
        dy=dy*self.orig_um_per_pix;
        #the size of the cutout box in microns
##        print xc,yc,"xc yc, or the middle stage coord of the cutout"
##        print dx,dy
##        print self.orig_um_per_pix,"um"
        boxsize_um=(2*window+1)*self.orig_um_per_pix;
        
        #if there is no image yet, create one and a box
        if self.oneImage==None:
            self.oneImage=self.paintImageCenter(cut, self.one_axis,xc=xc,yc=yc,scale=self.orig_um_per_pix)
            self.oneBox=CenterRectangle((xc+dx,yc+dy),width=50,height=50,edgecolor='r',linewidth=1.5,fill=False)
            self.one_axis.add_patch(self.oneBox)
            self.one_axis_center=Line2D([xc],[yc],marker='+',markersize=7,markeredgewidth=1.5,markeredgecolor='r')
            self.one_axis.add_line(self.one_axis_center) 
            self.one_axis.set_title('Point 1')
            self.one_axis.set_ylabel('Microns')
            self.one_axis.autoscale(False)
            self.oneImage.set_clim(0,self.maxvalue)     
        #if there is an image update it and the self.oneBox
        else:
            self.updateImageCenter(cut, self.oneImage, self.one_axis,xc=xc,yc=yc,scale=self.orig_um_per_pix)
            self.oneBox.set_center((dx+xc,dy+yc))
            self.oneBox.set_height(boxsize_um)
            self.oneBox.set_width(boxsize_um)
            self.one_axis_center.set_xdata([xc])
            self.one_axis_center.set_ydata([yc])
    
        
    def paintImageTwo(self,cut,xy=(0,0)):
        """paints an image in the self.two_axis, with 0,0 at the center cut=the 2d numpy"""
        #create or update appropriately
        (xc,yc)=xy
##        print xy,"xy2"
        if self.twoImage==None:
            self.twoImage=self.paintImageCenter(cut, self.two_axis,xc=xc,yc=yc,scale=self.orig_um_per_pix)
            self.two_axis_center=Line2D([xc],[yc],marker='+',markersize=7,markeredgewidth=1.5,markeredgecolor='r')
            self.two_axis.add_line(self.two_axis_center) 
            self.two_axis.set_title('Point 2')
            self.two_axis.set_ylabel('Pixels from point 2')
            self.two_axis.autoscale(False)
            self.twoImage.set_clim(0,self.maxvalue)
 
        else:
            self.updateImageCenter(cut, self.twoImage, self.two_axis,xc=xc,yc=yc,scale=self.orig_um_per_pix)
            self.two_axis_center.set_xdata([xc])
            self.two_axis_center.set_ydata([yc])
    
    def paintCorrImage(self,corrmat,dxy_pix,skip):
        """paints an image in the self.corr_axis, with 0,0 at the center and rescaled by skip, plotting a point at dxy_pix
        
        keywords)
        corrmat) the 2d numpy matrix with the image data
        dxy_pix) the offset in pixels from the center of the image to plot the point
        skip) the factor to rescale the axis by, so that when corrmat was produced by mycorrelate2d with a certain skip value, 
        the axis will be in units of pixels
        
        """
        #unpack the values
        (dx,dy)=dxy_pix
        #update or create new
        if self.corrImage==None:
            self.corrImage=self.paintImageCenter(corrmat, self.corr_axis,skip=skip,cmap='jet')             
            self.maxcorrPoint,=self.corr_axis.plot(dx,-dy,'ro')

            self.colorbar=self.corr_axis.figure.colorbar(self.corrImage,shrink=.9)
            self.corr_axis.set_title('Cross Correlation')
            self.corr_axis.set_ylabel('Pixels shifted')
          
        else:
            self.updateImageCenter(corrmat, self.corrImage, self.corr_axis,skip=skip)
            self.maxcorrPoint.set_data(dx,-dy)   
        #hard code the correlation maximum at .5
        self.corrImage.set_clim(0,.5)

    def convert_pos_to_orig_ind(self,x,y,tile=None):
        """converts a position in original units (usually microns) to indices in the original full resolution image
        
        keywords)
        x)x position in microns
        y)y position in microns
        
        returns) (x_pix,y_pix) the indices in pixels of that location
        
        """
        
        extent = self.findTileExtent(tile) if tile else self.extent
        x=x-extent[0]
        #if self.flipVert:
        #    y=self.extent[2]-y
        #else:
##        print y,extent,"SASFSD"
        y=abs(extent[3]-extent[2])-abs(extent[2]-y)
##        print x,y,"IS IT RIGHT?"
##        x_pix=int(round(x/self.orig_um_per_pix))
##        y_pix=int(round(y/self.orig_um_per_pix))
        x_pix=abs(int(x/.6)) #should just be converting to pixels here. Works but may be slightly off.
        y_pix=abs(int(y/.6))
##        print "convert_pos_to_orig_ind complete",extent,x_pix,y_pix
        return (x_pix,y_pix)
    
    
    def cutout_window(self,x,y,window):
        """returns a cutout of the original image at a certain location and size
        
        keywords)
        x)x position in microns
        y)y position in microns
        window) size of the patch to cutout, will cutout +/- window in both vertical and horizontal dimensions
        note.. behavior not well specified at edges, may crash
        
        function uses PIL to read in image and crop it appropriately
        returns) cut: a 2d numpy matrix containing the removed patch
        
        """
        tile = self.findHighResImageFile(x,y)
##        print x,y,"xy CUTOUT POS"
        (xpx,ypx)=self.convert_pos_to_orig_ind(x,y,tile)
        image=sixteen2eight(Image.open(tile))
##        print xpx,ypx,"XPX,YPX"
        image=image.crop([xpx-window,ypx-window,xpx+window,ypx+window])
        #image=image.convert('L')
##        image.show()
        #enh = ImageEnhance.Contrast(image)
        #image=enh.enhance(1.5)   
        (width,height)=image.size
##        print width,height
##        image.show()
        

        #WHAT MODE SHOULD THIS BE?
        cut=np.reshape(np.array(image.getdata(),np.dtype('uint16')),(height,width))
##        cut=np.reshape(np.array(image.getdata(),np.dtype('L')),(height,width))
        return cut



    def cross_correlate_two_to_one(self,xy1,xy2,window=100,delta=75,skip=3):
        """take two points in the image, and calculate the 2d cross correlation function of the image around those two points
        
        keywords)
        xy1) a (x,y) tuple specifying point 1, the point that should be fixed
        xy2) a (x,y) tuple specifiying point 2, the point that should be moved
        window) the size of the patch to cutout (+/- window around the points) for calculating the correlation (default = 100 pixels)
        delta) the size of the maximal shift +/- delta from no shift to calculate
        skip) the number of integer pixels to skip over when calculating the correlation
        
        returns (one_cut,two_cut,corrmat)
        one_cut) the patch cutout around point 1
        two_cut) the patch cutout around point 2
        corrmat) the matrix of correlation values measured with 0,0 being a shift of -delta,-delta
        
        """
##        from matplotlib import pyplot as plt

        (x1,y1)=xy1
        (x2,y2)=xy2
        one_cut=self.cutout_window(x1,y1,window+delta)
        two_cut=self.cutout_window(x2,y2,window)
        #return (target_cut,source_cut,mycorrelate2d(target_cut,source_cut,mode='valid'))
    
##        print xy1,xy2
##        print type(one_cut)
##        plt.imshow(one_cut, interpolation='nearest')
##        plt.show()
        
##        plt.imshow(two_cut, interpolation='nearest')

##        plt.show()
        return (one_cut,two_cut,mycorrelate2d(one_cut,two_cut,skip))
       
    def align_by_correlation(self,xy1,xy2,window=100,delta=75,skip=3):
        """take two points in the image, and calculate the 2d cross correlation function of the image around those two points
        plots the results in the appropriate axis, and returns the shift which aligns the two points given in microns
        
        keywords)
        xy1) a (x,y) tuple specifying point 1, the point that should be fixed
        xy2) a (x,y) tuple specifiying point 2, the point that should be moved
        window) the size of the patch to cutout (+/- window around the points) for calculating the correlation (default = 100 pixels)
        delta) the size of the maximal shift +/- delta from no shift to calculate
        skip) the number of integer pixels to skip over when calculating the correlation
        
        returns) (maxC,dxy_um)
        maxC)the maximal correlation measured
        dxy_um) the (x,y) tuple which contains the shift in microns necessary to align point xy2 with point xy1
        
        """
        #calculate the cutout patches and the correlation matrix
        (one_cut,two_cut,corrmat)=self.cross_correlate_two_to_one(xy1,xy2,window,delta,skip)
        #find the peak of the matrix
        maxind=corrmat.argmax()
        #determine the indices of that peak
        (max_i,max_j)=np.unravel_index(maxind,corrmat.shape)

##        print max_i,max_j,"mI,mJ"
        
        
        #calculate the shift for that index in pixels
        dy_pix=max_i*skip-delta
        dx_pix=max_j*skip-delta

        

        #convert those indices into microns
        dy_um=dy_pix*self.orig_um_per_pix
        dx_um=dx_pix*self.orig_um_per_pix


        #pack up the shifts into tuples
        dxy_pix=(dx_pix,dy_pix)
        dxy_um=(dx_um,dy_um)
        #calculate what the maximal correlation was
        corrval=corrmat.max()
        
        print "(correlation,(dx,dy))="
        print (corrval,dxy_pix)
        #paint the patch around the first point in its axis, with a box of size of the two_cut centered around where we found it
        self.paintImageOne(one_cut,xy=xy1,dxy_pix=dxy_pix, window=window)
        #paint the patch around the second point in its axis
        self.paintImageTwo(two_cut,xy=xy2)
        #paint the correlation matrix in its axis
        self.paintCorrImage(corrmat, dxy_pix,skip)
        return (corrmat.max(),dxy_um)
    
    def paintPointsOneTwo(self,xy1,xy2,window):
        (x1,y1)=xy1
        (x2,y2)=xy2
        one_cut=self.cutout_window(x1,y1,window)
        two_cut=self.cutout_window(x2,y2,window)
##        print "HIII",x1,y1,window
        self.paintImageOne(one_cut,xy1)
        #paint the patch around the second point in its axis
        self.paintImageTwo(two_cut,xy2)
        
    def make_preview_stack(self,xpos,ypos,width,height,directory):
        print "make a preview stack"
   
        hw_pix=int(round(width*.5/self.orig_um_per_pix))
        hh_pix=int(round(height*.5/self.orig_um_per_pix))
        queue = Queue.Queue()
          
        #spawn a pool of threads, and pass them queue instance 
        for i in range(4):
            t = ImageCutThread(queue)
            t.setDaemon(True)
            t.start()
              
        for i in range(len(self.mosaicArray.xpos)):
            (cx_pix,cy_pix)=self.convert_pos_to_ind(xpos[i],ypos[i])
            rect=[cx_pix-hw_pix,cy_pix-hh_pix,cx_pix+hw_pix,cy_pix+hh_pix]
            queue.put((self.imagefile,rect,i))
        queue.join()
