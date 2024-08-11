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


""" Configuration Tree Items for use in PyQtGraph-based inspectors.
"""


from .groupcti import GroupCti
from .abstractcti import AbstractCti, AbstractCtiEditor
from .boolcti import BoolCti, BoolGroupCti
from .choicecti import ChoiceCti
from .intcti import IntCti
from .floatcti import FloatCti, SnFloatCti
from .untypedcti import UntypedCti
from .qtctis import PenCti, ColorCti, createPenStyleCti, createPenWidthCti
from ...color.colors import CmLibModelSingleton, DEFAULT_COLOR_MAP
from ..utils import setWidgetSizePolicy
from ...utils.mask import _subsampleArray, _maskedNanPercentile
from ...bindings import QtGui, QtWidgets, QtSlot

from functools import partial
from collections import OrderedDict

from cmlib import ColorSelectionWidget, ColorMap, makeColorBarPixmap
from cmlib import CmMetaData, CatalogMetaData

import logging
import numpy as np
import pyqtgraph as pg
from pyqtgraph.graphicsItems.GradientEditorItem import Gradients as GRADIENTS

logger = logging.getLogger(__name__)

X_AXIS = pg.ViewBox.XAxis
Y_AXIS = pg.ViewBox.YAxis
BOTH_AXES = pg.ViewBox.XYAxes
VALID_AXIS_NUMBERS = (X_AXIS, Y_AXIS, BOTH_AXES)
VALID_AXIS_POSITIONS = ('left', 'right', 'bottom', 'top')
NO_LABEL_STR = '-- none --'


class ViewBoxDebugCti(GroupCti):
    """ Read-only config tree for inspecting a pyqtgraph viewbox.
    """

    def __init__(self, nodeName, viewBox, expanded=False):

        super(ViewBoxDebugCti, self).__init__(nodeName, expanded=expanded)

        self.viewBox = viewBox

        self.insertChild(UntypedCti("targetRange", [[0, 1], [0, 1]],
                                    doc="Child coord. range visible [[xmin, xmax], [ymin, ymax]]"))

        self.insertChild(UntypedCti("viewRange", [[0, 1], [0, 1]],
                                    doc="Actual range viewed"))

        self.insertChild(UntypedCti("xInverted", None))
        self.insertChild(UntypedCti("yInverted", None))
        self.insertChild(UntypedCti("aspectLocked", False,
                                    doc="False if aspect is unlocked, otherwise float specifies the locked ratio."))
        self.insertChild(UntypedCti("autoRange", [True, True],
                                    doc="False if auto range is disabled, otherwise float gives the fraction of data "
                                        "that is visible"))
        self.insertChild(UntypedCti("autoPan", [False, False],
                                    doc="Whether to only pan (do not change scaling) when auto-range is enabled"))
        self.insertChild(UntypedCti("autoVisibleOnly", [False, False],
                                    doc="Whether to auto-range only to the visible portion of a plot"))
        self.insertChild(UntypedCti("linkedViews", [None, None],
                                    doc="may be None, 'viewName', or weakref.ref(view) a name string indicates that "
                                        "the view *should* link to another, but no view with that name exists yet."))
        self.insertChild(UntypedCti("mouseEnabled", [None, None]))
        self.insertChild(UntypedCti("mouseMode", None))
        self.insertChild(UntypedCti("enableMenu", None))
        self.insertChild(UntypedCti("wheelScaleFactor", None))
        self.insertChild(UntypedCti("background", None))

        self.limitsItem = self.insertChild(GroupCti("limits"))
        self.limitsItem.insertChild(UntypedCti("xLimits", [None, None],
                                               doc="Maximum and minimum visible X values "))
        self.limitsItem.insertChild(UntypedCti("yLimits", [None, None],
                                               doc="Maximum and minimum visible Y values"))
        self.limitsItem.insertChild(UntypedCti("xRange", [None, None],
                                               doc="Maximum and minimum X range"))
        self.limitsItem.insertChild(UntypedCti("yRange", [None, None],
                                               doc="Maximum and minimum Y range"))

    def _refreshNodeFromTarget(self):
        """ Updates the config settings
        """
        for key, value in self.viewBox.state.items():
            if key != "limits":
                childItem = self.childByNodeName(key)
                childItem.data = value
            else:
                # limits contains a dictionary as well
                for limitKey, limitValue in value.items():
                    limitChildItem = self.limitsItem.childByNodeName(limitKey)
                    limitChildItem.data = limitValue


def viewBoxAxisRange(viewBox, axisNumber):
    """ Calculates the range of an axis of a viewBox.
    """
    rect = viewBox.childrenBoundingRect()  # taken from viewBox.autoRange()
    if rect is not None:
        if axisNumber == X_AXIS:
            return rect.left(), rect.right()
        elif axisNumber == Y_AXIS:
            return rect.bottom(), rect.top()
        else:
            raise ValueError("axisNumber should be 0 or 1, got: {}".format(axisNumber))
    else:
        # Does this happen? Probably when the plot is empty.
        raise AssertionError("No children bbox. Plot range not updated.")


def inspectorDataRange(inspector, percentage, subsample):
    """ Calculates the range from the inspectors' sliced array. Discards percentage of the minimum
        and percentage of the maximum values of the inspector.slicedArray

        Meant to be used with functools.Partial for filling the autorange methods combobox.
        The first parameter is an inspector, it's not an array, because we would then have to
        regenerate the range function every time sliced array of an inspector changes.
    """
    # logger.debug("Discarding {}% from id: 0x{:08x}".format(percentage, id(inspector.slicedArray)))

    return nanPercentileOfSubsampledArrayWithMask(
        inspector.slicedArray, (percentage, 100 - percentage), subsample)
    pass


def nanPercentileOfSubsampledArrayWithMask(arrayWithMask, percentiles, subsample, *args, **kwargs):
    """ Sub samples the array and then calls maskedNanPercentile on this.

        If subsample is False, no sub sampling is done. And it just calls maskedNanPercentile
    """

    maskedArray = arrayWithMask.asMaskedArray()

    if subsample:
        maskedArray = _subsampleArray(maskedArray)

    return _maskedNanPercentile(maskedArray, percentiles, *args, **kwargs)


def defaultAutoRangeMethods(inspector, intialItems=None):
    """ Creates an ordered dict with default autorange methods for an inspector.

        :param inspector: the range methods will work on (the sliced array) of this inspector.
        :param intialItems: will be passed on to the  OrderedDict constructor.
    """
    rangeFunctions = OrderedDict({} if intialItems is None else intialItems)
    rangeFunctions['use all data'] = partial(inspectorDataRange, inspector, 0.0)
    for percentage in [0.1, 0.2, 0.5, 1, 2, 5, 10, 20]:
        label = "discard {}%".format(percentage)
        rangeFunctions[label] = partial(inspectorDataRange, inspector, percentage)
    return rangeFunctions


def setXYAxesAutoRangeOn(commonCti, xAxisRangeCti, yAxisRangeCti, axisNumber):
    """ Turns on the auto range of an X and Y axis simultaneously.
        It sets the autoRangeCti.Data of the xAxisRangeCti and yAxisRangeCti to True.
        After that, it emits the sigItemChanged signal of the commonCti.

        Can be used with functools.Partial to make a slot that atomically resets the X and Y axis.
        That is, only one sigItemChanged will be emitted.

        This function is necessary because, if one would call PgAxisRangeCti.sigItemChanged
        separately on the X and Y axes the sigItemChanged signal would be emitted twice. This in
        not only slower, but autoscaling one axis may slightly change the others range, so the
        second call to sigItemChanged may unset the autorange of the first.

        axisNumber must be one of: 0 (X-axis), 1 (Y-axis), 2, (Both X and Y axes).
    """
    assert axisNumber in VALID_AXIS_NUMBERS, \
        "Axis number should be one of {}, got {}".format(VALID_AXIS_NUMBERS, axisNumber)

    logger.debug("setXYAxesAutoRangeOn, axisNumber: {}".format(axisNumber))
    if axisNumber == X_AXIS or axisNumber == BOTH_AXES:
        xAxisRangeCti.autoRangeCti.data = True

    if axisNumber == Y_AXIS or axisNumber == BOTH_AXES:
        yAxisRangeCti.autoRangeCti.data = True

    commonCti.model.sigItemChanged.emit(commonCti)


class AbstractRangeCti(GroupCti):
    """ Configuration tree item is linked to a target range.

        Is an abstract class. Descendants must override getTargetRange and setTargetRange
    """

    def __init__(self, autoRangeFunctions=None, nodeName='range',
                 expanded=False, paddingDefault=-1):
        """ Constructor.
            The target axis is specified by viewBox and axisNumber (0 for x-axis, 1 for y-axis)

            If given, autoRangeMethods must be a (label to function) dictionary that will be used
            to populate the (auto range) method ChoiceCti.
            If autoRangeFunctions is None, there will be no auto-range child CTI.
            If autoRangeFunctions has one element there will be an auto-range child without a method
            child CTI (the function from the autoRangeMethods dictionary will be the default).

            :param int paddingDefault: default padding value. Use -1 for 'dynamic' padding, which
                is the PyQtGraph padding algorithm.
        """
        super(AbstractRangeCti, self).__init__(nodeName, expanded=expanded)

        self._rangeFunctions = {}
        self.autoRangeCti = None
        self.methodCti = None
        self.subsampleCti = None
        self.paddingCti = None

        if autoRangeFunctions is not None:
            self.autoRangeCti = self.insertChild(BoolCti("auto-range", True, expanded=False))
            self._rangeFunctions = autoRangeFunctions

        if len(autoRangeFunctions) > 1:
            self.methodCti = ChoiceCti("method", configValues=list(autoRangeFunctions.keys()))
            self.autoRangeCti.insertChild(self.methodCti)

            self.subsampleCti = BoolCti("subsample", True)
            self.autoRangeCti.insertChild(self.subsampleCti)

        self.paddingCti = IntCti("padding", paddingDefault,
                                 suffix="%", specialValueText="dynamic",
                                 minValue=-1, maxValue=1000, stepSize=1)
        self.autoRangeCti.insertChild(self.paddingCti)

        self.rangeMinCti = self.insertChild(SnFloatCti('min', 0.0))
        self.rangeMaxCti = self.insertChild(SnFloatCti('max', 1.0))

    @property
    def autoRangeMethod(self):
        """ The currently selected auto range method.
            If there is no method child CTI, there will be only one method (which will be returned).
        """
        if self.methodCti:
            return self.methodCti.configValue
        else:
            assert len(self._rangeFunctions) == 1, \
                "Assumed only one _rangeFunctions. Got: {}".format(self._rangeFunctions)
            return list(self._rangeFunctions.keys())[0]

    def _refreshNodeFromTarget(self, *args, **kwargs):
        """ Used to update the axis config tree item when the target axes was changed.
            It updates the autoRange checkbox (_forceRefreshAutoRange) and calculates new min max config
            values from range by calling _forceRefreshMinMax.

            The *args and **kwargs arguments are ignored.
        """
        # No need to check for self.getRefreshBlocked().
        # This is already done in the caller (refreshFromTarget)
        self._forceRefreshAutoRange()
        self._forceRefreshMinMax()

    def _forceRefreshMinMax(self):
        """ Refreshes the min max config values from the axes' state.
        """
        rangeMin, rangeMax = self.getTargetRange()
        maxOrder = np.log10(np.abs(max(rangeMax, rangeMin)))
        diffOrder = np.log10(np.abs(rangeMax - rangeMin))

        extraDigits = 2  # add some extra digits to make each pan/zoom action show a new value.
        precisionF = np.clip(abs(maxOrder - diffOrder) + extraDigits, extraDigits + 1, 25)
        precision = int(precisionF) if np.isfinite(precisionF) else extraDigits + 1


        self.rangeMinCti.precision = precision
        self.rangeMaxCti.precision = precision
        self.rangeMinCti.data, self.rangeMaxCti.data = rangeMin, rangeMax

        # Update values in the tree
        self.model.emitDataChanged(self.rangeMinCti)
        self.model.emitDataChanged(self.rangeMaxCti)

    def refreshMinMax(self):
        """ Refreshes the min max config values from the axes' state.
            Does nothing when self.getRefreshBlocked() returns True.
        """
        if self.getRefreshBlocked():
            logger.debug("refreshMinMax blocked for {}".format(self.nodeName))
            return

        self._forceRefreshMinMax()

    def _forceRefreshAutoRange(self):
        """ The min and max config items will be disabled if auto range is on.
        """
        enabled = self.autoRangeCti and self.autoRangeCti.configValue
        self.rangeMinCti.enabled = not enabled
        self.rangeMaxCti.enabled = not enabled
        self.model.emitDataChanged(self)

    def setAutoRangeOff(self):
        """ Turns off the auto range checkbox.
            Calls _refreshNodeFromTarget, not _updateTargetFromNode, because setting auto range off
            does not require a redraw of the target.
        """
        # /rtk/hdf-eos/DeepBlue-SeaWiFS-1.0_L3_20100101_v002-20110527T191319Z.h5/aerosol_optical_thickness_stddev_ocean
        if self.getRefreshBlocked():
            logger.debug("setAutoRangeOff blocked for {}".format(self.nodeName))
            return

        if self.autoRangeCti:
            self.autoRangeCti.data = False

        self._forceRefreshAutoRange()

    def setAutoRangeOn(self):
        """ Turns on the auto range checkbox for the equivalent axes
            Emits the sigItemChanged signal so that the inspector may be updated.

            Use the setXYAxesAutoRangeOn stand-alone function if you want to set the autorange on
            for both axes of a viewport.
        """
        if self.getRefreshBlocked():
            logger.debug("Set autorange on blocked for {}".format(self.nodeName))
            return

        if self.autoRangeCti:
            self.autoRangeCti.data = True
        self.model.sigItemChanged.emit(self)  # this should typically only be called by other classes.

    def calculateRange(self):
        """ Calculates the range depending on the config settings.
        """
        if not self.autoRangeCti or not self.autoRangeCti.configValue:
            return self.rangeMinCti.data, self.rangeMaxCti.data
        else:
            rangeFunction = self._rangeFunctions[self.autoRangeMethod]

            if self.subsampleCti is None:
                return rangeFunction()
            else:
                temp = rangeFunction(self.subsampleCti.configValue)
                return rangeFunction(self.subsampleCti.configValue)

    def _updateTargetFromNode(self):
        """ Applies the configuration to the target axis.
        """
        if not self.autoRangeCti or not self.autoRangeCti.configValue:
            padding = 0
        elif self.paddingCti.configValue == -1:  # specialValueText
            # PyQtGraph dynamic padding: between 0.02 and 0.1 dep. on the size of the ViewBox
            padding = None
        else:
            padding = self.paddingCti.configValue / 100

        targetRange = self.calculateRange()
       
        if not np.all(np.isfinite(targetRange)):
            logger.debug("New target range is not finite. Plot range not updated")
            return

        self.setTargetRange(targetRange, padding=padding)

    def getTargetRange(self):
        """ Gets the range of the target
        """
        raise NotImplementedError("Abstract method. Please override.")

    def setTargetRange(self, targetRange, padding=None):
        """ Sets the range of the target.
        """
        # The padding parameter is a bit of a hack.
        # That last option may be useful to colorize images with uints, which currently don't
        # show out black pixels for the maximum values (e.g. 255)
        raise NotImplementedError("Abstract method. Please override.")


class PgAxisRangeCti(AbstractRangeCti):
    """ Configuration tree item is linked to the axis range.
    """
    PYQT_RANGE = 'by PyQtGraph'

    def __init__(self, viewBox, axisNumber, autoRangeFunctions=None,
                 nodeName='range', expanded=True):
        """ Constructor.
            The target axis is specified by viewBox and axisNumber (0 for x-axis, 1 for y-axis)

            If given, autoRangeFunctions must be a (label to function) dictionary that will be used
            to populate the (auto range) method ChoiceCti. If not give, then there will not be
            a method choice and the autorange implemented by PyQtGraph will be used.
        """
        if autoRangeFunctions is None:
            autoRangeFunctions = {self.PYQT_RANGE: partial(viewBoxAxisRange, viewBox, axisNumber)}

        super(PgAxisRangeCti, self).__init__(autoRangeFunctions=autoRangeFunctions,
                                             nodeName=nodeName, expanded=expanded)
        assert axisNumber in (X_AXIS, Y_AXIS), "axisNumber must be 0 or 1"

        self.viewBox = viewBox
        self.axisNumber = axisNumber

        # Autorange must be disabled as not to interfere with this class.
        # Note that autorange of RTKPgPlotItem is set to False by default.
        axisAutoRange = self.viewBox.autoRangeEnabled()[axisNumber]
        assert axisAutoRange is False, \
            "Autorange is {!r} for axis {} of {}".format(axisAutoRange, axisNumber, self.nodePath)

        # Connect signals
        self.viewBox.sigRangeChangedManually.connect(self.setAutoRangeOff)
        self.viewBox.sigRangeChanged.connect(self.refreshMinMax)

    def _closeResources(self):
        """ Disconnects signals.
            Is called by self.Finalize when the cti is deleted.
        """
        self.viewBox.sigRangeChangedManually.disconnect(self.setAutoRangeOff)
        self.viewBox.sigRangeChanged.disconnect(self.refreshMinMax)

    def getTargetRange(self):
        """ Gets the range of the target
        """
        return self.viewBox.state['viewRange'][self.axisNumber]

    def setTargetRange(self, targetRange, padding=None):
        """ Sets the range of the target.
        """
        # viewBox.setRange doesn't accept an axis number :-(
        if self.axisNumber == X_AXIS:
            xRange, yRange = targetRange, None
        else:
            xRange, yRange = None, targetRange

        # Do not set disableAutoRange to True in setRange; it triggers 'one last' auto range.
        # This is why the viewBox autorange must be False at construction.
        self.viewBox.setRange(xRange=xRange, yRange=yRange, padding=padding,
                              update=False, disableAutoRange=False)


class PgHistLutColorRangeCti(AbstractRangeCti):
    """ Configuration tree item is linked to the HistogramLUTItem range.

        Used in the old imageplot2d.py
    """

    def __init__(self, histLutItem, autoRangeFunctions=None, nodeName='color range', expanded=True):
        """ Constructor.
            The target axis is specified by viewBox and axisNumber (0 for x-axis, 1 for y-axis)

            If given, autoRangeFunctions must be a (label to function) dictionary that will be used
            to populate the (auto range) method ChoiceCti. If not give, then there will not be
            a method choice and the autorange implemented by PyQtGraph will be used.
        """
        super(PgHistLutColorRangeCti, self).__init__(autoRangeFunctions=autoRangeFunctions,
                                                     nodeName=nodeName, expanded=expanded)
        self.histLutItem = histLutItem

        # Connect signals
        self.histLutItem.sigLevelsChanged.connect(self.setAutoRangeOff)
        self.histLutItem.sigLevelsChanged.connect(self.refreshMinMax)

    def _closeResources(self):
        """ Disconnects signals.
            Is called by self.Finalize when the cti is deleted.
        """
        self.histLutItem.sigLevelsChanged.disconnect(self.setAutoRangeOff)
        self.histLutItem.sigLevelsChanged.disconnect(self.refreshMinMax)

    def getTargetRange(self):
        """ Gets the (color) range of the HistogramLUTItem
        """
        return self.histLutItem.getLevels()

    def setTargetRange(self, targetRange, padding=None):
        """ Sets the (color) range of the HistogramLUTItem
            The padding variable is ignored.
        """
        rangeMin, rangeMax = targetRange
        self.histLutItem.setLevels(rangeMin, rangeMax)


class PgColorLegendCti(AbstractRangeCti):
    """ Configuration tree item is linked to the HistogramLUTItem range.
    """

    def __init__(self, legend, autoRangeFunctions=None, nodeName='color range', expanded=True):
        """ Constructor.
            The target axis is specified by viewBox and axisNumber (0 for x-axis, 1 for y-axis)

            If given, autoRangeFunctions must be a (label to function) dictionary that will be used
            to populate the (auto range) method ChoiceCti. If not give, then there will not be
            a method choice and the autorange implemented by PyQtGraph will be used.
        """
        super(PgColorLegendCti, self).__init__(
            autoRangeFunctions=autoRangeFunctions, nodeName=nodeName,
            expanded=True, paddingDefault=0)

        self.legend = legend

        self.paddingCti.defaultData = 0
        # Connect signals
        self.legend.sigLevelsChanged.connect(self.setAutoRangeOff)
        self.legend.sigLevelsChanged.connect(self.refreshMinMax)

    def _closeResources(self):
        """ Disconnects signals.
            Is called by self.Finalize when the cti is deleted.
        """
        self.legend.sigLevelsChanged.disconnect(self.setAutoRangeOff)
        self.legend.sigLevelsChanged.disconnect(self.refreshMinMax)

    def getTargetRange(self):
        """ Gets the (color) range of the HistogramLUTItem
        """
        return self.legend.getLevels()

    def setTargetRange(self, targetRange, padding=None):
        """ Sets the (color) range of the HistogramLUTItem
        """
        self.legend.setLevels(targetRange, padding=padding)


class PgColorLegendLabelCti(ChoiceCti):
    """ Configuration tree item that is linked to the axis label of a color legend .
    """

    def __init__(self, colorLegendItem, collector,
                 nodeName='label', defaultData=0, configValues=None):
        """ Constructor
            :param colorLegendItem PgColorLegendLabelCti:
            :param collector: needed to get the collector.rtiInfo
            :param nodeName: the node name of this config tree item (default = label
            :param defaultData:
            :param configValues:
        """
        super(PgColorLegendLabelCti, self).__init__(
            nodeName, editable=True, defaultData=defaultData, configValues=configValues)

        self.colorLegendItem = colorLegendItem
        self.collector = collector


    def _updateTargetFromNode(self):
        """ 
        Applies the configuration to the target axis it monitors.
        The axis label will be set to the configValue. If the configValue equals
        NO_LABEL_STR, the label will be hidden.
        """
        self.colorLegendItem.setLabel(None)


class PgShowHistCti(BoolCti):
    """ BoolCti that shows/hides the histogram of a color bar.
    """

    def __init__(self, colorLegendItem, nodeName='show histogram', defaultData=False):
        """ Constructor.
            The target axis is specified by viewBox and axisNumber (0 for x-axis, 1 for y-axis)
        """
        super(PgShowHistCti, self).__init__(nodeName, defaultData=defaultData)

        self.colorLegendItem = colorLegendItem

    def _updateTargetFromNode(self):
        """ Applies the configuration to its target axis
        """
        self.colorLegendItem.showHistogram(self.configValue)



class PgShowDragLinesCti(BoolCti):
    """ BoolCti that shows/hides the drag lines a color bar.
    """

    def __init__(self, colorLegendItem, nodeName='show drag lines',
                 defaultData=True, expanded=False):
        """ Constructor.
            The target axis is specified by viewBox and axisNumber (0 for x-axis, 1 for y-axis)
        """
        super(PgShowDragLinesCti, self).__init__(nodeName,
                                                 defaultData=defaultData, expanded=expanded)

        self.marginCti = self.insertChild(
            IntCti("margins", 40, minValue=0, maxValue=250, stepSize=5))

        self.colorLegendItem = colorLegendItem

    def _updateTargetFromNode(self):
        """ Applies the configuration to its target axis
        """
        try:
            self.colorLegendItem.showDragLines(self.configValue)
            self.colorLegendItem.setEdgeMargins(self.marginCti.configValue)
        except AttributeError as ex:
            logger.warning("Please update cmlib to latest version. No drag lines: {}".format(ex))


class PgGradientEditorItemCti(ChoiceCti):
    """ Lets the user select one of the standard color scales in a GradientEditorItem

        Is not used in the new PgImagePlot2d, only in the one in old_imageplot2d.py.
    """

    def __init__(self, gradientEditorItem, nodeName="color scale", defaultData=-1):
        """ Constructor.
            The gradientEditorItem must be a PyQtGraph.GradientEditorItem.
            The configValues are taken from pyqtgraph.graphicsItems.GradientEditorItem.Gradients
            which is an OrderedDict of color scales. By default the last item from this list is
            chosen, which are they 'grey' color scale.
        """
        super(PgGradientEditorItemCti, self).__init__(nodeName, defaultData=defaultData,
                                                      configValues=list(GRADIENTS.keys()))
        self.gradientEditorItem = gradientEditorItem

    def _updateTargetFromNode(self):
        """ Applies the configuration to its target widget
        """
        self.gradientEditorItem.loadPreset(self.configValue)


class PgAspectRatioCti(BoolCti):
    """ BoolCti for locking and specifying the aspect ratio (x/y)
    """

    def __init__(self, viewBox, nodeName="lock aspect ratio", defaultData=False, expanded=False):
        """ Constructor.
            The target axis is specified by viewBox and axisNumber (0 for x-axis, 1 for y-axis)
        """
        super(PgAspectRatioCti, self).__init__(nodeName, defaultData=defaultData, expanded=expanded)

        self.aspectRatioCti = self.insertChild(FloatCti("ratio", 1.0, minValue=0.0))
        self.viewBox = viewBox

    def _updateTargetFromNode(self):
        """ Applies the configuration to its target axis
        """
        self.viewBox.setAspectLocked(lock=self.configValue, ratio=self.aspectRatioCti.configValue)


class PgAxisFlipCti(BoolCti):
    """ BoolCti that flips an axis when True.
    """

    def __init__(self, viewBox, axisNumber, nodeName='flipped', defaultData=False
                 ):
        """ Constructor.
            The target axis is specified by viewBox and axisNumber (0 for x-axis, 1 for y-axis)
        """
        super(PgAxisFlipCti, self).__init__(nodeName, defaultData=defaultData)

        assert axisNumber in (X_AXIS, Y_AXIS), "axisNumber must be 0 or 1"
        self.viewBox = viewBox
        self.axisNumber = axisNumber

    def _updateTargetFromNode(self):
        """ Applies the configuration to its target axis
        """
        if self.axisNumber == X_AXIS:
            self.viewBox.invertX(self.configValue)
        else:
            self.viewBox.invertY(self.configValue)


class PgAxisLabelCti(ChoiceCti):
    """ Configuration tree item that is linked to the axis label.
    """

    def __init__(self, plotItem, axisPosition, collector,
                 nodeName='label', defaultData=0, configValues=None):
        """ Constructor
            :param plotItem:
            :param axisPosition: 'left', 'right', 'bottom', 'top'
            :param collector: needed to get the collector.rtiInfo
            :param nodeName: the node name of this config tree item (default = label
            :param defaultData:
            :param configValues:
        """
        super(PgAxisLabelCti, self).__init__(nodeName, editable=True,
                                             defaultData=defaultData, configValues=configValues)
        assert axisPosition in VALID_AXIS_POSITIONS, \
            "axisPosition must be in {}".format(VALID_AXIS_POSITIONS)
        self.collector = collector
        self.plotItem = plotItem
        self.axisPosition = axisPosition


    def _updateTargetFromNode(self):
        """ 
        Applies the configuration to the target axis it monitors.

        The axis label will be set to the configValue. If the configValue equals
            NO_LABEL_STR, the label will be hidden.
        """
        pass



class PgAxisShowCti(BoolCti):
    """ BoolCti that toggles axisPosition showing/hiding an axis.
    """

    def __init__(self, plotItem, axisPosition, nodeName='show', defaultData=True):
        """ Constructor.
            The target axis is specified by imagePlotItem and axisPosition.
            axisPosition must be one of: 'left', 'right', 'bottom', 'top'

            NOTE: the PyQtGraph showAxis seems not to work.
        """
        super(PgAxisShowCti, self).__init__(nodeName, defaultData=defaultData)
        assert axisPosition in VALID_AXIS_POSITIONS, \
            "axisPosition must be in {}".format(VALID_AXIS_POSITIONS)

        self.plotItem = plotItem
        self.axisPosition = axisPosition

    def _updateTargetFromNode(self):
        """ Applies the configuration to its target axis
        """
        logger.debug("showAxis: {}, {}".format(self.axisPosition, self.configValue))
        self.plotItem.showAxis(self.axisPosition, show=self.configValue)  # Seems not to work


class PgAxisLogModeCti(BoolCti):
    """ BoolCti that toggles an axis between logarithmic vs linear mode.
    """

    def __init__(self, plotItem, axisNumber, nodeName='logarithmic', defaultData=False):
        """ Constructor.
            The target axis is specified by imagePlotItem and axisNumber (0 for x-axis, 1 for y-axis)
        """
        super(PgAxisLogModeCti, self).__init__(nodeName, defaultData=defaultData)
        self.plotItem = plotItem
        self.axisNumber = axisNumber

    def _updateTargetFromNode(self):
        """ Applies the configuration to its target axis
        """
        if self.axisNumber == X_AXIS:
            xMode, yMode = self.configValue, None
        else:
            xMode, yMode = None, self.configValue

        self.plotItem.setLogMode(x=xMode, y=yMode)


class PgGridCti(BoolGroupCti):
    """ CTI for toggling the grid on and off.

        Has child CTIs for toggling the X and Y axes separately. These are typically not added
        as children of PgAxisCti objects so that the user can enable both grids with one checkbox.
        Also includes a child to configure the transparency (alpha) of the grid.
    """

    def __init__(self, plotItem, nodeName="grid", defaultData=True, expanded=False):
        """ Constructor.
            The target axis is specified by viewBox and axisNumber (0 for x-axis, 1 for y-axis)
        """
        super(PgGridCti, self).__init__(nodeName, defaultData=defaultData, expanded=expanded)

        self.plotItem = plotItem

        self.xGridCti = self.insertChild(BoolCti('x-axis', defaultData))
        self.yGridCti = self.insertChild(BoolCti('y-axis', defaultData))
        self.alphaCti = self.insertChild(FloatCti('alpha', 0.20,
                                                  minValue=0.0, maxValue=1.0, stepSize=0.01, decimals=2))

    def _updateTargetFromNode(self):
        """ Applies the configuration to the grid of the plot item.
        """
        self.plotItem.showGrid(x=self.xGridCti.configValue, y=self.yGridCti.configValue,
                               alpha=self.alphaCti.configValue)
        self.plotItem.updateGrid()


class PgAxisCti(GroupCti):
    """ Configuration tree item for a PyQtGraph plot axis.

        Currently, nothing more than a GroupCti.
    """
    pass


class PgPlotDataItemCti(GroupCti):
    """ Configuration tree item for a PyQtGraph plot data item.
        It allows for configuring a line style, color and symbols.

        Note that using a line width > 1 in comination with anti-aliassing may be slow.
        See https://github.com/pyqtgraph/pyqtgraph/issues/533
    """

    def __init__(self, nodeName="pen", defaultData=None, expanded=True):
        """ Constructor.
        """
        super(PgPlotDataItemCti, self).__init__(nodeName, defaultData=defaultData, expanded=expanded)
        self.antiAliasCti = self.insertChild(BoolCti("anti-alias", True))

        self.colorCti = self.insertChild(ColorCti('color', QtGui.QColor('#FF0066')))
        self.lineCti = self.insertChild(BoolCti('line', True, expanded=False,
                                                childrenDisabledValue=False))
        self.lineStyleCti = self.lineCti.insertChild(createPenStyleCti('style'))
        self.lineWidthCti = self.lineCti.insertChild(createPenWidthCti('width'))

        defaultShadowPen = QtGui.QPen(QtGui.QColor('#BFBFBF'))
        defaultShadowPen.setWidth(0)
        self.lineCti.insertChild(PenCti("shadow", False, expanded=False,
                                        resetTo=QtGui.QPen(defaultShadowPen),
                                        includeNoneStyle=True, includeZeroWidth=True))

        self.symbolCti = self.insertChild(BoolCti("symbol", False, expanded=False,
                                                  childrenDisabledValue=False))
        self.symbolShapeCti = self.symbolCti.insertChild(ChoiceCti("shape", 0,
                                                                   displayValues=['circle', 'square', 'triangle',
                                                                                  'diamond', 'plus'],
                                                                   configValues=['o', 's', 't', 'd', '+']))
        self.symbolSizeCti = self.symbolCti.insertChild(IntCti('size', 5, minValue=0,
                                                               maxValue=100, stepSize=1))

    @property
    def penColor(self):
        """ Returns the pen/color value"""
        return self.colorCti.configValue

    def createPlotDataItem(self):
        """ Creates a PyQtGraph PlotDataItem from the config values
        """
        antialias = self.antiAliasCti.configValue

        color = self.penColor
        if self.lineCti.configValue:
            pen = QtGui.QPen()
            pen.setCosmetic(True)
            pen.setColor(color)
            pen.setWidthF(self.lineWidthCti.configValue)
            pen.setStyle(self.lineStyleCti.configValue)
            shadowCti = self.lineCti.findByNodePath('shadow')
            shadowPen = shadowCti.createPen(altStyle=pen.style(), altWidth=2.0 * pen.widthF())
        else:
            pen = None
            shadowPen = None

        drawSymbols = self.symbolCti.configValue
        symbolShape = self.symbolShapeCti.configValue if drawSymbols else None
        symbolSize = self.symbolSizeCti.configValue if drawSymbols else 0.0
        symbolPen = None  # otherwise the symbols will also have dotted/solid line.
        symbolBrush = QtGui.QBrush(color) if drawSymbols else None

        plotDataItem = pg.PlotDataItem(antialias=antialias, pen=pen, shadowPen=shadowPen,
                                       symbol=symbolShape, symbolSize=symbolSize,
                                       symbolPen=symbolPen, symbolBrush=symbolBrush)
        return plotDataItem


class PgColorMapCti(AbstractCti):
    """ Lets the user select one of color maps of the color map library
    """

    SUB_SAMPLING_OFF = 1

    def __init__(self, colorLegendItem,
                 nodeName="color map", defaultData=DEFAULT_COLOR_MAP, expanded=False):
        """ Constructor.

            Stores a color map as data.

            :param defaultData: the default index in the combobox that is used for editing
        """

        self.colorLegendItem = colorLegendItem
        self.cmLibModel = CmLibModelSingleton.instance()

        # grey scale color map for when no color map is selected.
        lutRgba = np.outer(np.arange(256, dtype=np.uint8), np.array([1, 1, 1, 1], dtype=np.uint8))
        lutRgba[:, 3] = 255
        self.greyScaleColorMap = ColorMap(CmMetaData("-- none --"), CatalogMetaData("Argos"))
        self.greyScaleColorMap.set_rgba_uint8_array(lutRgba)

        super(PgColorMapCti, self).__init__(nodeName, defaultData, expanded=expanded)

        self.reverseCti = self.insertChild(
            BoolCti("reversed", False))

        self.subSampleCti = self.insertChild(
            IntCti("subsample", self.SUB_SAMPLING_OFF, specialValueText="off",
                   minValue=self.SUB_SAMPLING_OFF, maxValue=64, stepSize=1)
        )

    def _enforceDataType(self, data):
        """ Converts to int so that this CTI always stores that type.
        """
        if data is None:
            return self.greyScaleColorMap
        elif isinstance(data, ColorMap):
            return data
        else:
            return self.cmLibModel.getColorMapByKey(data)

    @property
    def configValue(self):
        """ The currently selected configValue

            :rtype: ColorMap
        """
        return self.data

    def _updateTargetFromNode(self):
        """ Applies the configuration to its target axis.
            Sets the image item's lookup table to the LUT of the selected color map.
        """
        lut = self.data.rgb_uint8_array

        targetSize = self.subSampleCti.configValue
        if targetSize > self.SUB_SAMPLING_OFF:
            sourceSize, _ = lut.shape
            subIdx = np.round(np.linspace(0, sourceSize - 1, targetSize)).astype(np.uint)
            lut = lut[subIdx, :]

        if self.reverseCti.configValue:
            lut = np.flipud(lut)

        self.colorLegendItem.setLut(lut)

    def _dataToString(self, data):
        """ Conversion function used to convert the (default)data to the display value.
        """
        return "" if data is None else data.meta_data.pretty_name

    @property
    def decoration(self):
        """ Returns a pixmap of the color map to show as icon
        """
        return makeColorBarPixmap(
            self.data,
            width=self.cmLibModel.iconBarWidth * 0.65,
            height=self.cmLibModel.iconBarHeight * 0.65,
            drawBorder=self.cmLibModel.drawIconBarBorder)

    def _nodeMarshall(self):
        """ Returns the non-recursive marshalled value of this CTI. Is called by marshall()
        """
        return self.data.key

    def _nodeUnmarshall(self, key):
        """ Initializes itself non-recursively from data. Is called by unmarshall()
        """
        self.data = self.cmLibModel.getColorMapByKey(key)

    def createEditor(self, delegate, parent, option):
        """ Creates a ChoiceCtiEditor.
            For the parameters see the AbstractCti constructor documentation.
        """
        return PgColorMapCtiEditor(self, delegate, parent=parent)


class PgColorMapCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a QCombobox for editing ChoiceCti objects.
    """

    def __init__(self, cti, delegate, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters
        """
        super(PgColorMapCtiEditor, self).__init__(cti, delegate, parent=parent)

        selectionWidget = ColorSelectionWidget(self.cti.cmLibModel)
        setWidgetSizePolicy(selectionWidget, QtWidgets.QSizePolicy.Expanding, None)

        selectionWidget.sigColorMapHighlighted.connect(self.onColorMapHighlighted)
        selectionWidget.sigColorMapChanged.connect(self.onColorMapChanged)
        self.selectionWidget = self.addSubEditor(selectionWidget, isFocusProxy=True)
        self.comboBox = self.selectionWidget.comboBox

    def finalize(self):
        """ Is called when the editor is closed. Disconnect signals.
        """
        logger.debug("PgColorMapCtiEditor.finalize")
        self.selectionWidget.sigColorMapChanged.disconnect(self.onColorMapChanged)
        self.selectionWidget.sigColorMapHighlighted.disconnect(self.onColorMapHighlighted)
        super(PgColorMapCtiEditor, self).finalize()

    def setData(self, data):
        """ Provides the main editor widget with a data to manipulate.
        """
        if data is None:
            logger.warning("No color map to select")
        else:
            self.selectionWidget.setColorMapByKey(data.key)

    def getData(self):
        """ Gets data from the editor widget.
        """
        return self.selectionWidget.getCurrentColorMap()

    @QtSlot(ColorMap)
    def onColorMapHighlighted(self, colorMap):
        """ Is called when the user highlights an item in the combo box or dialog.

            The item's index is passed.
            Note that this signal is sent even when the choice is not changed.
        """
        logger.debug("onColorMapHighlighted({})".format(colorMap))
        self.cti.data = colorMap
        self.cti.updateTarget()

    @QtSlot(ColorMap)
    def onColorMapChanged(self, index):
        """ Is called when the user chooses an item in the combo box. The item's index is passed.
            Note that this signal is sent even when the choice is not changed.
        """
        logger.debug("onColorMapChanged")
        self.delegate.commitData.emit(self)

