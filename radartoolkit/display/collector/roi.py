#!/usr/bin.env python

"""
    Demonstrates a variety of regions-of-interest. 
    It is possible to customize the layout and function of the scale/rotate handles in very flexible ways. 
"""

from typing import Optional
import PySide6.QtCore
import PySide6.QtWidgets
from ..settings import RIGHT_ARROW
from ..bindings import QtSignal, QtCore, QtSlot, QtWidgets
from ..utils.check_class import check_class
import numpy as np
import pyqtgraph as pg
from pyqtgraph.graphicsItems.PlotItem import PlotItem
import logging


logger = logging.getLogger(__name__)

class RoiWidget(pg.GraphicsLayoutWidget):
    """ Region-of-interest viewer, one for better to discover the details,
        the other is to prevent from being crashed for the big chunk of data.
    """
    sigRoiRegionChanged = QtSignal(int)

    def __init__(self, parent=None, defaultSliceStep=1000, 
                 defaultMaximumChunkSize=50000):
        """ Constructor.
            ::param defaultSliceStep: default value for the slice size of the roi, can be resized.
            ::param defaultMaximumChunkSize: the maximum value before downsampling.
        """
        super(RoiWidget, self).__init__(parent)

        self.setBackground("white")
        self.scaleStep = 1

        # default value
        self._defaultSliceStep = defaultSliceStep
        self._defaultMaximumChunkSize = defaultMaximumChunkSize

        self.roiItem = PlotItem()
        viewBox = self.roiItem.getViewBox()
        viewBox.invertY(True)
        viewBox.setMouseEnabled(x=False, y=False)
        viewBox.setAspectLocked(True)
        viewBox.setBorder(pg.mkPen("#DDDDDD"))

        print("viewRect: {}".format(viewBox.viewRect()))
        self.imageItem = pg.ImageItem()
        self.imageItem.setPos(-0.5, -0.5)
        self.roiItem.addItem(self.imageItem)

        rois = []
        rois.append(pg.LinearRegionItem(brush=pg.mkBrush('#FFF8DC')))
        rois.append(pg.TestROI([0, 0], [20, 20], maxBounds=QtCore.QRectF(-10, -10, 230, 140), pen=pg.mkPen(0, 9)))
        self._rois = rois
        self._roiConifg = {'linear-roi': True, 'rect-roi': True}
        self._roi = self._rois[0]

        self.addItem(self.roiItem)
        self.show()

    @property
    def defaultSliceStep(self):
        return self._defaultSliceStep
    
    @property
    def defaultMaximumChunkSize(self):
        return self._defaultMaximumChunkSize

    def _createRoi(self, data, dimNr=1,
                   sliceStep=None, maximumChunkSize=None):
        """ initialize to create roi region """
        if not sliceStep:
            sliceStep = self.defaultSliceStep
        if not maximumChunkSize:
            maximumChunkSize = self.defaultMaximumChunkSize

        if data.shape[dimNr] > maximumChunkSize:
            _data, _step = self.downSampleData(data, dimNr)
        else:
            _data, _step = data, 1
        self.scaleStep = _step
        
        # setup roi
        self.imageItem.setImage(_data.T)
        self.imageItem.setRect(0, 0, 34370, 3437)
        self.imageItem.setColorMap(pg.colormap.get('CET-L12')) # CET-L8
        self.roiItem.addItem(self._roi)
        
        self._roi.setClipItem(self.roiItem)
        self._roi.sigRegionChanged.connect(self.updateRoiRegion)
        
    def downSampleData(self, data=None, dimNr=1):
        """ default: dimNr = 1 """
        check_class(data, np.ndarray, allow_none=False)

        step = data.shape[dimNr] // (data.shape[dimNr-1] * 10)
        data = data[:, 0:data.shape[dimNr]:step]
        return step, data
    
    def updateRoiRegion(self, roi):
        if roi is None:
            return

        minValue, maxValue = roi.getRegion()
        valueMax = int((np.trunc(maxValue)+np.trunc(minValue))//2) # center value
        self.sigRoiRegionChanged.emit(valueMax) # emit the signal

    def _clearContents(self):
        self.imageItem.clear()



class roiPlots(QtWidgets.QWidget):

    def __init__(self, label, parent=None):
        super(roiPlots, self).__init__(parent=parent)

        self._checkBox = QtWidgets.QCheckBox()
        self._checkBox.setEnabled(False)
        self._label = QtWidgets.QLabel(label)
        
        hLayout = QtWidgets.QHBoxLayout(self)
        hLayout.setSpacing(10)
        hLayout.setContentsMargins(0, 0, 0, 0)
        hLayout.setAlignment(QtCore.Qt.AlignCenter)
        
        hLayout.addWidget(self._checkBox)
        hLayout.addWidget(self._label)

        



        


