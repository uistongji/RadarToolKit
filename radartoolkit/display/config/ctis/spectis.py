#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# This code is part of package RadarToolKit (RTK).
# 
# RadarToolKit (RTK) manages the track, view, processing, analysis and simulation of radargrams, 
# e.g., impulse and chirp. The distributed version focuses on the chirped system utilized in Antarctica,
# namely the ice sounding radar (ISR). Therefore RTK currently is also called as RadarToolKit (ISR).
#
# RTK is distributed in the hope that it would be helpful for
# the users that needs to generate paper-like image results,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# You should have received a copy of the GNU General Public License
# together with the RadarToolKit (ISR): https://github.com/uistongji/RadarToolKit
#
# AUTHOR: Chen Lv (supervisor: Tong Hao), Tongji University


""" Special configuration tree items for use in collector (spectis).
"""

from .groupcti import MainGroupCti, GroupCti
from .choicecti import ChoiceCti
from .floatcti import SnFloatCti, FloatCti
from .boolcti import BoolCti
from .intcti import IntCti



class ColProcCti(MainGroupCti):
    """ 
    Processing Parameters Tree Widget for the Collector.
    """

    def __init__(self, collector=None, nodeName='', expanded=True):
        """ 
        Constructor

        Maintains a link to the target collector, so that changes in the
        configuration can be applied to the target by simply calling the apply method.
        Vice versa, it can connect signals to the target.
        """

        super(ColProcCti, self).__init__(nodeName, expanded)
        self.collector = collector # assumed it's already sanity checked

        # --- Radar Stream --- #
        self.radarCti = self.insertChild(StreamCti())
        
        # --- Range --- #
        self.ranProcCti = self.insertChild(RangeProcCti())

        # --- Azimuth/Along-track --- #
        self.aziProcCti = self.insertChild(AziProcCti('azimuth (along-track)'))

        # --- Cross-track --- #
        self.crossProcCti = self.insertChild(GroupCti('cross-track'))

        # --- Presentation --- #
        self.presentCti = self.insertChild(GroupCti('present'))
        self.presentCti.insertChild(AxisYUnitCti())
        self.presentCti.insertChild(AxisXUnitCti())

        # --- ROI --- #
        self.roiCti = self.insertChild(RoiCti())


class StreamCti(ChoiceCti):
    """ Config Tree Item to store a choice between strings.
        A QCombobox will pop-up if the user clicks on the cell to edit it.
        
        :: StreamCti can auto-detect the t 
    """
    def __init__(self, nodeName='stream', 
                 defaultData=0, editable=True, 
                 configValues=["auto-detect", "RADnh3", "RADnh5", "unsorted"]):
        super(StreamCti, self).__init__(nodeName, defaultData, configValues, editable=editable)



############
#   PROC   #
############

class RangeProcCti(GroupCti):
    """ Read only config Tree Item that only stores None. It can be used to group CTIs of range.
    """
    def __init__(self, nodeName='range', expanded=True):
        super(RangeProcCti, self).__init__(nodeName, expanded=expanded)

        self.inputSamplesCti = self.insertChild(
            IntCti(nodeName='input', defaultData=3200, minValue=0))
        self.outputSamplesCti = self.insertChild(
            IntCti(nodeName='output', defaultData=3200, minValue=0))
        
        self.dechirpCti = self.insertChild(
            GroupCti(nodeName='dechirp', expanded=True))
        self.dechirpCti.insertChild(
            IntCti('blanking', defaultData=0,
                   minValue=0, maxValue=self.inputSamplesCti.data))
        self.dechirpCti.insertChild(BoolCti('bandpass', defaultData=True))
        self.dechirpCti.insertChild(
            ChoiceCti('windowing', 0, editable=True,
                      configValues=["-- none --", 'hamming window']))
        

class AziProcCti(GroupCti):
    """ Read only config Tree Item that only stores None. It can be used to group CTIs of azimuth.
    """
    def __init__(self, nodeName='azimuth', expanded=True):
        super(AziProcCti, self).__init__(nodeName, expanded=expanded)

        self.cohCti = self.insertChild(
            BoolCti('coherent stacking', False))
        self.cohCti.insertChild(IntCti('depth', defaultData=5, minValue=1, maxValue=500))
        self.cohCti.insertChild(ChoiceCti('method', configValues=["presum", "center"]))

        self.incohCti = self.insertChild(
            BoolCti('incoherent stacking', False))
        self.incohCti.insertChild(IntCti('depth', defaultData=10, minValue=1, maxValue=500))
        self.incohCti.insertChild(ChoiceCti('method', configValues=["presum", "center"]))
        


##############
#  AXIS UNIT #
##############
    
class AxisYUnitCti(GroupCti):
    """ Configuration tree item that is linked to the range axis unit label.
    """ 
    def __init__(self, nodeName='y-axis', expanded=True):
        """ Constructor.
        """
        super(AxisYUnitCti, self).__init__(nodeName, expanded=expanded)

        # range interval: dt = 1/fs
        self.dtSpacingCti = self.insertChild(
            SnFloatCti("dt", minValue=0, maxValue=1, precision=3, 
                       specialValueText='auto-detect'))
        self.outputSamplesCti = self.insertChild(
            IntCti("output samples", defaultData=3200, minValue=1))
        
        # TWTT -> Depth in the range direction
        self.unitCti = self.insertChild(
            BoolCti("time2depth", False, expanded=True))
        self.unitCti.insertChild(
            IntCti("air-ice bin", minValue=0, 
                   maxValue=self.outputSamplesCti.defaultData,
                   specialValueText='auto-detect'))
        self.unitCti.insertChild(
            FloatCti("relative permittivity", defaultData=3.15,
                     minValue=0, maxValue=81))
        

class AxisXUnitCti(GroupCti):
    """ Configuration tree item that is linked to the range axis unit label.
    """
    def __init__(self, nodeName='x-axis', expanded=True):
        super(AxisXUnitCti, self).__init__(nodeName, expanded=expanded) 

        # along-track interval: dx = v/PRF
        self.dxSpacingCti = self.insertChild(
            FloatCti("dx", minValue=0, stepSize=0.1,
                     specialValueText='auto-detect'))



##############
#  PRESENT   #
##############

class RoiCti(GroupCti):
    """ ROI: Region of intereset to be discovered
    """
    def __init__(self, nodeName='roi', expanded=False):
        """ Constructor.
        """
        super(RoiCti, self).__init__(nodeName, expanded=expanded)

        self.setpCti = self.insertChild(IntCti("step", defaultData=1, minValue=1, maxValue=10))

        self.insertChild(IntCti("spacing", defaultData=1, minValue=1, 
                                stepSize=self.setpCti.defaultData))



