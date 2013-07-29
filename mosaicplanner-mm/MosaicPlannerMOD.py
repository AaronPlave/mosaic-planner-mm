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
 
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from NavigationToolBarImproved import NavigationToolbar2Wx_improved as NavBarImproved
from matplotlib.figure import Figure
import OleFileIO_PL,os
import Image
import wx.lib.intctrl
import numpy as np
from Settings import MosaicSettings, CameraSettings, ChangeCameraSettings, ImageSettings, ChangeImageMetadata, SmartSEMSettings, ChangeSEMSettings,MMSettings,ChangeMMSettings
from PositionList import posList
from MyLasso import MyLasso
from MosaicImage import MosaicImage
from Transform import Transform,ChangeTransform
from xml.dom.minidom import parseString
import wx
import MetadataHandler
import MM_AT  #_MOD #as MM_AT
import time
import json
import img as Acq
import collections
import sys
import shutil
import Image #chANGE TO from PIL import Image -for 64 bit sometimes
from matplotlib.patches import Rectangle


class MosaicToolbar(NavBarImproved):
    """A custom toolbar which adds buttons and to interact with a MosaicPanel
    
    current installed buttons which, along with zoom/pan
    are in "at most one of group can be selected mode":
    selectnear: a cursor point
    select: a lasso like icon  
    add: a cursor with a plus sign
    selectone: a cursor with a number 1
    selecttwo: a cursor with a number 2
    
    installed Simple tool buttons:
    deleteTool) calls self.canvas.OnDeleteSelected ID=ON_DELETE_SELECTED
    corrTool: a button that calls self.canvas.OnCorrTool ID=ON_CORR
    stepTool: a button that calls self.canvas.OnStepTool ID=ON_STEP
    ffTool: a button that calls OnFastForwardTool ID=ON_FF
    
    
    installed Toggle tool buttons:
    gridTool: a toggled button that calls self.canvas.OnGridTool with the ID=ON_GRID
    rotateTool: a toggled button that calls self.canvas.OnRotateTool with the ID=ON_ROTATE
    THESE SHOULD PROBABLY BE CHANGED TO BE MORE MODULAR IN ITS EFFECT AND NOT ASSUME SOMETHING
    ABOUT THE STRUCTURE OF self.canvas
    
    a set of controls for setting the parameters of a mosaic (see class MosaicSettings)
    the function getMosaicSettings will return an instance of MosaicSettings with the current settings from the controls
    the function self.canvas.posList.set_mosaic_settings(self.getMosaicSettings) will be called when the mosaic settings are changed
    the function self.canvas.posList.set_mosaic_visible(visible) will be called when the show? checkmark is click/unclick
    THIS SHOULD BE CHANGED TO BE MORE MODULAR IN ITS EFFECT
    
    note this will also call self.canvas.OnHomeTool when the home button is pressed
    """
    ON_FIND = wx.NewId()
    ON_SELECT  = wx.NewId()
    ON_SELECT_IMG = wx.NewId()
    ON_NEWPOINT = wx.NewId()
    ON_DELETE_SELECTED = wx.NewId()
    ON_DELETE_IMG = wx.NewId()
    #ON_CORR_LEFT = wx.NewId()
    ON_STEP = wx.NewId()
    ON_FF = wx.NewId()
    ON_LOADIMG = wx.NewId()
    ON_LOADIMG2 = wx.NewId()
    ON_NEXT = wx.NewId()
    ON_MANUAL_IMG = wx.NewId()    
    ON_CORR = wx.NewId() 
    ON_FINETUNE = wx.NewId()
    ON_GRID = wx.NewId()
    ON_ROTATE = wx.NewId()
    ON_REDRAW = wx.NewId()
    MAGCHOICE = wx.NewId()
    SHOWMAG = wx.NewId()
  
    def __init__(self, plotCanvas):  
        """initializes this object
        
        keywords)
        plotCanvas: an instance of MosaicPanel which has the correct features (see class doc)
        
        """
        
        #recursively call the init function of what we are extending
        NavBarImproved.__init__(self, plotCanvas)
        
        #import the icons
        selectBmp=wx.Image('icons/lasso-icon.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        addpointBmp=wx.Image('icons/add-icon.bmp', wx.BITMAP_TYPE_BMP).ConvertToBitmap()
        trashBmp =  wx.Image('icons/delete-icon.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()             
        selectnearBmp =  wx.Image('icons/cursor2-icon.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()   
        # wx.Image('icons/cursor-icon.bmp', wx.BITMAP_TYPE_BMP).ConvertToBitmap()  
        oneBmp =wx.Image('icons/one-icon.bmp', wx.BITMAP_TYPE_BMP).ConvertToBitmap()  
        twoBmp =wx.Image('icons/two-icon.bmp', wx.BITMAP_TYPE_BMP).ConvertToBitmap()
        stepBmp = wx.Image('icons/step-icon.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()  
        #leftcorrBmp = wx.ArtProvider.GetBitmap(wx.ART_GO_BACK,wx.ART_TOOLBAR) ]
        corrBmp = wx.Image('icons/target-icon.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        ffBmp =  wx.Image('icons/ff-icon.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        smalltargetBmp = wx.Image('icons/small-target-icon.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        rotateBmp = wx.Image('icons/rotate-icon.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        gridBmp = wx.Image('icons/grid-icon.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
    
        
        #add the mutually exclusive/toggleable tools to the toolbar, see superclass for details on how function works
        self.selectImg=self.add_user_tool('selectImg',6,selectnearBmp,True,'Add Nearest Image to selection')        
        self.selectNear=self.add_user_tool('selectnear',7,selectnearBmp,True,'Add Nearest Point to selection')
        self.selectTool=self.add_user_tool('select', 8, selectBmp, True, 'Select Points')
        self.addTool=self.add_user_tool('add', 9, addpointBmp, True, 'Add a Point')     
        self.oneTool = self.add_user_tool('selectone', 10, oneBmp, True, 'Choose pointLine2D 1') 
        self.twoTool = self.add_user_tool('selecttwo', 11, twoBmp, True, 'Choose pointLine2D 2')
        
        self.AddSeparator()
        self.AddSeparator()
        
        #add the simple button click tools
        #self.leftcorrTool=self.AddSimpleTool(self.ON_CORR_LEFT,leftcorrBmp,'do something with correlation','correlation baby!') 
        self.deleteTool=self.AddSimpleTool(self.ON_DELETE_SELECTED,trashBmp,'Delete selected points','delete points') 
        self.deleteImg=self.AddSimpleTool(self.ON_DELETE_IMG,trashBmp,'Delete selected image','delete img')
        self.corrTool=self.AddSimpleTool(self.ON_CORR,corrBmp,'Ajdust pointLine2D 2 with correlation','corrTool') 
        self.stepTool=self.AddSimpleTool(self.ON_STEP,stepBmp,'Take one step using points 1+2','stepTool')     
        self.ffTool=self.AddSimpleTool(self.ON_FF,ffBmp,'Auto-take steps till C<.3 or off image','fastforwardTool')       
        self.loadimages=self.AddSimpleTool(self.ON_LOADIMG,ffBmp,'Load first image manually')
        self.loadimages2=self.AddSimpleTool(self.ON_LOADIMG2,stepBmp,'Load second image manually')
        self.nextimage=self.AddSimpleTool(self.ON_NEXT,corrBmp,'Acquire new images automatically')
        self.nextimage=self.AddSimpleTool(self.ON_MANUAL_IMG,corrBmp,'Acquire new images manually without autofocus')
        #add the toggleable tools
        self.gridTool=self.AddCheckTool(self.ON_GRID,gridBmp,wx.NullBitmap,'toggle rotate boxes')
        #self.finetuneTool=self.AddSimpleTool(self.ON_FINETUNE,smalltargetBmp,'auto fine tune positions','finetuneTool')  
        #self.redrawTool=self.AddSimpleTool(self.ON_REDRAW,smalltargetBmp,'redraw canvas','redrawTool')  
        self.rotateTool=self.AddCheckTool(self.ON_ROTATE,rotateBmp,wx.NullBitmap,'toggle rotate boxes')
        #self.AddSimpleTool(self.ON_ROTATE,rotateBmp,'toggle rotate mosaic boxes according to rotation','rotateTool')
        
      
        #setup the controls for the mosaic
        self.showmagCheck = wx.CheckBox(self)
        self.showmagCheck.SetValue(False)
        self.magChoiceCtrl = wx.lib.agw.floatspin.FloatSpin(self,size=(65, -1 ),
                                       value=65.486,
                                       min_val=0,
                                       increment=.1,
                                       digits=2,
                                       name='magnification')    
                #wx.lib.intctrl.IntCtrl( self, value=63,size=( 30, -1 ) )
        self.mosaicXCtrl = wx.lib.intctrl.IntCtrl( self, value=1,size=( 20, -1 ) )
        self.mosaicYCtrl = wx.lib.intctrl.IntCtrl( self, value=1,size=( 20, -1 ) )
        self.overlapCtrl = wx.lib.intctrl.IntCtrl( self, value=10,size=( 25, -1 ))
        
        #setup the controls for the min/max slider
        minstart=0
        maxstart=500
        #self.sliderMinCtrl = wx.lib.intctrl.IntCtrl( self, value=minstart,size=( 30, -1 ))
        self.slider = wx.Slider(self,value=250,minValue=minstart,maxValue=maxstart,size=( 180, -1),style = wx.SL_SELRANGE)        
        self.sliderMaxCtrl = wx.lib.intctrl.IntCtrl( self, value=maxstart,size=( 60, -1 ))
    
        #add the control for the mosaic
        self.AddControl(wx.StaticText(self,label="Show Mosaic"))
        self.AddControl(self.showmagCheck)  
        self.AddControl(wx.StaticText(self,label="Mag"))
        self.AddControl( self.magChoiceCtrl)         
        self.AddControl(wx.StaticText(self,label="MosaicX"))
        self.AddControl(self.mosaicXCtrl)       
        self.AddControl(wx.StaticText(self,label="MosaicY"))     
        self.AddControl(self.mosaicYCtrl)       
        self.AddControl(wx.StaticText(self,label="%Overlap"))      
        self.AddControl(self.overlapCtrl)
        self.AddSeparator()
        #self.AddControl(self.sliderMinCtrl)
        self.AddControl(self.slider)
        self.AddControl(self.sliderMaxCtrl)

        #bind event handles for the various tools
        
        #this one i think is inherited... the zoom_tool function
        self.Bind(wx.EVT_TOOL, self.on_toggle_pan_zoom, self.zoom_tool)    
        # self.Bind(wx.wx.EVT_TOOL,self.canvas.OnHomeTool,self.home_tool)
        self.Bind(wx.EVT_CHECKBOX,self.toggleMosaicVisible,self.showmagCheck)
        self.Bind( wx.lib.agw.floatspin.EVT_FLOATSPIN,self.updateMosaicSettings, self.magChoiceCtrl)
        self.Bind(wx.lib.intctrl.EVT_INT,self.updateMosaicSettings, self.mosaicXCtrl)
        self.Bind(wx.lib.intctrl.EVT_INT,self.updateMosaicSettings, self.mosaicYCtrl)
        self.Bind(wx.lib.intctrl.EVT_INT,self.updateMosaicSettings, self.overlapCtrl)

        #event binding for slider
        self.Bind(wx.EVT_SCROLL_THUMBRELEASE,self.canvas.OnSliderChange,self.slider)
        #self.Bind(wx.lib.intctrl.EVT_INT,self.updateSliderRange, self.sliderMinCtrl)
        self.Bind(wx.lib.intctrl.EVT_INT,self.updateSliderRange, self.sliderMaxCtrl)
        
        wx.EVT_TOOL(self, self.ON_DELETE_SELECTED, self.canvas.OnDeletePoints)  
        wx.EVT_TOOL(self, self.ON_DELETE_IMG, self.canvas.DeleteImg)
        wx.EVT_TOOL(self, self.ON_CORR, self.canvas.OnCorrTool)        
        wx.EVT_TOOL(self, self.ON_STEP, self.canvas.OnStepTool)           
        wx.EVT_TOOL(self, self.ON_FF, self.canvas.OnFastForwardTool)
        wx.EVT_TOOL(self, self.ON_LOADIMG, self.canvas.ButtonLoad) ################################################ for loading first image
        wx.EVT_TOOL(self, self.ON_LOADIMG2, self.canvas.ButtonLoad2) ################################################ for loading second image
        wx.EVT_TOOL(self, self.ON_NEXT, self.canvas.NextImage) #################################################### for loading next images automatically
        wx.EVT_TOOL(self, self.ON_MANUAL_IMG, self.canvas.Manual_Img) #################################################### for loading next images automatically
        wx.EVT_TOOL(self, self.ON_GRID, self.canvas.OnGridTool)
        #wx.EVT_TOOL(self, self.ON_FINETUNE, self.canvas.OnFineTuneTool)
        #wx.EVT_TOOL(self, self.ON_REDRAW, self.canvas.OnRedraw)
        wx.EVT_TOOL(self, self.ON_ROTATE, self.canvas.OnRotateTool)
        
        self.Realize()
    
    def updateMosaicSettings(self,evt=""):
        """"update the mosaic_settings variables of the canvas and the posList of the canvas and redraw
        set_mosaic_settings should take care of what is necessary to replot the mosaic"""
        self.canvas.posList.set_mosaic_settings(self.getMosaicParameters())
        self.canvas.mosaic_settings=self.getMosaicParameters()
        self.canvas.draw()
    
    def updateSliderRange(self,evt=""):
        #self.setSliderMin(self.sliderMinCtrl.GetValue())
        self.setSliderMax(self.sliderMaxCtrl.GetValue())
        
        
    def toggleMosaicVisible(self,evt=""):
        """call the set_mosaic_visible function of self.canvas.posList to initiate what is necessary to hide the mosaic box"""
        self.canvas.posList.set_mosaic_visible(self.showmagCheck.IsChecked())
        self.canvas.draw()
        
    def getMosaicParameters(self):
        """extract out an instance of MosaicSettings from the current controls with the proper values"""
        return MosaicSettings(mag=self.magChoiceCtrl.GetValue(),
                              show_box=self.showmagCheck.IsChecked(),
                              mx=self.mosaicXCtrl.GetValue(),
                              my=self.mosaicYCtrl.GetValue(),
                              overlap=self.overlapCtrl.GetValue())
                                 
    #unused 
    def CrossCursor(self, event):
        self.canvas.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
    #overrides the default
    def home(self,event):
        """calls self.canvas.OnHomeTool(), should be triggered by the hometool press.. overrides default behavior"""
        self.canvas.OnHomeTool()
    def setSliderMin(self,min=0):
        self.slider.SetMin(min)
    def setSliderMax(self,max=500):
        self.slider.SetMax(max)
           
class MosaicPanel(FigureCanvas):
    """A panel that extends the matplotlib class FigureCanvas for plotting all the plots, and handling all the GUI interface events
    """
    def __init__(self, parent, **kwargs):
        """keyword the same as standard init function for a FigureCanvas"""
        self.figure = Figure(figsize=(5, 9))
        FigureCanvas.__init__(self, parent, -1, self.figure, **kwargs)
        self.canvas = self.figure.canvas
        
        #format the appearance
        self.figure.set_facecolor((1,1,1))
        self.figure.set_edgecolor((1,1,1))
        self.canvas.SetBackgroundColour('white')   
        
        #add subplots for various things
        self.subplot = self.figure.add_axes([.05,.5,.92,.5]) 
        self.posone_plot = self.figure.add_axes([.1,.05,.2,.4]) 
        self.postwo_plot = self.figure.add_axes([.37,.05,.2,.4]) 
        self.corrplot = self.figure.add_axes([.65,.05,.25,.4]) 
        
        #initialize the camera settings and mosaic settings
        self.camera_settings=CameraSettings(sensor_height=1040,sensor_width=1388,pix_width=6.5,pix_height=6.5)
        self.mosaic_settings=MosaicSettings()
        
        
        #setup a blank position list
        self.posList=posList(self.subplot,self.mosaic_settings,self.camera_settings)
        #start with no MosaicImage
        self.mosaicImage=None
        #start with relative_motion on, so that keypress calls shift_selected_curved() of posList
        self.relative_motion = True
        
        #start with no toolbar and no lasso tool
        self.navtoolbar = None
        self.lasso = None
        self.lassoLock=False
        
        #make a sin plot just to see that things are working
        #self.t = arange(0.0,3.0,0.01)
        #s = sin(2*pi*self.t)
        #self.subplot.plot(self.t,s)

        #initialize which images are currently selected
        self.selected_imgs = ['init',[0,0,0,0]]
        self.img_box = ""
        #initialize tile height and width
        self.tile_height = 1040
        self.tile_width = 1380

        ########MOVE TO mosaicImage eventually, SETUP PREVIOUS Z LIST
        self.prevZ=[]

        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('key_press_event', self.on_key)
        
    def repaint_image(self,evt):
        """event handler used when the slider bar changes and you want to repaint the MosaicImage with a different color scale"""
        if not self.mosaicImage==None:
            self.mosaicImage.repaint()
            self.draw()
            
    def lasso_callback(self, verts):
        """callback function for handling the lasso event, called from on_release"""
        #select the points inside the vertices listed
        self.posList.select_points_inside(verts)
        #redraw the plot
        self.canvas.draw_idle()
        #release the widgetlock and remove the lasso 
        self.canvas.widgetlock.release(self.lasso)
        self.lassoLock=False
        del self.lasso
     
    def on_key(self,evt):
        if (evt.inaxes == self.mosaicImage.axis):
            if (evt.key == 'a'):
                self.posList.select_all()
                self.draw()
            if (evt.key == 'd'):
                self.posList.delete_selected()
        
    def on_press(self, evt):
        """canvas mousedown handler
        """
        #on a left click
        if evt.button == 1:
            #if something hasn't locked the widget
            if self.canvas.widgetlock.locked(): 
                return
            #if the click is inside the axis
            if evt.inaxes is None: 
                return
            #if we have a toolbar
            if (self.navtoolbar):
                #figure out which of the mutually exclusive toolbar buttons are active
                mode = self.navtoolbar.get_mode() 
                #call the appropriate function  
                if (evt.inaxes == self.mosaicImage.one_axis):
                    self.posList.pos1.setPosition(evt.xdata,evt.ydata)
                    self.mosaicImage.paintPointsOneTwo(self.posList.pos1.getPosition(),self.posList.pos2.getPosition(),window=170)
                elif (evt.inaxes == self.mosaicImage.two_axis):
                    self.posList.pos2.setPosition(evt.xdata,evt.ydata)
                    self.mosaicImage.paintPointsOneTwo(self.posList.pos1.getPosition(),self.posList.pos2.getPosition(),window=170)
                else:
                    if (mode == 'selectone'):
                        self.posList.set_pos1_near(evt.xdata,evt.ydata)   
                        if not (self.posList.pos2 == None):
                            self.mosaicImage.paintPointsOneTwo(self.posList.pos1.getPosition(),self.posList.pos2.getPosition(),window=170)             
                    if (mode == 'selecttwo'):
                        print self.posList.pos1.getPosition()
                        self.posList.set_pos2_near(evt.xdata,evt.ydata)
                        print self.posList.pos2.getPosition()
                        if not (self.posList.pos1 == None):
                            self.mosaicImage.paintPointsOneTwo(self.posList.pos1.getPosition(),self.posList.pos2.getPosition(),window=170)   
                    if (mode == 'selectnear'):
                        pos=self.posList.get_position_nearest(evt.xdata,evt.ydata) 
                        if not evt.key=='shift':
                            self.posList.set_select_all(False)
                        pos.set_selected(True)
                        
                    if (mode == 'selectImg'):
                        try:
                            (img,zpos,extent) = self.mosaicImage.findHighResImageFile(evt.xdata,evt.ydata)
                            print img, extent
##                            if not evt.key=='shift':
                            #select only current select
                            print "solo"
##                            print "solo keys",self.selected_imgs.keys()
##                            if img not in self.selected_imgs.keys():
                            print "tr"
                            print self.selected_imgs
                            try:
                                self.img_box.set_visible(False)
                            except:
                                print "first time"
                            self.selected_imgs = [img,extent]
##                            elif evt.key=='shift':
##                                #add to list
##                                print "shift"
##                                print "shift keys",self.selected_imgs.keys()
##                                if img not in self.selected_imgs.keys():
##                                    print "tr2"
##                                    self.selected_imgs[img] = extent
                            print self.selected_imgs
                            self.img_highlight() #highlights/enables for deletion all images in selected_imgs

                        except TypeError:
                            print "No image found in this location"
                                    
                    elif (mode == 'add'):
                        #CHECK FOR MM PROJECT
                        print self.Parent.MM_FLAG
                        if self.Parent.MM_FLAG == True:
                            zpos = self.mosaicImage.findHighResImageFile(evt.xdata,evt.ydata)[1]
                            self.posList.add_position(
                                evt.xdata,evt.ydata,
                                zpos) #set tile z
                            
                        if self.Parent.MM_FLAG == False:
                            self.posList.add_position(evt.xdata,evt.ydata)               
                    elif (mode  == 'select' ):
                        self.lasso = MyLasso(evt.inaxes, (evt.xdata, evt.ydata), self.lasso_callback,linecolor='white')
                        self.lassoLock=True                
                        self.canvas.widgetlock(self.lasso)
                self.draw()
                
    def on_release(self, evt):
        """canvas mouseup handler
        """
        # Note: lasso_callback is not called on click without drag so we release
        #   the lock here to handle this case as well.
        if evt.button == 1:
            if self.lassoLock:
                self.canvas.widgetlock.release(self.lasso)
                self.lassoLock=False
        else:
            #this would be for handling right click release, and call up a popup menu, this is not implemented so it gives an error
            self.show_popup_menu((evt.x, self.canvas.GetSize()[1]-evt.y), None)
    
    def get_toolbar(self):
        """"return the toolbar, make one if neccessary"""
        if not self.navtoolbar:
            self.navtoolbar = MosaicToolbar(self.canvas)
            self.navtoolbar.Realize()
        return self.navtoolbar   
                
    def OnSliderChange(self,evt):
        """handler for when the maximum value slider changes"""
        if not self.mosaicImage==None:
            self.mosaicImage.set_maxval(self.get_toolbar().slider.GetValue())
            self.draw()
            
    def OnGridTool(self,evt):
        """handler for when the grid tool is toggled"""
        #returns whether the toggle is True or False
        visible=self.navtoolbar.GetToolState(self.navtoolbar.ON_GRID)
        #make the frames grid visible/invisible accordingly
        self.posList.set_frames_visible(visible)
        self.draw()
        
    def OnDeletePoints(self,event="none"):
        """handler for handling the Delete tool press"""
        self.posList.delete_selected()
        self.draw()

    def DeleteImg(self,event="none"):
        """handler for handling the Delete Image tool press"""
        img = self.selected_imgs[0]
        print img

        print self.mosaicImage.imagefiles
        self.mosaicImage.imagefiles.remove(img)
        print self.mosaicImage.imagefiles
        
        #calculating new extent and padding

        #first image in list
        extent = MetadataHandler.LoadMetadata(self.mosaicImage.imagefiles[0])[0]

        
        #calculate extent of first tile again
        extent = MetadataHandler.LoadMetadata(self.mosaicImage.imagefiles[0])[0]
        (image,small_height,small_width)=self.Parent.LoadImage(self.mosaicImage.imagefiles[0],True) #scaling = yes
        if len(self.mosaicImage.imagefiles) == 1:
            #draw first image
            print "Loading first image..."
            self.Parent.mosaicCanvas.loadImage(image.getdata(),small_height,small_width,self.mosaicImage.imagefiles[0],self.Parent.proj_folder,flipVert=self.Parent.flipvert.IsChecked())
            self.Parent.mosaicCanvas.draw()
            self.Parent.mosaicCanvas.setImageExtent(extent)
    
        else:
            print "#########",self.mosaicImage.imagefiles
            
            for i in range(len(self.mosaicImage.imagefiles)):
                print i,self.mosaicImage.imagefiles[i],"IMAGE"
                mosaic = self.Parent.LoadImage(os.path.join(self.Parent.proj_folder,'mosaic.tif'),False)[0]
                extent2 = self.mosaicImage.extendMosaicTiff(mosaic,self.mosaicImage.imagefiles[i],self.Parent.LoadImage(self.mosaicImage.imagefiles[i],True)[0],extent,self.Parent.scaling)
                print extent2
                
            #draw new image SHOULD IT BE FROM FILE OR FROM MEMORY?
            (image,small_height,small_width)=self.Parent.LoadImage(os.path.join(self.Parent.proj_folder,'mosaic.tif'),False)

            self.mosaicImage.updateImageCenter(np.reshape(np.array(image.getdata(),np.dtype('uint16')),(small_height,small_width)),self.mosaicImage.Image,self.mosaicImage.axis)
            self.Parent.mosaicCanvas.draw()
            self.Parent.mosaicCanvas.setImageExtent(extent2)
       
        directory = os.path.dirname(img)
        print directory,"end of this shiz"
        #DELETE AFTER YOU REDO THE MOSAIC
        #shutil.rmtree(directory)
        #ALSO REMOVE THE IMG HIGHLIGHT
        #TEST MORE, DOESN'T WORK SECOND/MAYBE FIRST TIME...
        

    def img_highlight(self):
        """
        highlight selected images marked for deletion.
        """
        x,y = self.selected_imgs[1][0],self.selected_imgs[1][2]
        scaling = self.Parent.scaling
        width,height = self.tile_width*.6,self.tile_height*.6 #GENERALIZE THIS
        print x,y,width,height
        self.img_box = Rectangle((x,y), width, height,fill=False,edgecolor='c')
        self.mosaicImage.axis.add_patch(self.img_box)
        
    def OnRotateTool(self,evt):
        """handler for handling when the Rotate tool is toggled"""
        if self.navtoolbar.GetToolState(self.navtoolbar.ON_ROTATE):
            self.posList.rotate_boxes()
        else:
            self.posList.unrotate_boxes()          
        self.draw()
   
    def OnStepTool(self,evt=""):
        """handler for when the StepTool is pressed"""
        #we call another steptool function so that the fast forward tool can use the same function
        goahead=self.StepTool(window=100,delta=75,skip=3)
        self.draw()
            
    def OnCorrTool(self,evt=""):
        """handler for when the CorrTool is pressed"""
        #we call another function so the step tool can use the same function
        corrval=self.CorrTool(window=100,delta=75,skip=3)
        self.draw()
    
    def OnHomeTool(self):
        """handler which overrides the usual behavior of the home button, just resets the zoom on the main subplot for the mosaicImage"""
        self.subplot.set_xlim(self.mosaicImage.extent[1],self.mosaicImage.extent[0])
        self.subplot.set_ylim(self.mosaicImage.extent[2],self.mosaicImage.extent[3])
        self.draw()
           
    def OnFineTuneTool(self,evt=""): 
        print "fine tune tool not yet implemented, should do something to make fine adjustments to current position list"
        #this is a list of positions which we forbid from being point 1, our anchor points
        badpositions = []
        badstreak=0
        if ((self.posList.pos1 != None) & (self.posList.pos2 != None)):
            #start with point 1 where it is, and make point 2 the next point
            #self.posList.set_pos2(self.posList.get_next_pos(self.posList.pos1))
            #we are going to loop through until point 2 reaches the end
            #while (self.posList.pos2 != None):
            if badstreak>2:
                return
            #adjust the position of point 2 using a fine scale alignment with a small search radius
            corrval=self.CorrTool(window=100,delta=10,skip=1)
            #each time through the loop we are going to move point 2 but not point 1, but after awhile
            #we expect the correlation to fall off, at which point we will move point 1 to be closer
            # so first lets try moving point 1 to be the closest point to pos2 that we have fixed (which hasn't been marked "bad")
            if (corrval<.3):
                #lets make point 1 the point just before this one which is still a "good one"
                newp1=self.posList.get_prev_pos(self.posList.pos2)
                #if its marked bad, lets try the one before it
                while (newp1 in badpositions):
                    newp1=self.posList.get_prev_pos(newp1)
                self.posList.set_pos1(newp1) 
                #try again
                corrval2=self.CorrTool(window=100,delta=10,skip=1)
                if (corrval2<.3):
                    badstreak=badstreak+1
                    #if this fails a second time, lets assumarraye that this point 2 is a messed up one and skip it
                    #we just want to make sure that we don't use it as a point 1 in the future
                    badpositions.append(self.posList.pos2)
            else:
                badstreak=0
            #select pos2 as the next point in line
            self.posList.set_pos2(self.posList.get_next_pos(self.posList.pos2))
            self.draw()     
    
    #===========================================================================
    # def PreviewTool(self,evt):
    #    """handler for handling the make preview stack tool.... not fully implemented"""
    #    (h_um,w_um)=self.calcMosaicSize()
    #    mypf=pointFinder(self.positionarray,self.tif_filename,self.extent,self.originalfactor)
    #    mypf.make_preview_stack(w_um, h_um)       
    #===========================================================================
    def OnRedraw(self,evt=""):
        self.mosaicImage.paintPointsOneTwo((self.posList.pos1.x,self.posList.pos1.y),
                                           (self.posList.pos2.x,self.posList.pos2.y),
                                                               100)
        self.draw()
                        
    def OnFastForwardTool(self,event):
        """handler for the FastForwardTool"""
        goahead=True
        #keep doing this till the StepTool says it shouldn't go forward anymore
        while (goahead):
            goahead=self.StepTool(window=100,delta=75,skip=3)
            self.draw()
        #call up a box and make a beep alerting the user for help
        wx.MessageBox('Fast Forward Aborted, Help me','Info')         
                                                  
    def is_pos_on_array(self,pos):
        """function for determining if a slicePosition or Point is on the array
        
        keywords
        pos)The position to check works for anything with attributes .x and .y
        
        """
        if (pos.x<self.mosaicImage.extent[0]):
             return False
        if (pos.x>self.mosaicImage.extent[1]):
            return False
        if (pos.y>self.mosaicImage.extent[2]):
            return False
        if (pos.y<self.mosaicImage.extent[3]):
            return False
        return True
             
    def StepTool(self,window,delta,skip):
        """function for performing a step, assuming point1 and point2 have been selected
        
        keywords:
        window)size of the patch to cut out
        delta)size of shifts in +/- x,y to look for correlation
        skip)the number of positions in pixels to skip over when sampling shifts
        
        """
        newpos=self.posList.new_position_after_step()
        #if the new postiion was not created, or if it wasn't on the array stop and return False
        if newpos == None:
            return False
        if not self.is_pos_on_array(newpos):
            return False
        #if things were fine, fine adjust the position 
        corrval=self.CorrTool(window,delta,skip)
        if corrval>.3:
            return True
        else:
            return False
        
    def setImageExtent(self,extent):
        if not self.mosaicImage==None:
##            print extent
            self.mosaicImage.set_extent(extent)
            self.draw()
        
              
    def CorrTool(self,window,delta,skip):
        """function for performing the correlation correction of two points, identified as point1 and point2
        
        keywords)
        window)size of the patch to cut out
        delta)size of shifts in +/- x,y to look for correlation
        skip)the number of positions in pixels to skip over when sampling shifts
        
        """
        
        (corrval,dxy_um)=self.mosaicImage.align_by_correlation((self.posList.pos1.x,self.posList.pos1.y),(self.posList.pos2.x,self.posList.pos2.y),window,delta,1)
        (dx_um,dy_um)=dxy_um
        
        self.posList.pos2.shiftPosition(dx_um,dy_um) #watch out for this shi(f)t.. gets weird
        #self.draw()
        return corrval
          
    def OnKeyPress(self,event="none"):
        """function for handling key press events"""
        
        #pull out the current bounds
        #(minx,maxx)=self.subplot.get_xbound()
        (miny,maxy)=self.subplot.get_ybound()
        
        #make the jump a size dependant on the y extent of the bounds, and depending on whether you are holding down shift
        if event.ShiftDown():
            jump=(maxy-miny)/20
        else:
            jump=(maxy-miny)/100
        #initialize the jump to be zero
        dx=dy=0

    
        keycode=event.GetKeyCode()
     
        #if keycode in (wx.WXK_DELETE,wx.WXK_BACK,wx.WXK_NUMPAD_DELETE):
        #    self.posList.delete_selected()
        #    self.draw()
        #    return      
        #handle arrow key presses
        if keycode == wx.WXK_DOWN:
            dy=jump
        elif keycode == wx.WXK_UP:
            dy=-jump
        elif keycode == wx.WXK_LEFT:
            dx=-jump
        elif keycode == wx.WXK_RIGHT:
            dx=jump  
        #skip the event if not handled above    
        else:
            event.Skip()     
        #if we have a jump move accomplish it depending on whether you have relative_motion on/off                     
        if not (dx==0 and dy==0):
            if self.relative_motion:
                self.posList.shift_selected_curve(dx, dy)
            else:
                self.posList.shift_selected(dx,dy)
            self.draw()

    def loadImage(self,imagedata,height,width,tif_filename,proj_folder=None,extent=None,flipVert=False):
        """load an image, initializing the MosaicImage and redefining the slider such that the far right is the maximum pixel
        
        keywords:
        imagedata)a list containing all the pixels of a low res version of the mosaic, laid out row attached to row
        height) the height of the low res image
        width) the width of the low res image
        extent) a list [minx,maxx,miny,maxy] of the corners of the image.  This will specify the scale of the image, and allow the corresponding point functionality
        to specify how much the movable point should be shifted in the units given by this extent. (default=None)
        tif_filename)a string containing the path pointing to the full resolution version of the image
        
        """
##        print np.array(imagedata,np.dtype('uint16')).shape,(height,width)
        imagematrix=np.reshape(np.array(imagedata,np.dtype('uint16')),(height,width))
##        print extent
        try:
            proj_folder = self.Parent.proj_folder
        except:
            proj_folder = None
        self.mosaicImage=MosaicImage(self.subplot,self.posone_plot,self.postwo_plot,self.corrplot,tif_filename,imagematrix,proj_folder,extent,flipVert=flipVert)
       
        #self.get_toolbar().sliderMinCtrl.SetValue(int(self.mosaicImage.imagematrix.min(axis=None)))
        self.get_toolbar().sliderMaxCtrl.SetValue(int(self.mosaicImage.imagematrix.max(axis=None)))
        self.get_toolbar().updateSliderRange()

    def sixteen2eight(self,img16):
        """Converts 16 bit PIL image to 8 bit PIL image"""
        a = np.array(img16.getdata(),dtype='uint16')
        b=256.0*a/a.max()
        array8= np.reshape(b,(img16.size[1],img16.size[0]))
        img8 = Image.fromarray(array8)
        
        return img8
    
    def newImage(self,old_extent,filename):
        #this is a temporary test function since for the actual run there will only be 2 images
        #in the beginning and the rest will be acquired on the fly

        #get new image with attributes
        (image,small_height,small_width)=self.Parent.LoadImage(filename,False)

        #set extent
        old_mosaic = self.Parent.LoadImage(os.path.join(self.Parent.proj_folder,'mosaic.tif'))
        new_extent = self.mosaicImage.extendMosaicTiff(old_mosaic[0],filename,image,old_extent,self.Parent.scaling)

        (new_mosaic,small_height,small_width)=self.Parent.LoadImage(os.path.join(self.Parent.proj_folder,'mosaic.tif'))
        new_mosaic = self.sixteen2eight(new_mosaic)
        
        #update canvas
        self.mosaicImage.updateImageCenter(np.reshape(np.array(new_mosaic.getdata(),np.dtype('uint16')),(small_height,small_width)),self.mosaicImage.Image,self.mosaicImage.axis)
        self.Parent.mosaicCanvas.draw()
        self.Parent.mosaicCanvas.setImageExtent(new_extent)
        return new_extent

    def ButtonLoad(self,evt="None"):

        #PUT THIS IN POSLIST LATER
##        self.z_positions = collections.OrderedDict()
        
        #grab first image from microscope
        (steps,rough_size,fine_size) = self.Parent.focus_params
        (x,y,z) = MM_AT.getXYZ()
        orig_pos = (x,y,z)
        MM_AT.setAutoShutter(0)
        MM_AT.setShutter(1)
        MM_AT.setExposure(self.Parent.exposure)
        (pos,score,im) = Acq.get(orig_pos,True,steps,rough_size,fine_size)
        
        #check if tile folder exists
        new_tiles = os.path.join(self.Parent.proj_folder,'new_tiles')
        if not os.path.exists(new_tiles):
            os.mkdir('new_tiles')
            print "making new_tiles dir, THIS SHOULDN'T HAPPEN!"
        
        #create new dir for image, save im
        (x,y,z) = MM_AT.getXYZ()
##        self.z_positions[str((x,y))] = z
##        print self.z_positions
        str_xyz = str((x,y,z))    
        newdir = os.path.join(new_tiles,str_xyz)
        os.mkdir(newdir)
        f_out = os.path.join(newdir,'img_%s_.tif' % str_xyz)
        im.save(f_out)
        
        #write new image metadata to file, fix pixel size, currently not grabbing right 
        width,height,Pxsize,Xpos,Ypos,Zpos = im.size[0],im.size[1],.6,pos[0],pos[1],pos[2]
        d = {"Summary":{"Width":width,"Height":height,
                        "PixelSize_um":Pxsize},
             "Frame":{"XPositionUm":Xpos,"YPositionUm":Ypos,"ZPositionUm":Zpos}}   
        meta = json.dumps(d)
        new_meta = open(os.path.join(newdir,'metadata.txt'),'w')
        new_meta.write(meta)
        new_meta.close()

        #set tile width and height
        self.tile_height = height
        self.tile_width = width

        #calculate extent ------COULD PROBABLY JUST USE THE IMG FROM MEMORY, OR ELSE CLOSE IT
        extent = MetadataHandler.LoadMetadata(f_out)[0]
        (image,small_height,small_width)=self.Parent.LoadImage(f_out,True) #scaling = yes
        
        #draw first image
        print "Loading first image..."
        self.Parent.mosaicCanvas.loadImage(image.getdata(),small_height,small_width,f_out,self.Parent.proj_folder,flipVert=self.Parent.flipvert.IsChecked())
        self.Parent.mosaicCanvas.draw()
        self.Parent.mosaicCanvas.setImageExtent(extent)

        print "Now manually set second position via looking through scope."
        return

    
    def ButtonLoad2(self,evt="None"):
        """After first image is manually grabbed, use this function to grab the second image"""
        
        #grab second image from microscope
        (steps,rough_size,fine_size) = self.Parent.focus_params
        (x,y,z) = MM_AT.getXYZ()
        orig_pos = (x,y,z)
        MM_AT.setExposure(self.Parent.exposure)
        MM_AT.setShutter(1)
        MM_AT.setAutoShutter(0)
        (pos,score,im) = Acq.get(orig_pos,True,steps,rough_size,fine_size)
        MM_AT.setShutter(0)

        #check if tile folder self.Parent.mosaicCanvas.setImageExtent(extent)exists
        new_tiles = os.path.join(self.Parent.proj_folder,'new_tiles')
        if not os.path.exists(new_tiles):
            os.mkdir('new_tiles')
            print "PROBLEM, NOT FINDING new_tiles"
        
        #create new dir for image, save im
        (x,y,z) = MM_AT.getXYZ()
##        self.z_positions[str((x,y))]=z
        str_xyz = str((x,y,z))    
        newdir = os.path.join(new_tiles,str_xyz)
        os.mkdir(newdir)
        f_out = os.path.join(newdir,'img_%s_.tif' % str_xyz)
        im.save(f_out)
        
        #write new image metadata to file, fix pixel size, currently not grabbing right
        width,height,Pxsize,Xpos,Ypos,Zpos = im.size[0],im.size[1],.6,pos[0],pos[1],pos[2]
        d = {"Summary":{"Width":width,"Height":height,
                        "PixelSize_um":Pxsize},
             "Frame":{"XPositionUm":Xpos,"YPositionUm":Ypos,"ZPositionUm":Zpos}}   
        meta = json.dumps(d)
        new_meta = open(os.path.join(newdir,'metadata.txt'),'w')
        new_meta.write(meta)
        new_meta.close()

        #calculating new extent and padding
        first_image = self.mosaicImage.imagefiles[0]
        extent = self.mosaicImage.imageExtents[first_image] #a not so clean way to grab the first image extent
        extent2 = self.mosaicImage.extendMosaicTiff(self.Parent.LoadImage(first_image)[0],f_out,self.Parent.LoadImage(f_out,True)[0],extent,self.Parent.scaling) #scaling only low res param

        #draw new image SHOULD IT BE FROM FILE OR FROM MEMORY?
        (image,small_height,small_width)=self.Parent.LoadImage(os.path.join(self.Parent.proj_folder,'mosaic.tif'),False) #no scaling here, already scaled        
        
        self.mosaicImage.updateImageCenter(np.reshape(np.array(image.getdata(),np.dtype('uint16')),(small_height,small_width)),self.mosaicImage.Image,self.mosaicImage.axis)
        self.Parent.mosaicCanvas.draw()
        self.Parent.mosaicCanvas.setImageExtent(extent2)
        return
    
    def Manual_Img(self,evt="None"): #could add option for autofocus, need a dialogue box then..
        """
        Snaps an image at current position without autofocus on button activation. 
        """
        #grab image from microscope
        (x,y,z) = MM_AT.getXYZ()
        orig_pos = (x,y,z)
        MM_AT.setAutoShutter(0)
        MM_AT.setShutter(1)
        MM_AT.setExposure(self.Parent.exposure)
        img = Acq.get(orig_pos,False)
        MM_AT.setShutter(0)
        
        #check if tile folder exists
        new_tiles = os.path.join(self.Parent.proj_folder,'new_tiles')
        if not os.path.exists(new_tiles):
            os.mkdir('new_tiles')
            print "making new_tiles dir, THIS SHOULDN'T HAPPEN!"
        
        #create new dir for image, save im
        (x,y,z) = MM_AT.getXYZ()
##        self.z_positions[str((x,y))] = z
##        print self.z_positions
        str_xyz = str((x,y,z))    
        newdir = os.path.join(new_tiles,str_xyz)
        os.mkdir(newdir)
        f_out = os.path.join(newdir,'img_%s_.tif' % str_xyz)
        img.save(f_out)
        
        #write new image metadata to file, fix pixel size, currently not grabbing right 
        width,height,Pxsize,Xpos,Ypos,Zpos = img.size[0],img.size[1],.6,x,y,z
        d = {"Summary":{"Width":width,"Height":height,
                        "PixelSize_um":Pxsize},
             "Frame":{"XPositionUm":Xpos,"YPositionUm":Ypos,"ZPositionUm":Zpos}}   
        meta = json.dumps(d)
        new_meta = open(os.path.join(newdir,'metadata.txt'),'w')
        new_meta.write(meta)
        new_meta.close()

        #calculating new extent and padding
        extent = self.mosaicImage.extent

        mosaic = self.Parent.LoadImage(os.path.join(self.Parent.proj_folder,'mosaic.tif'),False)[0]
        
        extent2 = self.mosaicImage.extendMosaicTiff(mosaic,f_out,self.Parent.LoadImage(f_out,True)[0],extent,self.Parent.scaling)
        
        #draw new image SHOULD IT BE FROM FILE OR FROM MEMORY?
        (image,small_height,small_width)=self.Parent.LoadImage(os.path.join(self.Parent.proj_folder,'mosaic.tif'),False)

        self.mosaicImage.updateImageCenter(np.reshape(np.array(image.getdata(),np.dtype('uint16')),(small_height,small_width)),self.mosaicImage.Image,self.mosaicImage.axis)
        self.Parent.mosaicCanvas.draw()
        self.Parent.mosaicCanvas.setImageExtent(extent2)
        
    def z_diff(self,p1,p2):
        """
        Calculates z diff between two points, maybe change this later to return a range of acceptable
        Z focus?
        """
        print "delta Z from p1 to p2 = ", p2-p1

            
    def NextImage(self,evt="None"): 
        #calls the real function 
        go = True

        #one way to stop, need a user input for number of slices
        counter = 0

        #another way, stop after each failure or number of consecutive failures? Maybe both since stopping anyways?
        
        acq_start = time.clock()

        #If user specified num_slices, use that, else no stop (default value = 0)
        stop = self.Parent.num_slices
##        print "STOP = ",stop

        #Acquire               
        while go:
            print "ROUND " + str(counter+1)
            if stop != 0:
                if counter == stop:
                    print "reached num_slices limit, stopping."
                    break
            go = self.AcquireNext()
##            dict_tmp = self.z_positions.copy() #Very roundabout way to store ordered dict pos and get last two entries
##            self.z_diff(dict_temp.popitem[1],dict_temp.popitem[1])
            counter += 1
        print "Total acq time = ",time.clock()-acq_start
        print "Number of rounds completed = ",counter
        

    def AcquireNext(self):
        #also might want to move this to MosaicImage
        #stop condition??
        
        #guess next tile from previous coordinates
        newpos=self.posList.new_position_after_step()
        if newpos == None:
            print "newpos false"
            return False
        
        print "newpos",newpos
        x3,y3,z3 = self.posList.pos2.x,self.posList.pos2.y,MM_AT.getXYZ()[2]
        print x3,y3,z3,"x3,y3,z3 ##############################################"
        
        #image capture, if true then successfully acquired image or found image in mosaic

        start_capt = time.clock()
        new_z = self.image_capture(x3,y3,z3)

        #Have to append z3 to current position in PosList
        self.posList.pos2.z = new_z
        print self.posList.pos2.x,self.posList.pos2.y,self.posList.pos2.z,"!@#$%"
        print "image_capture time = ",time.clock()-start_capt

        start_corr = time.clock()
        corr = self.cross_corr(window=self.Parent.win1)
        print "corr time = ",time.clock()-start_corr
    
  #################### ends here for now ############

        #if good match
        if corr:
            print "good match on first try with window=100"
            return True
        
        #if bad match AFTER extended window size correlation
        else:
            if self.Parent.num_searches > 1:
                start_corr300 = time.clock() 
                corr = self.cross_corr(self.Parent.win2) #how much window expansion here?
                print "corr 300 time = ", time.clock()-start_corr300
                if corr:
                    print "good match with window=300"
                    return True

                if self.Parent.num_searches > 2:
                    start_corr600 = time.clock()
                    corr = self.cross_corr(self.Parent.win3)
                    print "corr 600 time = ",time.clock()-start_corr600
                    if corr:
                        print "good match with windpow=600" 
                        return True
                    else:
                        print "Acquisition could not find the next tile, either complete or lost."
                        return
                        #ENABLE THIS IF YOU WANT SURROUNDING BOXES BY REMOVING THE RETURN.
                        print "going to boxes"
                            
                        box = self.surrounding_box() #autofocus on boxes? no for now.
                        z = MM_AT.getXYZ()[2]
                        for point in box:
                            print point,point[0],point[1],"POINTS FROM BOX"
                            img = self.image_capture(point[0],point[1],z)
                            corr = self.cross_corr(window=600)
                            if corr > .3:
                                print "found it here",
                                return True
                            #could remove the tile here if it's not good, but eh.
                            else: #probably should tell it to cross corr towards the middle box or else this is fairly usless..
                                print "no match, trying next tile in box"
                        #fail condition, what to do here?
                        print "no successful matches, game over, more testing required, your castle was overrun, go home, you lose, sciencefail."
                        return False
               
 
    def image_capture(self,x3,y3,z3):
        
        #check if x3,y3 is a point already in the mosaic using findhighrestile
        check = self.mosaicImage.findHighResImageFile(x3,y3)
        
        if check:
            print "point already in mosaic"
            #down to cross corr
            return check[1] #Z position of tile

        else:
            #grab next image from microscope
            MM_AT.setExposure(self.Parent.exposure)
            MM_AT.setXY(x3,y3)
            Acq.wait_XYstage() #for now these are fixed at time.sleep(.2) since it's been tricky to get the communication checks working
            MM_AT.setZ(z3)
            Acq.wait_Zstage()
            orig_pos = MM_AT.getXYZ()
            print "point not in current mosaic, acquiring new image"
            print "POS BEFORE AUTOFOCUS",MM_AT.getXYZ()
            MM_AT.setAutoShutter(0)
            MM_AT.setShutter(1)
                
            (num_steps,rough_size,fine_size) = self.Parent.focus_params
            print num_steps,rough_size,fine_size,"FOCUS PARAMS"
            #Acquire image
            (pos,score,im) = Acq.get(orig_pos,True,num_steps,rough_size,fine_size)
            
            print MM_AT.getXYZ(),"POS AFTER AUTOFOCUS"
            print pos,"pos from auto"
            MM_AT.setShutter(0)
            
            #create new dir for image, save im
            (x,y,z) = MM_AT.getXYZ()
            str_xyz = str((x,y,z))
            new_tiles = os.path.join(self.Parent.proj_folder,'new_tiles')
            newdir = os.path.join(new_tiles,str_xyz)
            os.mkdir(newdir)
            f_out = os.path.join(newdir,'img_%s_.tif' % str_xyz)
            im.save(f_out)
            
            #write new image metadata to file, fix pixel size, currently not grabbing right
            width,height,Pxsize,Xpos,Ypos,Zpos = im.size[0],im.size[1],.6,pos[0],pos[1],pos[2]
            d = {"Summary":{"Width":width,"Height":height,
                            "PixelSize_um":Pxsize},
                 "Frame":{"XPositionUm":Xpos,"YPositionUm":Ypos,"ZPositionUm":Zpos}}   
            meta = json.dumps(d)
            new_meta = open(os.path.join(newdir,'metadata.txt'),'w')
            new_meta.write(meta)
            new_meta.close()

            #calculating new extent and padding
            extent = self.mosaicImage.extent

            mosaic = self.Parent.LoadImage(os.path.join(self.Parent.proj_folder,'mosaic.tif'),False)[0]
            
            extent2 = self.mosaicImage.extendMosaicTiff(mosaic,f_out,self.Parent.LoadImage(f_out,True)[0],extent,self.Parent.scaling)
            
            #draw new image SHOULD IT BE FROM FILE OR FROM MEMORY?
            (image,small_height,small_width)=self.Parent.LoadImage(os.path.join(self.Parent.proj_folder,'mosaic.tif'),False)

            self.mosaicImage.updateImageCenter(np.reshape(np.array(image.getdata(),np.dtype('uint16')),(small_height,small_width)),self.mosaicImage.Image,self.mosaicImage.axis)
            self.Parent.mosaicCanvas.draw()
            self.Parent.mosaicCanvas.setImageExtent(extent2)


            print "THIS IS POSITION Z",pos[2]
            return pos[2]
        
##          except:
##              print "Unable to grab and process next image"
##              return False
##    
    def cross_corr(self,window=100):
        """
        Cross corr for MM
        """
        corrval=self.CorrTool(window=100,delta=75,skip=3)
        corrval=self.CorrTool(window=100,delta=75,skip=3) #doing this twice for now since corr is broken
        #if good match:
        if corrval > .3:
            return True
        else:
            return False
        
    def surrounding_box(self): #not first resort.
        """
        Generates box of surrounding tiles using pos2. Named p1 through p8, starting top left, going to the right and down a row, snake pattern (for now).
        """
        x,y = self.posList.pos2.x,self.posList.pos2.y
        width_um,height_um = self.mosaicImage.originalwidth*.6,self.mosaicImage.originalheight*.6

        #points in stage coords (microns)
        p1 = (x - width_um, y + height_um)
        p2 = (x, y + height_um)
        p3 = (x + width_um, y + height_um)
        p4 = (x + width_um, y)
        p5 = (x - width_um, y)
        p6 = (x - width_um, y - height_um)
        p7 = (x, y - height_um)
        p8 = (x + width_um, y - height_um)

        return [p1,p2,p3,p4,p5,p6,p7,p8]
        
          
class ZVISelectFrame(wx.Frame):
    """class extending wx.Frame for highest level handling of GUI components """
    ID_RELATIVEMOTION = wx.NewId()
    ID_EDIT_CAMERA_SETTINGS = wx.NewId()
    ID_EDIT_SMARTSEM_SETTINGS = wx.NewId()
    ID_EDIT_MM_SETTINGS = wx.NewId()
    ID_SORTPOINTS = wx.NewId()
    ID_SHOWNUMBERS = wx.NewId()
    ID_SAVETRANSFORM = wx.NewId()
    ID_EDITTRANSFORM = wx.NewId()
    ID_FLIPVERT = wx.NewId()
    
    def __init__(self, parent, title):     
        """default init function for a wx.Frame
        
        keywords:
        parent)parent window to associate it with
        title) title of the 
   
        """
        #default metadata info and image file, remove for release
        default_meta=""
        default_image=""
        default_proj=os.getcwd()
        default_conf="C:\Program Files\Micro-Manager-1.4_nightly.cfg"
        self.MM_FLAG = False
        print "default proj dir",default_proj

        #default MM Settings
        self.scaling = .1
        self.num_slices = 0 #MAKE FALSE OR -1 OR SOMETHING, SOME CHECK HERE, DEFAULT OFF!
        self.corr_coefficient = .3
        self.focus_params = (4,10,2)
        self.exposure = 150
        self.num_searches = 0
        self.win1 = 100
        self.win2 = 300
        self.win3 = 600

            
        
        
        #recursively call old init function
        wx.Frame.__init__(self, parent, title=title, size=(1400,885),pos=(5,5))
        
        #setup menu         
        menubar = wx.MenuBar()
        options = wx.Menu()   
        transformMenu = wx.Menu()
        SmartSEM_Menu = wx.Menu()
        MM_Menu = wx.Menu()
        
        #setup the menu options
        self.relative_motion = options.Append(self.ID_RELATIVEMOTION, 'Relative motion?', 'Move points in the ribbon relative to the apparent curvature, else in absolution coordinates',kind=wx.ITEM_CHECK)
        self.sort_points = options.Append(self.ID_SORTPOINTS,'Sort positions?','Should the program automatically sort the positions by their X coordinate from right to left?',kind=wx.ITEM_CHECK)
        self.show_numbers = options.Append(self.ID_SHOWNUMBERS,'Show numbers?','Display a number next to each position to show the ordering',kind=wx.ITEM_CHECK)
        self.flipvert = options.Append(self.ID_FLIPVERT,'Flip Image Vertically?','Display the image flipped vertically relative to the way it was meant to be displayed',kind=wx.ITEM_CHECK)
        options.Check(self.ID_RELATIVEMOTION,True) 
        options.Check(self.ID_SORTPOINTS,True)  
        options.Check(self.ID_SHOWNUMBERS,False)
        options.Check(self.ID_FLIPVERT,False)
        
        self.edit_transform = options.Append(self.ID_EDIT_CAMERA_SETTINGS,'Edit Camera Properties...','Edit the size of the camera chip and the pixel size',kind=wx.ITEM_NORMAL)
         
        self.Bind(wx.EVT_MENU, self.ToggleRelativeMotion, id=self.ID_RELATIVEMOTION)
        self.Bind(wx.EVT_MENU, self.ToggleSortOption, id=self.ID_SORTPOINTS)
        self.Bind(wx.EVT_MENU, self.ToggleShowNumbers,id=self.ID_SHOWNUMBERS)
        self.Bind(wx.EVT_MENU, self.EditCameraSettings, id=self.ID_EDIT_CAMERA_SETTINGS)
        
        self.save_transformed = transformMenu.Append(self.ID_SAVETRANSFORM,'Save Transformed?',\
        'Rather than save the coordinates in the original space, save a transformed set of coordinates according to transform configured in set_transform...',kind=wx.ITEM_CHECK)
        
        transformMenu.Check(self.ID_SAVETRANSFORM,False)
   
        self.edit_camera_settings = transformMenu.Append(self.ID_EDITTRANSFORM,'Edit Transform...',\
        'Edit the transform used to save transformed coordinates, by setting corresponding points and fitting a model',kind=wx.ITEM_NORMAL)
      
        self.Bind(wx.EVT_MENU, self.EditTransform, id=self.ID_EDITTRANSFORM)        
        
        self.edit_smartsem_settings = SmartSEM_Menu.Append(self.ID_EDIT_SMARTSEM_SETTINGS,'Edit SmartSEMSettings',\
        'Edit the settings used to set the magnification, rotation,tilt, Z position, and working distance of SEM software in position list',kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.EditSmartSEMSettings, id=self.ID_EDIT_SMARTSEM_SETTINGS)

        self.edit_MM_settings = MM_Menu.Append(self.ID_EDIT_MM_SETTINGS,'Edit MM Settings',\
        'Edit the settings used for Micro-Manager type acquisition',kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.Edit_MM_Settings, id=self.ID_EDIT_MM_SETTINGS)
        
        menubar.Append(options, '&Options')
        menubar.Append(transformMenu,'&Transform')
        menubar.Append(SmartSEM_Menu,'&Platform Options')
        menubar.Append(MM_Menu,'&MM Options')
        self.SetMenuBar(menubar)
        
        #setup a mosaic panel #############################
        self.mosaicCanvas=MosaicPanel(self)     
      
        #setup a file picker for the metadata selector
        self.meta_label=wx.StaticText(self,id=wx.ID_ANY,label="metadata file")
        self.meta_filepicker=wx.FilePickerCtrl(self,message='Select a metadata file',\
        path=default_meta,name='metadataFilePickerCtrl1',\
        style=wx.FLP_USE_TEXTCTRL, size=wx.Size(300,100),wildcard='*.*')
        self.meta_formatBox=wx.ComboBox(self,id=wx.ID_ANY,value='ZVI',\
        size=wx.DefaultSize,choices=['MM','ZVI','ZeissXML'], name='File Format For Meta Data')
        self.meta_formatBox.SetEditable(False)
        self.meta_filepicker.SetPath(default_meta)
        self.meta_load_button=wx.Button(self,id=wx.ID_ANY,label="Load",name="metadata load")
        self.meta_enter_button=wx.Button(self,id=wx.ID_ANY,label="Edit",name="manual meta")
        
        #define the image file picker components      
        self.image_label=wx.StaticText(self,id=wx.ID_ANY,label="image file")
        self.image_filepicker=wx.FilePickerCtrl(self,message='Select an image file',\
        path=default_image,name='imageFilePickerCtrl1',\
        style=wx.FLP_USE_TEXTCTRL, size=wx.Size(300,100),wildcard='*.tif')
        self.image_filepicker.SetPath(default_image)
        self.image_load_button=wx.Button(self,id=wx.ID_ANY,label="Load",name="image load")

        #define project folder for Micro-Manager project type
        self.proj_label=wx.StaticText(self,id=wx.ID_ANY,label="MM project folder")
        self.proj_folderpicker=wx.DirPickerCtrl(self,
            message='Select a project folder for your MM project',\
            path=default_proj,name='projectFolderPickerCtrl1',
            style=wx.FLP_USE_TEXTCTRL,size=wx.Size(300,100))
        self.proj_folderpicker.SetPath(default_proj)
        self.folder_create_button=wx.Button(self,id=wx.ID_ANY,label="Create",name="folder create")

        #define the microscope configuration file picker
        self.conf_label=wx.StaticText(self,id=wx.ID_ANY,label="Micromanager microscope config file")
        self.conf_filepicker=wx.FilePickerCtrl(self,message='Select a MM config file',\
        path=default_image,name='configFilePickerCtrl1',\
        style=wx.FLP_USE_TEXTCTRL, size=wx.Size(300,100),wildcard='*.cfg')
        self.conf_filepicker.SetPath(default_conf)
        self.config_load_button=wx.Button(self,id=wx.ID_ANY,label="Load",name="config load")
       
        #wire up the button to the "OnLoad" button
        self.Bind(wx.EVT_BUTTON, self.OnImageLoad,self.image_load_button)
        self.Bind(wx.EVT_BUTTON, self.OnMetaLoad,self.meta_load_button)
        self.Bind(wx.EVT_BUTTON, self.OnProjCreate,self.folder_create_button)
        self.Bind(wx.EVT_BUTTON, self.OnConfLoad,self.config_load_button)
        self.Bind(wx.EVT_BUTTON, self.OnEditImageMetadata,self.meta_enter_button)
        
       
        #define the array picker components 
        self.array_label=wx.StaticText(self,id=wx.ID_ANY,label="array file")
        self.array_filepicker=wx.FilePickerCtrl(self,message='Select an array file',\
        path="",name='arrayFilePickerCtrl1',\
        style=wx.FLP_USE_TEXTCTRL, size=wx.Size(300,100),wildcard='*.csv')
        self.array_load_button=wx.Button(self,id=wx.ID_ANY,label="Load",name="load button")
        self.array_formatBox=wx.ComboBox(self,id=wx.ID_ANY,value='AxioVision',\
        size=wx.DefaultSize,choices=['AxioVision','SmartSEM','OMX','MM'], name='File Format For Position List')
        self.array_formatBox.SetEditable(False)
        self.array_save_button=wx.Button(self,id=wx.ID_ANY,label="Save",name="save button")
        self.array_saveframes_button=wx.Button(self,id=wx.ID_ANY,label="Save Frames",name="save-frames button")
             
        #wire up the button to the "OnLoad" button
        self.Bind(wx.EVT_BUTTON, self.OnArrayLoad,self.array_load_button)
        self.Bind(wx.EVT_BUTTON, self.OnArraySave,self.array_save_button)
        self.Bind(wx.EVT_BUTTON, self.OnArraySaveFrames,self.array_saveframes_button)
        
        #define a horizontal sizer for them and place the file picker components in there
        self.meta_filepickersizer=wx.BoxSizer(wx.HORIZONTAL)
        self.meta_filepickersizer.Add(self.meta_label,0,wx.EXPAND)
        self.meta_filepickersizer.Add(self.meta_filepicker,1,wx.EXPAND)
        self.meta_filepickersizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="Metadata Format:"))
        self.meta_filepickersizer.Add(self.meta_formatBox,0,wx.EXPAND)
        self.meta_filepickersizer.Add(self.meta_load_button,0,wx.EXPAND)
        self.meta_filepickersizer.Add(self.meta_enter_button,0,wx.EXPAND)
        
        #define a horizontal sizer for them and place the file picker components in there
        self.image_filepickersizer=wx.BoxSizer(wx.HORIZONTAL)
        self.image_filepickersizer.Add(self.image_label,0,wx.EXPAND)
        self.image_filepickersizer.Add(self.image_filepicker,1,wx.EXPAND)        
        self.image_filepickersizer.Add(self.image_load_button,0,wx.EXPAND)

        #define a horizontal sizer for them and place the folder picker components in there
        self.proj_folderpickersizer=wx.BoxSizer(wx.HORIZONTAL)
        self.proj_folderpickersizer.Add(self.proj_label,0,wx.EXPAND)
        self.proj_folderpickersizer.Add(self.proj_folderpicker,1,wx.EXPAND)        
        self.proj_folderpickersizer.Add(self.folder_create_button,0,wx.EXPAND)

        #define a horizontal sizer for them and place the folder picker components in there
        self.conf_filepickersizer=wx.BoxSizer(wx.HORIZONTAL)
        self.conf_filepickersizer.Add(self.conf_label,0,wx.EXPAND)
        self.conf_filepickersizer.Add(self.conf_filepicker,1,wx.EXPAND)        
        self.conf_filepickersizer.Add(self.config_load_button,0,wx.EXPAND)
        
        #define a horizontal sizer for them and place the file picker components in there
        self.array_filepickersizer=wx.BoxSizer(wx.HORIZONTAL)
        self.array_filepickersizer.Add(self.array_label,0,wx.EXPAND)   
        self.array_filepickersizer.Add(self.array_filepicker,1,wx.EXPAND) 
        self.array_filepickersizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="Format:"))
        self.array_filepickersizer.Add(self.array_formatBox,0,wx.EXPAND)
        self.array_filepickersizer.Add(self.array_load_button,0,wx.EXPAND)
        self.array_filepickersizer.Add(self.array_save_button,0,wx.EXPAND)
        self.array_filepickersizer.Add(self.array_saveframes_button,0,wx.EXPAND)

        #define the overall vertical sizer for the frame
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        #place the filepickersizer into the vertical arrangement
        self.sizer.Add(self.image_filepickersizer,0,wx.EXPAND)
        self.sizer.Add(self.proj_folderpickersizer,0,wx.EXPAND)
        self.sizer.Add(self.conf_filepickersizer,0,wx.EXPAND)
        self.sizer.Add(self.meta_filepickersizer,0,wx.EXPAND)
        self.sizer.Add(self.array_filepickersizer,0,wx.EXPAND)
        self.sizer.Add(self.mosaicCanvas.get_toolbar(), 0, wx.LEFT | wx.EXPAND)
        self.sizer.Add(self.mosaicCanvas, 0, wx.EXPAND)
        
        #self.poslist_set=False
        #set the overall sizer and autofit everything
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyPress)
             
        #self.sizer.Fit(self)
        self.Show(True)
        
        self.Transform = Transform()
        self.SmartSEMSettings=SmartSEMSettings()
        self.MMSettings = MMSettings()
        #self.OnImageLoad()
        #self.OnArrayLoad()          
       # self.mosaicCanvas.draw()
           
    def OnKeyPress(self,event="none"):
        """forward the key press event to the mosaicCanvas handler"""
        self.mosaicCanvas.OnKeyPress(event)
     
    def OnArrayLoad(self,event="none"):
        """event handler for the array load button"""
        if self.array_formatBox.GetValue()=='AxioVision':
            self.mosaicCanvas.posList.add_from_file(self.array_filepicker.GetPath())          
        elif self.array_formatBox.GetValue()=='OMX':
            print "not yet implemented"    
        elif self.array_formatBox.GetValue()=='SmartSEM':
            SEMsetting=self.mosaicCanvas.posList.add_from_file_SmartSEM(self.array_filepicker.GetPath())
            self.SmartSEMSettings=SEMsetting
        elif self.array_formatBox.GetValue()=='MM':
            print "not implemented yet"
        self.mosaicCanvas.draw()
            
    def OnArraySave(self,event):
        """event handler for the array save button"""
        if self.array_formatBox.GetValue()=='AxioVision':
            if self.save_transformed.IsChecked():
                self.mosaicCanvas.posList.save_position_list(self.array_filepicker.GetPath(),trans=self.Transform)
            else:
                self.mosaicCanvas.posList.save_position_list(self.array_filepicker.GetPath())                
        elif self.array_formatBox.GetValue()=='OMX':
            if self.save_transformed.IsChecked():
                self.mosaicCanvas.posList.save_position_list_OMX(self.array_filepicker.GetPath(),trans=self.Transform);
            else:
                self.mosaicCanvas.posList.save_position_list_OMX(self.array_filepicker.GetPath(),trans=None);
        elif self.array_formatBox.GetValue()=='SmartSEM':
            if self.save_transformed.IsChecked():
                self.mosaicCanvas.posList.save_position_list_SmartSEM(self.array_filepicker.GetPath(),SEMS=self.SmartSEMSettings,trans=self.Transform)    
            else:
                self.mosaicCanvas.posList.save_position_list_SmartSEM(self.array_filepicker.GetPath(),SEMS=self.SmartSEMSettings,trans=None)
        elif self.array_formatBox.GetValue()=='MM':
            if self.save_transformed.IsChecked():
                self.mosaicCanvas.posList.save_position_list_MM(self.array_filepicker.GetPath()) #add transform support here later, update save pos function
            else:
                self.mosaicCanvas.posList.save_position_list_MM(self.array_filepicker.GetPath())
              
    def OnArraySaveFrames(self,event):   
        if self.array_formatBox.GetValue()=='AxioVision':
            if self.save_transformed.IsChecked():
                self.mosaicCanvas.posList.save_frame_list(self.array_filepicker.GetPath(),trans=self.Transform)  
            else:
                self.mosaicCanvas.posList.save_frame_list(self.array_filepicker.GetPath())       
                
        elif self.array_formatBox.GetValue()=='OMX':
            if self.save_transformed.IsChecked():
                self.mosaicCanvas.posList.save_frame_list_OMX(self.array_filepicker.GetPath(),trans=self.Transform);
            else:
                self.mosaicCanvas.posList.save_frame_list_OMX(self.array_filepicker.GetPath(),trans=None);
        elif self.array_formatBox.GetValue()=='SmartSEM':
            if self.save_transformed.IsChecked():
                self.mosaicCanvas.posList.save_frame_list_SmartSEM(self.array_filepicker.GetPath(),SEMS=self.SmartSEMSettings,trans=self.Transform)    
            else:
                self.mosaicCanvas.posList.save_frame_list_SmartSEM(self.array_filepicker.GetPath(),SEMS=self.SmartSEMSettings,trans=None)        
        elif self.array_formatBox.GetValue()=='MM':
            self.mosaicCanvas.posList.save_frame_list_MM(self.array_filepicker.GetPath())
    
    def GetXMLMetaFloatByIndex(self,dom,index):
        
        xmlTag = dom.getElementsByTagName('V%d'%index)[0].toxml()
        xmlData=xmlTag.replace("<V%d>"%index,'').replace("</V%d>"%index,'')
        xmlData=float(xmlData)
        return float(xmlData)
    
    def FindTag(self,tagnode,tagindex):
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
                    value= self.GetXMLMetaFloatByIndex(tagnode,index)
                    return value

            
    def LoadAxioVisionXMLMetaData(self,filename):
           
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
        xpos=self.FindTag(tagroot,2073)
        ypos=self.FindTag(tagroot,2074)
        ScaleFactorX=self.FindTag(tagroot,769)
        ScaleFactorY=self.FindTag(tagroot,772)
        Width=self.FindTag(tagroot,515)
        Height=self.FindTag(tagroot,516)
        extent=[xpos-(Width/2)*ScaleFactorX,xpos+(Width/2)*ScaleFactorX,\
                     ypos+(Height/2)*ScaleFactorY,ypos-(Height/2)*ScaleFactorY]
        print "loaded metadata from xml file, was detected to be: "
        print extent 
        return extent

    def LoadMMMetadata(self,filename):
        """retrieves and parses metadata from mm folder..."""
        
        file = open(filename,'r')
        data = file.read()
        file.close()
        data = data.replace("false","False")
        data = data.replace("true","True")
        data = data.replace("null","0")
##        print data
        f = eval(str(data))
        tiles = []
        for i in f.keys():
            if i != "Summary":
                tiles.append(i)
        xpos = f[tiles[0]]["XPositionUm"]
        ypos = f[tiles[0]]["YPositionUm"]
        ScaleFactorX= .6 #PixelSize_um??
        ScaleFactorY= .6 #?
        Width=f["Summary"]["Width"]
        Height=f["Summary"]["Height"]
        extent=[xpos-(Width/2)*ScaleFactorX,xpos+(Width/2)*ScaleFactorX,\
        ypos+(Height/2)*ScaleFactorY,ypos-(Height/2)*ScaleFactorY] #FOR NOW
        return extent
        
    def LoadZVIMetaData(self,filename):
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
     
    
    def sixteen2eightB(self,img16):
        """Converts 16 bit PIL image to 8 bit PIL image"""
        a = np.array(img16.getdata(),dtype='uint16')
        b=256.0*a/a.max()
        array8= np.reshape(b,(img16.size[1],img16.size[0]))
        img8 = Image.fromarray(array8)
        
        return img8
    
    
    def LoadImage(self,filename,scale=True):
        """function for loading images using PIL, returns a downsized PIL image
        
        keywords:
        filename)a string containing the path of image
        
        returns (image,small_height,small_width)
        image)returns a PIL image of the
        small_height)the height of the downsampled image
        small_width)the width of the downsampled image  
        
        """   
        image = Image.open(filename)
        (big_width,big_height)=image.size;
        if scale == True:
            print "scaling, ",filename
            rescale=self.scaling
            small_width=int(big_width*rescale)   
            small_height=int(big_height*rescale)       
            image=image.resize((small_width,small_height))
##            image.show()
            return (image,small_height,small_width)        
        elif scale == False:
            print "NOT scaling, ",filename
##            image.show()
            image_copy = image.copy()
            return (image_copy,big_height,big_width)    
        else:
            print "can't get here..?"

            
    def OnMetaLoad(self,evt):
        if self.meta_formatBox.GetValue()=='MM':
            extent=MetadataHandler.LoadMetadata(self.meta_filepicker.GetPath())
        if self.meta_formatBox.GetValue()=='ZVI':
            extent=self.LoadZVIMetaData(self.meta_filepicker.GetPath())
        if self.meta_formatBox.GetValue()=='ZeissXML':
            extent=self.LoadAxioVisionXMLMetaData(self.meta_filepicker.GetPath())
        self.mosaic = TrueCanvas.setImageExtent(extent)
                 
    def OnImageLoad(self,event="none"):
        """event handler for handling the Load button press"""
        #extent=self.LoadZVIMetaData(self.meta_filepicker.GetPath())
        filename=self.image_filepicker.GetPath()
        (image,small_height,small_width)=self.LoadImage(filename)
        try:
            proj_folder = self.Parent.proj_folder
        except:
            proj_folder = None
        self.mosaicCanvas.loadImage(image.getdata(),small_height,small_width,filename,proj_folder,flipVert=self.flipvert.IsChecked())
        self.mosaicCanvas.draw()
        self.meta_filepicker.SetPath(filename + "_meta.xml");
        self.array_filepicker.SetPath(os.path.splitext(self.meta_filepicker.GetPath())[0]+".tif-array.csv")

    def OnConfLoad(self,event="none"):
        """event handler for handling the Load button press for loading MM config file"""
        filename=str(self.conf_filepicker.GetPath())
        print filename
        print filename
        try:
            print "Loading MM config file"
            MM_AT.loadsysconf(filename)
            print "Successfully loaded config"
            print "Current stage position: ",MM_AT.getXYZ()
        except Exception,e:
            print "\n"
            print str(e)
            print ("Unable to load config file. Ensure that your components are powered on,\
                \nnot in use in another MosaicPlanner, Micro-Manager, or Axiovision instance,\
                \nand that your configuration file is valid.")

    def OnProjCreate(self,event="none"):
        """
        event handler for handling the Create button press. Creates subfolder called
        new_tiles where acquired images will be stored
        """
        self.proj_folder = self.proj_folderpicker.GetPath()
        if not os.path.exists(os.path.join(self.proj_folder,'new_tiles')):
            print "creating project folder"
            os.mkdir(os.path.join(self.proj_folder,'new_tiles'))
        else:
            print "folder already exists, can implement projecy loading here, but for now just sets dir?"

        #Toggle global MM_FLAG on, signals that and MM project is being worked on
        self.MM_FLAG = True
             
    def ToggleRelativeMotion(self,event):
        """event handler for handling the toggling of the relative motion"""  
        if self.relative_motion.IsChecked():
            self.mosaicCanvas.relative_motion=(True)
        else:
            self.mosaicCanvas.relative_motion=(False)   
    def ToggleSortOption(self,event):
        """event handler for handling the toggling of the relative motion"""  
        if self.sort_points.IsChecked():
            self.mosaicCanvas.posList.dosort=(True)
        else:
            self.mosaicCanvas.posList.dosort=(False)
            
    def ToggleShowNumbers(self,event):
        if self.show_numbers.IsChecked():
            self.mosaicCanvas.posList.setNumberVisibility(True)
        else:
            self.mosaicCanvas.posList.setNumberVisibility(False)
        self.mosaicCanvas.draw()
            
            
    def EditCameraSettings(self,event):
        """event handler for clicking the camera setting menu button"""
        dlg = ChangeCameraSettings(None, -1,
                                   title="Camera Settings",
                                   settings=self.mosaicCanvas.camera_settings)
        dlg.ShowModal()
        del self.posList.camera_settings
        #passes the settings to the position list
        self.mosaicCanvas.posList.set_camera_settings(dlg.GetSettings())
        dlg.Destroy()

    def EditSmartSEMSettings(self,event):
        dlg = ChangeSEMSettings(None, -1,
                                   title="Smart SEM Settings",
                                   settings=self.SmartSEMSettings)
        dlg.ShowModal()
        del self.SmartSEMSettings
        #passes the settings to the position list
        self.SmartSEMSettings=dlg.GetSettings()
        dlg.Destroy()
            
        
    def EditTransform(self,event):
        """event handler for clicking the edit transform menu button"""
        dlg = ChangeTransform(None, -1,title="Adjust Transform")
        dlg.ShowModal()
        #passes the settings to the position list
        (pts_from,pts_to,transformType,flipVert,flipHoriz)=dlg.GetTransformInfo()
        print transformType
        self.Transform.set_transform_by_fit(pts_from,pts_to,mode=transformType,flipVert=flipVert,flipHoriz=flipHoriz)
        for index,pt in enumerate(pts_from):
            (xp,yp)=self.Transform.transform(pt.x,pt.y)
            print("%5.5f,%5.5f -> %5.5f,%5.5f (%5.5f, %5.5f)"%(pt.x,pt.y,xp,yp,pts_to[index].x,pts_to[index].y))
        dlg.Destroy()
        
        
    def OnEditImageMetadata(self,event):
        dlg = ChangeImageMetadata(None,-1,title="Image Metadata",settings=ImageSettings(extent=self.mosaicCanvas.mosaicImage.extent))
        dlg.ShowModal()
        self.mosaicCanvas.setImageExtent(dlg.GetSettings().extent)
        
    def Edit_MM_Settings(self,event):
        dlg = ChangeMMSettings(None, -1,
                                   title="MM Settings",
                                   settings=self.MMSettings)
        dlg.ShowModal()
        del self.MMSettings
        #then do corrosponding stuff here..
        self.MMSettings=dlg.GetSettings()

        #set MM settings
        self.scaling = self.MMSettings.scaling
        self.num_slices = self.MMSettings.num_slices
        self.corr_coefficient = self.MMSettings.corr_coefficient
        self.focus_params = self.MMSettings.focus_params
        self.exposure = self.MMSettings.exposure
        self.num_searches = self.MMSettings.num_searches
        self.win1 = self.MMSettings.win1
        self.win2 = self.MMSettings.win2
        self.win3 = self.MMSettings.win3
        
        dlg.Destroy()
        return
    
#dirname=sys.argv[1]
#print dirname

app = wx.App(False)  
# Create a new app, don't redirect stdout/stderr to a window.
frame = ZVISelectFrame(None,"Mosaic Planner")
##frame.LoadMMMetadata("d:\User_Data\Administrator\Desktop\mm\New Folder\DAPI TEST_plain 10x_1\Pos0\metadata.txt")

# A Frame is a top-level window.
app.MainLoop()
MM_AT.unload_devices()
print "Unloaded all devices"
