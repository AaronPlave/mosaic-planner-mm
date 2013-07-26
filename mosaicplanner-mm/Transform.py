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
 
import numpy as np
from numpy import sin, pi, cos, arctan, sin, tan, sqrt
from Point import Point
import wx.lib.intctrl
import wx.lib.agw.floatspin    
import csv

class Transform():
    """class for storing, applying and fitting linear transformations of 2d points"""
    def __init__(self,matrix=None,disp_vector=None,flipVert=False,flipHoriz=False):

        if not matrix == None:
            self.T=matrix
        else:
            self.T=np.array([[1,0],[0,1]])
        
        if not disp_vector == None:
            self.D=disp_vector
        else:
            self.D=np.array([0,0])
        
        self.flipVert=flipVert;
        self.flipHoriz=flipHoriz;
        
    def transform(self,x,y):
        if self.flipVert:
            y=-y
        if self.flipHoriz:
            x=-x
        vec=np.array([x,y])
        vec_t=np.dot(self.T,vec);
        vec_t=vec_t+self.D;
        return (vec_t[0],vec_t[1])
        
    def set_transform_by_fit(self,from_pts,to_pts,mode='similarity',flipVert=False,flipHoriz=False):
        """set_transform_by_fit(x1,y1,x2,y2,mode='similarity')
        keywords:
        from_pts) a list of Point objects from the original space that correspond in a 1-1 way with the Points in to_pts
        to_pts) a list of Point objects from the new space that correspond in a 1-1 way with the Points in from_pts
        mode) whether these corresponding points should be fit using a 'translation','rigid','similarity' or 'affine' transformation
        'translation' only shifts them in x and y
        'rigid' does translation plus rotation
        'similarity' does rigid plus a scaling factor which is equal in x and y
        'affine' does a fully linear transformation
        default is similarity
        """
        self.flipVert=flipVert
        self.flipHoriz=flipHoriz
        
        if mode=='similarity':
            # Fill the matrices
            A_data = []
            for pt in from_pts:
              if flipVert:
                y=-pt.y
              else:
                y=pt.y
              
              if flipHoriz:
                x=-pt.x
              else:
                x=pt.x
              A_data.append( [-y, x, 1, 0] )
              A_data.append( [ x, y, 0, 1] )

            b_data = []
            for pt in to_pts:
              b_data.append(pt.x)
              b_data.append(pt.y)

            # Solve
            A = np.matrix( A_data )
            b = np.matrix( b_data ).T
            c = np.linalg.lstsq(A, b)[0].T
            c = np.array(c)[0]

            print("Solved coefficients:")
            print(c)

            self.T=[[c[1],-c[0]],[c[0],c[1]]]
            self.D=[c[2],c[3]]
            
        if mode=='translation':
            A_data = []
            for pt in from_pts:
                if flipVert:
                    y=-pt.y
                else:
                    y=pt.y
              
                if flipHoriz:
                    x=-pt.x
                else:
                    x=pt.x
                
                A_data.append( [1, 0] )
                A_data.append( [0, 1] )
            
            b_data = []
            for index,pt in enumerate(to_pts):
                if flipVert:
                    y=-from_pts[index].y
                else:
                    y=from_pts[index].y
              
                if flipHoriz:
                    x=-from_pts[index].x
                else:
                    x=from_pts[index].x
                b_data.append(pt.x-x)
                b_data.append(pt.y-y)    
            
            A = np.matrix( A_data )
            b = np.matrix( b_data ).T
            c = np.linalg.lstsq(A, b)[0].T
            c = np.array(c)[0]
            
            self.T=[[1,0],[0,1]]
            self.D=[c[0],c[1]]
            
            
class ChangeTransform(wx.Dialog):
    """simple dialog for changing the camera settings"""
    def __init__(self, parent, id, title, transform=None):
        wx.Dialog.__init__(self, parent, id, title, size=(600, 120))
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)  
        
        self.corresp_label=wx.StaticText(self,id=wx.ID_ANY,label="Correspondance file")
        self.corresp_filepicker=wx.FilePickerCtrl(self,message='Select file with corresponding points list (xf0,yf0,xt0,yt0 \\n xf1,yf1,xt1,yt1\n ...)',\
        path="",name='correspondancePicker',\
        style=wx.FLP_USE_TEXTCTRL, size=wx.Size(200,20),wildcard='*.csv')
        self.corresp_load_button=wx.Button(self,id=wx.ID_ANY,label="Load",name="load correspondance files")
                                         
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.corresp_label,1)
        hbox.Add(self.corresp_filepicker,4, wx.EXPAND)
        hbox.Add(self.corresp_load_button, 1, wx.EXPAND)
      
        self.transtypeBox=wx.ComboBox(self,id=wx.ID_ANY,value='similarity', size=wx.DefaultSize,
           choices=['similarity','rigid','translation','affine'], name='Transformation Type Name')
        self.transtypeBox.SetEditable(False)
        self.flipHoriz = wx.CheckBox(self)
        self.flipVert = wx.CheckBox(self)
        self.flipHoriz.SetValue(False)
        self.flipVert.SetValue(False)
        
        
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(wx.StaticText(self,id=wx.ID_ANY,label="Transformation Type:"))
        hbox2.Add(self.transtypeBox,border=5);
        hbox2.Add(wx.StaticText(self,id=wx.ID_ANY,label="Vertical flip:"))
        hbox2.Add(self.flipVert)
        hbox2.Add(wx.StaticText(self,id=wx.ID_ANY,label="Horizontal flip:"))
        hbox2.Add(self.flipHoriz)
        #vbox.Add(hbox,1,wx.EXPAND)
        
        vbox.Add(hbox, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        vbox.Add(hbox2,1, wx.ALIGN_RIGHT,5)
        self.SetSizer(vbox)

        self.Bind(wx.EVT_BUTTON, self.OnCorrespLoad,self.corresp_load_button)

    def OnCorrespLoad(self,evt):
        filename=self.corresp_filepicker.GetPath()
        coorespReader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='#')
        headerline = coorespReader.next()
        pts_from=[]
        pts_to=[]
        for row in coorespReader:
            if len(row)==4:
                (xf,yf,xt,yt)=row
                print row
                pts_from.append(Point(float(xf),float(yf)))
                pts_to.append(Point(float(xt),float(yt)))
                
        self.pts_from=pts_from
        self.pts_to=pts_to

    def GetTransformInfo(self):
        return (self.pts_from,self.pts_to,self.transtypeBox.GetValue(),self.flipHoriz.GetValue(),self.flipVert.GetValue())
        
