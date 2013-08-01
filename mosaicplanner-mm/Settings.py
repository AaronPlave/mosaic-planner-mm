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
import wx

class CameraSettings():
    """simple struct for containing the parameters for the camera"""
    def __init__(self,sensor_height=1388,sensor_width=1040,pix_width=6.5,pix_height=6.5):
        #in pixels        
        self.sensor_height=sensor_height
        self.sensor_width=sensor_width
        #in microns
        self.pix_width=pix_width
        self.pix_height=pix_height

class MMSettings():
    """simple struct for conatining the parameters for MM acquisition"""
    def __init__(self,scaling=.1,num_slices=0,corr_coefficient=.3,focus_params=(4,10,2),
                 exposure=150,num_searches=3,win1=100,win2=300,win3=600,search_params=False,boxes=False):
        self.scaling = scaling
        self.num_slices = num_slices

        #Bool to enable or disable box search, should be off by default, use for very curvy ribbon
        self.boxes = boxes
        
        self.corr_coefficient = corr_coefficient

        #not yet implemented
        self.num_searches = num_searches

        #list/dict mapping each search (one through three for now) to individual parameters like window size
        self.search_params = search_params

        #tuple of required focus params = # steps for each focus, rough step size, fine step size
        self.focus_params = focus_params

        self.exposure = exposure

        self.win1 = win1
        self.win2 = win2
        self.win3 = win3
        
    def update_settings(self,settings):
        """updates object with new settings from file, given in MosaicPlanner"""
        self.scaling = settings['scaling']
        self.num_slices = settings['num_slices']
        self.corr_coefficient = settings['corr_coefficient']
        self.num_searches = settings['num_searches']
        self.focus_params = settings['focus_params']
        self.exposure = settings['exposure']
        self.win1 = settings['win1']
        self.win2 = settings['win2']
        self.win3 = settings['win3']
        
class MosaicSettings:
    def __init__(self,mag=65.486,mx=1,my=1,overlap=10,show_box=False,show_frames=False):
        """a simple struct class for encoding settings about mosaics
        
        keywords)
        mag=magnification of objective
        mx=integer number of columns in a rectangular mosaic
        my=integer number of rows in a rectangular mosaic
        overlap=percentage overlap of individual frames (0-100)
        show_box=boolean as to whether to display the box
        show_frames=Boolean as to whether to display the individual frames
        
        """
        self.mx=mx
        self.my=my
        self.overlap=overlap
        self.show_box=show_box
        self.show_frames=show_frames
        self.mag=mag
        
  
class ChangeCameraSettings(wx.Dialog):
    """simple dialog for changing the camera settings"""
    def __init__(self, parent, id, title, settings):
        wx.Dialog.__init__(self, parent, id, title, size=(230, 210))
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)       
        self.widthIntCtrl=wx.lib.intctrl.IntCtrl( panel, value=settings.sensor_width,pos=(95,5),size=( 90, -1 ) )
        self.heightIntCtrl=wx.lib.intctrl.IntCtrl( panel, value=settings.sensor_height,pos=(95,35),size=( 90, -1 ) )
        self.pixwidthFloatCtrl=wx.lib.agw.floatspin.FloatSpin(panel, pos=(95,65),size=( 90, -1 ),
                                       value=settings.pix_width,
                                       min_val=0.1,
                                       max_val=100,
                                       increment=.1,
                                       digits=2,
                                       name='pix_width')
        self.pixheightFloatCtrl=wx.lib.agw.floatspin.FloatSpin(panel, pos=(95,95),size=( 90, -1 ),
                                       value=settings.pix_height,
                                       min_val=0.1,
                                       max_val=100,
                                       increment=.1,
                                       digits=2,
                                       name='pix_height')                             
                                         
        wx.StaticText(panel,id=wx.ID_ANY,label="Width (pixels)",pos=(5,8))
        wx.StaticText(panel,id=wx.ID_ANY,label="Height (pixels)",pos=(5,38))  
        wx.StaticText(panel,id=wx.ID_ANY,label="Pixel Width (um)",pos=(5,68))  
        wx.StaticText(panel,id=wx.ID_ANY,label="Pixel Height (um)",pos=(5,98)) 
                                         
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, wx.ID_OK, 'Ok', size=(70, 30))
       # closeButton = wx.Button(self, wx.ID_CLOSE, 'Close', size=(70, 30))
        hbox.Add(okButton, 1)
        #hbox.Add(closeButton, 1, wx.LEFT, 5)
        vbox.Add(panel)
        vbox.Add(hbox, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        self.SetSizer(vbox)
    def GetSettings(self):
        """extracts the Camera Settings from the controls"""
        return CameraSettings(sensor_width=self.widthIntCtrl.GetValue(),
                              sensor_height=self.heightIntCtrl.GetValue(),
                              pix_width=self.pixwidthFloatCtrl.GetValue(),
                              pix_height=self.pixheightFloatCtrl.GetValue())

class ChangeMMSettings(wx.Dialog):
    """Settings for MM acquisition"""
    def __init__(self, parent, id, title, settings):
        wx.Dialog.__init__(self, parent, id, title, size=(700, 700))
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)       

        self.scalingFloatCtrl=wx.lib.agw.floatspin.FloatSpin(panel, pos=(260,5),size=( 90, -1 ),
                                       value=settings.scaling,
                                       min_val=0.0,
                                       max_val=1.0,
                                       increment=.05,
                                       digits=2,
                                       name='scaling')
        self.numSlicesIntCtrl=wx.lib.intctrl.IntCtrl( panel, value=settings.num_slices,pos=(260,35),size=( 90, -1 ) )

        self.corr_coefficientIntCtrl=wx.lib.agw.floatspin.FloatSpin(panel, pos=(260,65),size=( 90, -1 ),
                                       value=settings.corr_coefficient,
                                       min_val=0.0,
                                       max_val=1.0,
                                       increment=.05,
                                       digits=2,
                                       name='corr_coefficient')
        
        self.stepsIntCtrl=wx.lib.intctrl.IntCtrl( panel, value=settings.focus_params[0],pos=(260,95),size=( 90, -1 ) )
        self.roughDistIntCtrl=wx.lib.intctrl.IntCtrl( panel, value=settings.focus_params[1],pos=(260,125),size=( 90, -1 ) )
        self.fineDistIntCtrl=wx.lib.intctrl.IntCtrl( panel, value=settings.focus_params[2],pos=(260,155),size=( 90, -1 ) )
        self.ExposureIntCtrl=wx.lib.intctrl.IntCtrl( panel, value=settings.exposure,pos=(260,185),size=( 90, -1 ) )
        self.num_searchesIntCtrl=wx.lib.intctrl.IntCtrl( panel, value=settings.num_searches,pos=(260,215),size=( 90, -1 ) )
        self.win1IntCtrl=wx.lib.intctrl.IntCtrl( panel, value=settings.win1,pos=(260,245),size=( 90, -1 ) )
        self.win2IntCtrl=wx.lib.intctrl.IntCtrl( panel, value=settings.win2,pos=(260,275),size=( 90, -1 ) )
        self.win3IntCtrl=wx.lib.intctrl.IntCtrl( panel, value=settings.win3,pos=(260,305),size=( 90, -1 ) )
                                 
        wx.StaticText(panel,id=wx.ID_ANY,label="Scaling (0-1)",pos=(5,8))
        wx.StaticText(panel,id=wx.ID_ANY,label="Number of positions (optional)",pos=(5,38))  
        wx.StaticText(panel,id=wx.ID_ANY,label="Cross corr coefficient (0-1)",pos=(5,68))  
        wx.StaticText(panel,id=wx.ID_ANY,label="Number of steps for each focus",pos=(5,98)) 
        wx.StaticText(panel,id=wx.ID_ANY,label="Rough step size (Um)",pos=(5,128))
        wx.StaticText(panel,id=wx.ID_ANY,label="Fine step size (Um)",pos=(5,158))
        wx.StaticText(panel,id=wx.ID_ANY,label="Exposure (ms)",pos=(5,188))
        wx.StaticText(panel,id=wx.ID_ANY,label="Number of searches (1-3)",pos=(5,218))
        wx.StaticText(panel,id=wx.ID_ANY,label="Window size of search one",pos=(5,248))
        wx.StaticText(panel,id=wx.ID_ANY,label="Window size of search two",pos=(5,278))
        wx.StaticText(panel,id=wx.ID_ANY,label="Window size of search three",pos=(5,308))
        
        #ADD BOXES OPTION
        #
        #ADD SEARCH PARAMS OPTION FOR 1-3rd SEARCHES
        

                                         
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, wx.ID_OK, 'Ok', size=(70, 30))
       # closeButton = wx.Button(self, wx.ID_CLOSE, 'Close', size=(70, 30))
        hbox.Add(okButton, 1)
        #hbox.Add(closeButton, 1, wx.LEFT, 5)
        vbox.Add(panel)
        vbox.Add(hbox, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        self.SetSizer(vbox)
        
    def GetSettings(self):
        """extracts the Camera Settings from the controls"""
        return MMSettings(scaling=self.scalingFloatCtrl.GetValue(),
                              num_slices=self.numSlicesIntCtrl.GetValue(),
                              corr_coefficient=self.corr_coefficientIntCtrl.GetValue(),
                              focus_params=(self.stepsIntCtrl.GetValue(),
                              self.roughDistIntCtrl.GetValue(),
                              self.fineDistIntCtrl.GetValue()),
                              exposure=self.ExposureIntCtrl.GetValue(),
                              num_searches=self.num_searchesIntCtrl.GetValue(),
                              win1=self.win1IntCtrl.GetValue(),
                              win2=self.win2IntCtrl.GetValue(),
                              win3=self.win3IntCtrl.GetValue()
                              )
        
class ImageSettings():
    def __init__(self,extent=[0,10,10,0]):
        self.extent=extent
        
class ChangeImageMetadata(wx.Dialog):
    """simple dialog for edchanging the camera settings"""
    def __init__(self, parent, id, title, settings=ImageSettings()):
        wx.Dialog.__init__(self, parent, id, title, size=(230, 210))
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)       
        self.minXIntCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.extent[0],pos=(125,5),size=( 90, -1 ),increment=1,digits=2 )
        self.maxXIntCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.extent[1],pos=(125,35),size=( 90, -1 ),increment=1,digits=2 )
        self.minYIntCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.extent[3],pos=(125,65),size=( 90, -1 ),increment=1,digits=2 )
        self.maxYIntCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.extent[2],pos=(125,95),size=( 90, -1 ),increment=1,digits=2 )
                                                           
        wx.StaticText(panel,id=wx.ID_ANY,label="Minimum X (um)",pos=(5,8))
        wx.StaticText(panel,id=wx.ID_ANY,label="Maximum X (um)",pos=(5,38))  
        wx.StaticText(panel,id=wx.ID_ANY,label="Minimum Y (um) (bottom)",pos=(5,68))  
        wx.StaticText(panel,id=wx.ID_ANY,label="Maximum Y (um) (top)",pos=(5,98)) 
                                         
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, wx.ID_OK, 'Ok', size=(70, 30))
       # closeButton = wx.Button(self, wx.ID_CLOSE, 'Close', size=(70, 30))
        hbox.Add(okButton, 1)
        #hbox.Add(closeButton, 1, wx.LEFT, 5)
        vbox.Add(panel)
        vbox.Add(hbox, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        self.SetSizer(vbox)
    def GetSettings(self):
        """extracts the Camera Settings from the controls"""
        return ImageSettings(extent=[self.minXIntCtrl.GetValue(),
                                     self.maxXIntCtrl.GetValue(),
                                     self.maxYIntCtrl.GetValue(),
                                     self.minYIntCtrl.GetValue()])
        

class SmartSEMSettings():
    def __init__(self,mag=1200,tilt=0.33,rot=0,Z=0.0125,WD=0.00632568):
        self.mag=mag
        self.tilt=tilt
        self.rot=rot
        self.Z=Z
        self.WD=WD
        
class ChangeSEMSettings(wx.Dialog):
    """simple dialog for edchanging the camera settings"""
    def __init__(self, parent, id, title, settings=SmartSEMSettings()):
        wx.Dialog.__init__(self, parent, id, title, size=(230, 210))
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)       
        self.magCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.mag,pos=(125,5),size=( 90, -1 ),increment=100,digits=2 )
        self.tiltCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.tilt,pos=(125,35),size=( 90, -1 ),increment=1,digits=4 )
        self.rotCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.rot,pos=(125,65),size=( 90, -1 ),increment=1,digits=4 )
        self.ZCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.Z,pos=(125,95),size=( 90, -1 ),increment=1,digits=4 )
        self.WDCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.WD,pos=(125,125),size=( 90, -1 ),increment=1,digits=4 )
        
        wx.StaticText(panel,id=wx.ID_ANY,label="magnification (prop. area)",pos=(5,8))
        wx.StaticText(panel,id=wx.ID_ANY,label="tilt (radians)",pos=(5,38))  
        wx.StaticText(panel,id=wx.ID_ANY,label="rotation (radians)",pos=(5,68))  
        wx.StaticText(panel,id=wx.ID_ANY,label="Z location (mm)",pos=(5,98))
        wx.StaticText(panel,id=wx.ID_ANY,label="WD working distance? (mm)",pos=(5,128))
        
                                         
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, wx.ID_OK, 'Ok', size=(70, 30))
       # closeButton = wx.Button(self, wx.ID_CLOSE, 'Close', size=(70, 30))
        hbox.Add(okButton, 1)
        #hbox.Add(closeButton, 1, wx.LEFT, 5)
        vbox.Add(panel)
        vbox.Add(hbox, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        self.SetSizer(vbox)
    def GetSettings(self):
        """extracts the Camera Settings from the controls"""
        return SmartSEMSettings(mag=self.magCtrl.GetValue(),
                                     tilt=self.tiltCtrl.GetValue(),
                                     rot=self.rotCtrl.GetValue(),
                                     Z=self.ZCtrl.GetValue(),
                                     WD=self.WDCtrl)
                                     
