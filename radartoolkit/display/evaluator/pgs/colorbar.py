#!/usr/bin.env python

""" Module that contains RTKPgColorBar.
"""

from ...bindings import QtCore, QtWidgets, QtSignal, QtGui
from ...utils.check_class import check_class

import pyqtgraph as pg
from pgcolorbar.colorlegend import ColorLegendItem
import logging, warnings

logger = logging.getLogger(__name__)

warnings.filterwarnings(action='default', category=RuntimeWarning, module='pgcolorbar.colorlegend')  # Show once


class RTKColorLegendItem(ColorLegendItem):
    """ Wrapper around pgcolorbar.colorlegend.ColorLegendItem.

        Suppresses the FutureWarning of PyQtGraph in _updateHistogram.
        Overrides the _imageItemHasIntegerData method.
        Adds context menu with reset color scale action.
        Middle mouse click resets the axis with the settings in the config tree.
    """
    # Use a QueuedConnection to connect to sigResetColorScale so that the reset is scheduled after
    # all current events have been processed. Otherwise the mouseReleaseEvent may look for a
    # PlotCurveItem that is no longer present after the reset, which results in a RuntimeError:
    # wrapped C/C++ object of type PlotCurveItem has been deleted.
    sigResetColorScale = QtSignal()  # Signal the inspectors to reset the color scale

    def __init__(self, *args, histHeightPercentile=99.0, **kwargs):
        """ Constructor
        """
        # 20230927 22:43 zjy histogram hiding problem need to be checked!!!
        super(RTKColorLegendItem, self).__init__(
            *args, showHistogram=False, histHeightPercentile=histHeightPercentile, **kwargs)
        self.resetColorScaleAction = QtGui.QAction("Reset Color Range", self)
        self.resetColorScaleAction.triggered.connect(self.emitResetColorScaleSignal)
        self.resetColorScaleAction.setToolTip("Reset the range of the color scale.")
        self.addAction(self.resetColorScaleAction)
        

    @classmethod
    def _imageItemHasIntegerData(cls, imageItem):
        """ Returns True if the imageItem contains integer data.

            Overriden so that the ImagePlotItem can replace integer arrays with float arrays (to
            plot masked values as NaNs) while it still calculates the histogram bins as if it
            where integers (to prevent aliasing)
        """
        check_class(imageItem, pg.ImageItem, allow_none=True)

        if hasattr(imageItem, '_wasIntegerData'):
            return imageItem._wasIntegerData
        else:
            return super(RTKColorLegendItem, cls)._imageItemHasIntegerData(imageItem)
        

    def emitResetColorScaleSignal(self):
        """ Emits the sigColorScaleReset to request the inspectors to reset the color scale
        """
        logger.debug("Emitting sigColorScaleReset() for {!r}".format(self))
        self.sigResetColorScale.emit()


    def mouseClickEvent(self, mouseClickEvent):
        """ Handles (PyQtGraph) mouse click events.

            Overrides the middle mouse click to reset using the settings in the config tree.

            Opens the context menu if a right mouse button was clicked. (We can't simply use
            setContextMenuPolicy(Qt.ActionsContextMenu because the PlotItem class does not derive
            from QWidget).

            :param mouseClickEvent: pyqtgraph.GraphicsScene.mouseEvents.MouseClickEvent
        """
        if mouseClickEvent.button() in self.resetRangeMouseButtons:
            self.emitResetColorScaleSignal()
            mouseClickEvent.accept()

        elif mouseClickEvent.button() == QtCore.Qt.RightButton:
            contextMenu = QtWidgets.QMenu()
            for action in self.actions():
                contextMenu.addAction(action)

            screenPos = mouseClickEvent.screenPos()  # Screenpos is a QPointF, convert to QPoint.
            screenX = round(screenPos.x())
            screenY = round(screenPos.y())
            contextMenu.exec_(QtCore.QPoint(screenX, screenY))

        else:
            super(RTKColorLegendItem, self).mouseClickEvent(mouseClickEvent)

