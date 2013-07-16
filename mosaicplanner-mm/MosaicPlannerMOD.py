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
from Settings import MosaicSettings, CameraSettings, ChangeCameraSettings, ImageSettings, ChangeImageMetadata, SmartSEMSettings, ChangeSEMSettings
from PositionList import posList
from MyLasso import MyLasso
from MosaicImage import MosaicImage
from Transform import Transform,ChangeTransform
from xml.dom.minidom import parseString
import wx
import MetadataHandler
import MM_AT_MOD as MM_AT
import time
import json
from PIL import Image

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
    ON_NEWPOINT = wx.NewId()
    ON_DELETE_SELECTED = wx.NewId()
    #ON_CORR_LEFT = wx.NewId()
    ON_STEP = wx.NewId()
    ON_FF = wx.NewId()
    ON_LOADIMG = wx.NewId()
    ON_NEXT = wx.NewId()
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
        self.corrTool=self.AddSimpleTool(self.ON_CORR,corrBmp,'Ajdust pointLine2D 2 with correlation','corrTool') 
        self.stepTool=self.AddSimpleTool(self.ON_STEP,stepBmp,'Take one step using points 1+2','stepTool')     
        self.ffTool=self.AddSimpleTool(self.ON_FF,ffBmp,'Auto-take steps till C<.3 or off image','fastforwardTool')       
        self.loadimages=self.AddSimpleTool(self.ON_LOADIMG,ffBmp,'Load Images')
        self.nextimage=self.AddSimpleTool(self.ON_NEXT,corrBmp,'Acquire new images automatically')
        
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
        wx.EVT_TOOL(self, self.ON_CORR, self.canvas.OnCorrTool)        
        wx.EVT_TOOL(self, self.ON_STEP, self.canvas.OnStepTool)           
        wx.EVT_TOOL(self, self.ON_FF, self.canvas.OnFastForwardTool)
        wx.EVT_TOOL(self, self.ON_LOADIMG, self.canvas.ButtonLoad) ################################################     
        wx.EVT_TOOL(self, self.ON_NEXT, self.canvas.NextImage) ################################################ 
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
                    elif (mode == 'add'): 
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
        """handlier for handling the Delete tool press"""
        self.posList.delete_selected()
        self.draw()
        
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
        self.subplot.set_xlim(self.mosaicImage.extent[0],self.mosaicImage.extent[1])
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
                    #if this fails a second time, lets assume that this point 2 is a messed up one and skip it
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
        
        self.posList.pos2.shiftPosition(-dx_um,dy_um) #watch out for this shi(f)t.. gets weird
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

    def loadImage(self,imagedata,height,width,tif_filename,extent=None,flipVert=False):
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
        self.mosaicImage=MosaicImage(self.subplot,self.posone_plot,self.postwo_plot,self.corrplot,tif_filename,imagematrix,extent,flipVert=flipVert)
       
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
        (image,small_height,small_width)=self.Parent.LoadImage(filename)

        #set extent
        old_mosaic = self.Parent.LoadImage('C:\Users\Aaron\Desktop\mosaic.tif')
        new_extent = self.mosaicImage.extendMosaicTiff(old_mosaic[0],filename,image,old_extent)

        (new_mosaic,small_height,small_width)=self.Parent.LoadImage('C:\Users\Aaron\Desktop\mosaic.tif')
        new_mosaic = self.sixteen2eight(new_mosaic)
        
        #update canvas
        self.mosaicImage.updateImageCenter(np.reshape(np.array(new_mosaic.getdata(),np.dtype('uint16')),(small_height,small_width)),self.mosaicImage.Image,self.mosaicImage.axis)
        self.Parent.mosaicCanvas.draw()
        self.Parent.mosaicCanvas.setImageExtent(new_extent)
        return new_extent

    def ButtonLoad(self,evt="None"):
        #open the first image
        default_image=""
        openfiledialog = wx.FileDialog(self,"Open Image File","","","*.tif",wx.FD_OPEN)
        if openfiledialog.ShowModal() == wx.ID_CANCEL:
            return
        self.image_filepicker1 = openfiledialog.GetPath()

        #calculate extent from metadata
        extent = MetadataHandler.LoadMetadata(self.image_filepicker1)
        (image,small_height,small_width)=self.Parent.LoadImage(self.image_filepicker1)
        image = self.sixteen2eight(image)
        
        #draw first image
        print "Loading first image..."
        self.Parent.mosaicCanvas.loadImage(image.getdata(),small_height,small_width,self.image_filepicker1,flipVert=self.Parent.flipvert.IsChecked())
        self.Parent.mosaicCanvas.draw()
        self.Parent.mosaicCanvas.setImageExtent(extent)


        #open the second image
        default_image=""
        openfiledialog = wx.FileDialog(self,"Open Image File","","","*.tif",wx.FD_OPEN)
        if openfiledialog.ShowModal() == wx.ID_CANCEL:
            return
        self.image_filepicker2 = openfiledialog.GetPath()

        #IMAGE 2
        extent2 = self.mosaicImage.extendMosaicTiff(self.Parent.LoadImage(self.image_filepicker1)[0],self.image_filepicker2,self.Parent.LoadImage(self.image_filepicker2)[0],extent)

        #draw new image SHOULD IT BE FROM FILE OR FROM MEMORY?
        (image,small_height,small_width)=self.Parent.LoadImage('C:\Users\Aaron\Desktop\mosaic.tif')
        image = self.sixteen2eight(image)
        
        self.mosaicImage.updateImageCenter(np.reshape(np.array(image.getdata(),np.dtype('uint16')),(small_height,small_width)),self.mosaicImage.Image,self.mosaicImage.axis)
        self.Parent.mosaicCanvas.draw()
        self.Parent.mosaicCanvas.setImageExtent(extent2)
        #Rest of images

        files = ['C:\Users\Aaron\Desktop\mosaic-planner-mm\mosaicplanner-mm\Testfiles\images\\1-Pos_001_000\img_000000000_DAPI_000.tif',
                 'C:\Users\Aaron\Desktop\mosaic-planner-mm\mosaicplanner-mm\Testfiles\images\\1-Pos_001_001\img_000000000_DAPI_000.tif']

  ##        self.newImage(extent2,files[0])

        old_extent = extent2
        for f in files:
            old_extent = self.newImage(old_extent,f)

            
    def NextImage(self,evt="None"):
        #calls the real function
        go = True
        counter = 0
        while go:
            if counter == 5:
                print "reached counter limit"
                break
            go = self.AcquireNext()
            counter += 1
            
        print "finished"
        
    def AcquireNext(self):
        #also might want to move this to MosaicImage
        #stop condition??
        #check for/make dir for next images
        print "ANOTHER ROUND OF ACQUIRE NEXT"
        if not os.path.exists('C:\\Program Files\Micro-Manager-1.4_32\\new_tiles'):
            os.mkdir('new_tiles') #HAVE TO ADD THIS DIR TO findHighResImageFIle CHECKING?
            
        #guess next tile from previous coordinates
        for i in self.posList.slicePositions: print i.x,i.y
        newpos=self.posList.new_position_after_step()
        if newpos == None:
            print "newpos false"
            return False
##        x1,y1 = self.posList.slicePositions[0].x,self.posList.slicePositions[0].y
##        x2,y2 = self.posList.slicePositions[1].x,self.posList.slicePositions[1].y
        x3,y3 = self.posList.pos2.x,self.posList.pos2.y
        print x3,y3,"x3,y3"

        #image capture and corr
        corr = self.image_capture_and_corr(x3,y3)

        #if good match
        if corr:
            return True

        #if bad match
        else:
            box = self.surrounding_three()
            for point in box:
                corr = self.image_capture_and_corr(point[0],point[1])
                if corr > .3:
                    return True
                #could remove the tile here if it's not good, but eh.
                print "no match, trying next tile in box"
            #fail condition, what to do here?
            print "no successful matches, game over, your castle was overrun, go home, you lose, sciencefail."
            return False
            

    def image_capture_and_corr(self,x3,y3):
        #check if x3,y3 is a point already in the mosaic using findhighrestile
        check = self.mosaicImage.findHighResImageFile(x3,y3)

        
        if check:
            print check
            print "point already in mosaic"
            #down to cross corr
            corr = self.cross_corr()

        else:
            print "point outside of current mosaic, acquiring new tile"
            #acquire next tile
            MM_AT.setExposure(100)
            MM_AT.setXY(x3,y3)
            
            time.sleep(3) #look at demo to see how image capture is waited for
            img16 = MM_AT.snapImage() #need to add autofocus support!! Should it autofocus after failure? maybe depending on sharpness of failed image?
            time.sleep(2)
            
            #convert to 8 bit, different from the normal function since not from file
            a = img16[0]
            print a,type(a)
            b=256.0*a/a.max()
            array8= np.reshape(b,(img16[2],img16[1]))
            img8 = Image.fromarray(array8)
##            img8.show()
            newdir = 'C:\\Program Files\\Micro-Manager-1.4_32\\new_tiles\\'+str(x3)+str(y3)
            os.mkdir(newdir)
            f_out = newdir+'\\'+'img_000000000_DAPI_000.tif'
            img8.save(f_out)
            
            #write new image metadata to file
            width,height,Pxsize,Xpos,Ypos = img16[1],img16[2],\
                                            MM_AT.get_property("PixelSize_um"),\
                                            x3,y3
            d = {"Summary":{"Width":width,"Height":height,
                            "PixelSize_um":Pxsize},
                 "Frame":{"XPositionUm":Xpos,"YPositionUm":Ypos}}   
            meta = json.dumps(d)
            new_meta = open(newdir+'\\'+'metadata.txt','w')
            new_meta.write(meta)
            new_meta.close()
            
            #add new image to mosaic
            print self.mosaicImage.extent
            print newdir+'\\'+'metadata.txt'
            self.newImage(self.mosaicImage.extent,newdir+'\\'+'img_000000000_DAPI_000.tif')
            
            #cross correllate new tile with last position
            corr = self.cross_corr()
            
        return corr
    
    def cross_corr(self):
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
        #if bad match:
            #take tiles surrounding point, i.e. increase search range
            #manual intervention?
            #say screw it and come back to the point later?  

    def surrounding_three(self):
        """
        Generates box of surrounding tiles using pos2. Named p1 through p8, starting top left, going to the right and down a row, snake pattern (for now).
        """
        x,y = self.posList.pos2.x,self.posList.pos2.y
        width_um,height_um = self.mosaicImage.originalwidth*.6,self.mosaicImage.originalheight*.6

        #points in stage coords (microns)
        p1 = (x - width_um, y + height_um)
        p2 = (x, y + height_um)
        p3 = (x + width_um + height_um)
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
        
        #recursively call old init function
        wx.Frame.__init__(self, parent, title=title, size=(1400,885),pos=(5,5))
        
        #setup menu         
        menubar = wx.MenuBar()
        options = wx.Menu()   
        transformMenu = wx.Menu()
        SmartSEM_Menu = wx.Menu()
        
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
        
        menubar.Append(options, '&Options')
        menubar.Append(transformMenu,'&Transform')
        menubar.Append(SmartSEM_Menu,'&Platform Options')
        self.SetMenuBar(menubar)
        
        #setup a mosaic panel #############################
        self.mosaicCanvas=MosaicPanel(self)     
      
        #setup a file picker for the metadata selector
        self.meta_label=wx.StaticText(self,id=wx.ID_ANY,label="metadata file")
        self.meta_filepicker=wx.FilePickerCtrl(self,message='Select a metadata file',\
        path=default_meta,name='metadataFilePickerCtrl1',\
        style=wx.FLP_USE_TEXTCTRL, size=wx.Size(300,100),wildcard='*.*')
        self.meta_formatBox=wx.ComboBox(self,id=wx.ID_ANY,value='MM',\
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
        
       
        #wire up the button to the "OnLoad" button
        self.Bind(wx.EVT_BUTTON, self.OnImageLoad,self.image_load_button)
        self.Bind(wx.EVT_BUTTON, self.OnMetaLoad,self.meta_load_button)
        self.Bind(wx.EVT_BUTTON, self.OnEditImageMetadata,self.meta_enter_button)
        
       
        #define the array picker components 
        self.array_label=wx.StaticText(self,id=wx.ID_ANY,label="array file")
        self.array_filepicker=wx.FilePickerCtrl(self,message='Select an array file',\
        path="",name='arrayFilePickerCtrl1',\
        style=wx.FLP_USE_TEXTCTRL, size=wx.Size(300,100),wildcard='*.csv')
        self.array_load_button=wx.Button(self,id=wx.ID_ANY,label="Load",name="load button")
        self.array_formatBox=wx.ComboBox(self,id=wx.ID_ANY,value='AxioVision',\
        size=wx.DefaultSize,choices=['AxioVision','SmartSEM','OMX'], name='File Format For Position List')
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
        print "loaded metadata from xml file, extent was detected to be: "
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
    
    
    def LoadImage(self,filename):
        """function for loading images using PIL, returns a downsized PIL image
        
        keywords:
        filename)a string containing the path of image
        
        returns (image,small_height,small_width)
        image)returns a PIL image of the
        small_height)the height of the downsampled image
        small_width)the width of the downsampled image
        
        """   
        image = self.sixteen2eightB(Image.open(filename))
        (big_width,big_height)=image.size;
        rescale=1 #CHANGED THIS TO 1 FROM 10, CAN CHANGE BACK BUT HAVE TO WORK IT INTO PADDING
        small_width=big_width/rescale   
        small_height=big_height/rescale       
        image=image.resize((small_width,small_height))  
        return (image,small_height,small_width)        
    
    
    def OnMetaLoad(self,evt):
        if self.meta_formatBox.GetValue()=='MM':
            extent=MetadataHandler.LoadMetadata(self.meta_filepicker.GetPath())
        if self.meta_formatBox.GetValue()=='ZVI':
            extent=self.LoadZVIMetaData(self.meta_filepicker.GetPath())
        if self.meta_formatBox.GetValue()=='ZeissXML':
            extent=self.LoadAxioVisionXMLMetaData(self.meta_filepicker.GetPath())
        self.mosaicCanvas.setImageExtent(extent)
                 
    def OnImageLoad(self,event="none"):
        """event handler for handling the Load button press"""
        #extent=self.LoadZVIMetaData(self.meta_filepicker.GetPath())
        filename=self.image_filepicker.GetPath()
        (image,small_height,small_width)=self.LoadImage(filename)
        self.mosaicCanvas.loadImage(image.getdata(),small_height,small_width,filename,flipVert=self.flipvert.IsChecked())
        self.mosaicCanvas.draw()
        self.meta_filepicker.SetPath(filename + "_meta.xml");
        self.array_filepicker.SetPath(os.path.splitext(self.meta_filepicker.GetPath())[0]+".tif-array.csv")
 
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
        
 
#dirname=sys.argv[1]
#print dirname

app = wx.App(False)  
# Create a new app, don't redirect stdout/stderr to a window.
frame = ZVISelectFrame(None,"Mosaic Planner")
##frame.LoadMMMetadata("d:\User_Data\Administrator\Desktop\mm\New Folder\DAPI TEST_plain 10x_1\Pos0\metadata.txt")

# A Frame is a top-level window.
app.MainLoop()
