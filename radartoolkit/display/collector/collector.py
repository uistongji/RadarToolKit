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


import os
import logging
import numpy as np
import numpy.ma as ma
from functools import partial
from collections import OrderedDict
import traceback

from ..widgets.basepanel import BasePanel
from ._defaults import ProcTypes
from display.rti.baserti import BaseRti
from ..bindings import QtWidgets, QtSignal, QtCore, QtGui, QtSlot
from ..settings import DOCK_SPACING, DOCK_MARGIN
from ..utils.check_class import check_class, check_is_a_sequence, check_is_an_array
from ..evaluator.abstract import UpdateReason
from ._defaults import Peach
from .roi import RoiWidget, roiPlots
from .tree import CollectorTree
from .histpane import HistPane
from .qts import InfoDialog, ParamsWidget
from ..config.ctis.spectis import ColProcCti
from ..utils.mask import ArrayWithMask
import cookies.processing as PIK1Module


logger = logging.getLogger(__name__)


FAKE_DIM_NAME = '-'
FAKE_DIM_OFFSET = 1000


COLOR_INFO, COLOR_PROC, COLOR_AXIS = '#ADD8E6', "#3CB371", '#708090'


class Collector(BasePanel):
    """ 
    Widget for collecting the selected data from the file tree widget.
    Consists of a table to collect the RtiItems

    The CollectorTree only stores the items, 
    the intelligence is located in the Collector itself.
    """     

    COL_COUNT = 6
    COL_PATH, COL_PROCESSING, COL_RANGE, COL_AZIMUTH, COL_ROI, COL_HIST = range(COL_COUNT)
    COL_FIRST_COMBO = 1 # column that contains the first combobox 
    VALID_ROWS = [0, 1] # first row: header

    # Any interations play in the MainWindow ground.
    sigContentsChanged = QtSignal(str) # any contents changed emit 
    sigShowMessage = QtSignal(str)     # any messages to be displaced emit
    sigShowHistory = QtSignal(dict, dict)  # any messages related interaction on the collector will be emitted
    sigSpinderUpdates = QtSignal(dict)
    sigProcessingChanged = QtSignal(str, object, object)
    sigProdDictChanged = QtSignal(str, str)


    def __init__(self):
        super(Collector, self).__init__()

        self._rti = None # currently selected rti-item
        self._rtis = OrderedDict()
        self._rtisInfo = OrderedDict()
        self._rtiInfo = None
        
        self._maxValidRow = 0 # in fact it can have 2 valid rows
        self._rtiFuncInfo = None # {} stores the dict
        self._signalsBlocked = False # make sure of the safe thread

        self.AXIS_POST_FIX = "-axis" # added to the axis label to give the combobox labels
        self._rtiConfig = None       # keep a reference to the collector-config to retrive parameters
        self._axisNames = []         # axis names, corresponding to the independent variable
        self._fullAxisNames = []     # will be set in clearAndSetComboBoxes
        self._fullProcNames = []     # will be set in clearAndSetComboBoxes
        self._slicedArrayRti = []

        # keep referenced to the widgets from being destroyed by QT. -.-
        # if not, it may happen 'segementation fault' 
        # or 'RuntimeError: Internal C++ object already deleted'
        self._comboBoxes = {}
        self._spinBoxes = []
        self._rois = {}
        self._histPanes = {} # displays the extra information 

        # initialize relavant widgets to be displayed inside the collector table
        # layout: path, processing, azimuth, range, histories/progress, interaction/roi button
        self._tree = CollectorTree(parent=self)

        # processing parameters widget for the items in the collector
        self._config = ColProcCti(collector=self, nodeName='Processing') 
        self.paramsViewer = ParamsWidget()
        self.paramsViewer._configTreeModel.setInvisibleRootItem(self._config)


        self._initView()
        self._updateRtisInfo()


    ##############
    #   Viewers  #
    ##############

    def _initView(self):
        """
        Initialize the interface.
        """
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setSpacing(DOCK_SPACING)
        self.mainLayout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)
        self.mainLayout.addWidget(self.tree)
        

    ##############
    # Properties #
    ##############

    def sizeHint(self):
        """ The recommended size for the widget """
        return QtCore.QSize(300, Peach.TOP_DOCK_HEIGHT)
    

    def __repr__(self) -> str:
        return f"<{type(self).__name__}"
    

    @property
    def config(self):
        return self._config
    
    
    @property
    def rti(self):
        """ The current RTI tree item. Can be None """
        return self._rti
    

    @property
    def maxValidRow(self):
        """
        Returns the maximum number of the valid Rtis that can be 
        displayed and handled by the collector.
        """
        return self._maxValidRow
    
    
    @property
    def rtiIsSliceable(self):
        return self._rti and self._rti.isSliceable
    

    @property
    def axisNames(self):
        """ returns the axis names, 
            indicating the independent dimensions of the vidualization.
        """
        return self._axisNames
    
    
    @property
    def fullAxisNames(self):
        return self._fullAxisNames
    

    @property
    def maxCombos(self):
        """ returns the maximum number of the axis combo boxes """
        return len(self._comboBoxes)
    
    
    @property
    def tree(self):
        return self._tree
        

    @property
    def rtiInfo(self):
        """ Returns a dictionary with information on the selected RTI (repo tree item).
            This can be used in string formatting of config options. For instance: the plot title
            can be specified as: '{path} {slices}', which will be expanded with the actual nodePath
            and slices-string of the RTI.

            If no RTI is selected the applicable values will be empty strings.

            The dictionary has the following contents:
                slices : a string representation of the selected slice indices.
                name        : nodeName of the RTI
                path        : nodePath of the RTI
                unit        : unit of the RTI in parentheses
                raw-unit    : unit of the RTI without parentheses (empty string if no unit given)
                n-dim       : dimension selected in the combobox for axis n. The axis name will be
                              in lower case (so e.g. x-dim, y-dim, etc)
        """
        return self._rtiInfo
    

    @property
    def rtisInfo(self):
        """ Returns a dictionary with information on the selected RTI (repo tree item).
            This can be used in string formatting of config options. For instance: the plot title
            can be specified as: '{path} {slices}', which will be expanded with the actual nodePath
            and slices-string of the RTI.

            If no RTI is selected the applicable values will be empty strings.

            The dictionary has the following contents:
                slices : a string representation of the selected slice indices.
                name        : nodeName of the RTI
                path        : nodePath of the RTI
                unit        : unit of the RTI in parentheses
                raw-unit    : unit of the RTI without parentheses (empty string if no unit given)
                n-dim       : dimension selected in the combobox for axis n. The axis name will be
                              in lower case (so e.g. x-dim, y-dim, etc)
        """
        return self._rtisInfo
    

    ##############
    #   Methods  #
    ##############
    
    def blockChildrenSignals(self, block):
        """ If block, the signals of the combo boxes, spinder, history widget are blocked.
            Returns the old blocking state.
        """
        logger.debug("Blocking collector signals")
        for spinBox in self._spinBoxes:
            spinBox.blockSignals(block)
        for _comboBoxes in self._comboBoxes.values():
            for comboBox in _comboBoxes:
                comboBox.blockSignals(block)
        result = self._signalsBlocked
        self._signalsBlocked = block
        return result
    

    def _hasFakeDimension(self, rti):
        """ returns True if a fake dimension exsits. 
        add a fake dimension (of length 1) only if there are fewer dimensions than the inspector can show.
        """
        return rti.nDims < (len(self._fullAxisNames) - 1)
    
    
    def _setColumnCountForContents(self):
        """ 
        Sets the column count given the current axis and selected rti.    
        Returns the newly set column count
        """
        # numRtiDims = self.rti.nDims if self.rti and self.rti.isSliceable else 0
        # colCount = Peach._COL_COUNT + max(numRtiDims, len(self.axisNames))
        colCount = self.COL_COUNT
        self.tree.model().setColumnCount(colCount)
        return colCount
    
    
    def clear(self):
        """ 
        Removes all the widgets.
        Don't use model.clear(). it will delete the column sizes
        """
        # model = self.tree.model()
        self._setColumnCountForContents()


    def _clearAndSetAll(self, axesNames, itemRows=[]):
        """ 
        Removes and resets all the widgets.
        """
        logger.debug(f"{self.__repr__()}:_clearAndSetAll> called, \
            removing and resetting all the values with axesNames({axesNames}) and itemRows({itemRows}).")
        check_is_a_sequence(axesNames)

        # deletes all the widgets and diconnects the signals
        self._deleteHistPane()
        self._deleteRoi()
        self._deleteComboBoxes() # comboBoxes=[processing, range, azimuth]
        self.clear()

        # resets all the widgets and connects the signals
        self._setLabels(axesNames)
        self._createComboBoxes(itemRows=itemRows)
        self._createRoi(itemRows=itemRows)
        self._createHistPane(itemRows=itemRows)
        self._updateWidgets(itemRows=itemRows)


    def _deleteHistPane(self):
        """ 
        Deletes the HistPane from the collector tree
        after counting how many rows that have been added to.
        """
        tree  = self.tree
        model = tree.model()

        if len(self._histPanes) == 0:
            return
        
        for row, _histPane in enumerate(self._histPanes.values()):
            # already setup the histPane and starts to delete it from the tree
            logger.debug(f"{self.__repr__()}:_deleteHistPane> called, \
                        removing combobox at: ({row}, {self.COL_HIST})")
            tree.setIndexWidget(model.index(row, self.COL_HIST), None)

            # disconnect signals
            self.sigShowHistory.disconnect(_histPane.setOptsText)

        # make sure that the space is already be freed up.
        self._histPanes = {}

    
    def _deleteRoi(self):
        """
        Deletes the Roi checkBox in the tree.
        """
        tree = self.tree
        model = self.tree.model()

        if len(self._rois) == 0:
            return 
        
        for row, _roi in enumerate(self._rois.values()):
            logger.debug(f"{self.__repr__()}:_deleteRoi> called, removing combobox at: ({row}, {self.COL_ROI})")
            tree.setIndexWidget(model.index(row, self.COL_ROI), None)
        self._rois = {}


    def _deleteComboBoxes(self):
        """
        Deletes all the combo boxes for each of the row.
        self._comboBoxes = {'row-0':[], 'row-1': []}
        """
        tree = self.tree
        model = self.tree.model()

        if len(self._comboBoxes) == 0:
            return 
        
        for row, _ in enumerate(self._comboBoxes.values()):
            for col in range(self.COL_PROCESSING, self.COL_AZIMUTH+1):
                logger.debug(f"{self.__repr__()}:_deleteComboBoxes> called, removing combobox at: ({row}, {col})")
                tree.setIndexWidget(model.index(row, col), None)
        self._comboBoxes = {}

    
    def _setLabels(self, axesNames):
        """ 
        Sets the axisnames, combobox labels and updates the headers,
        removes old values first.
        the axis combobolabels are the axis name + '-axis'
        """
        logger.debug(f"{self.__repr__()}:_setLabels> called, setting the axisnames, labels as well as the headers.")
        # processing 
        self._setHeaderLabel(self.COL_PROCESSING, "Processing")
        
        # axis
        self._axisNames = tuple(axesNames)
        self._fullAxisNames = [""] * len(self._axisNames)
        for AxisNr in range(len(self._fullAxisNames)):
            if AxisNr == 0:
                self._fullAxisNames[AxisNr] = "Range"
            elif AxisNr == 1:
                self._fullAxisNames[AxisNr] = "Azimuth"
            elif AxisNr == 2:
                self._fullAxisNames[AxisNr] = "Cross-track"
        for col, label in enumerate(self._fullAxisNames, self.COL_RANGE):
            self._setHeaderLabel(col, label)
        
        # history and roi
        self._setHeaderLabel(self.COL_ROI, "Interaction") 
        self._setHeaderLabel(self.COL_HIST, "History")


    def _setHeaderLabel(self, col, text):
        """ Sets the header of column col to text.
            Will increase the number of columns if col is larger than the current number.
        """
        model = self.tree.model()
        item = model.horizontalHeaderItem(col)
        if item:
            item.setText(text)
        else:
            model.setHorizontalHeaderItem(col, QtGui.QStandardItem(text))


    def _createComboBoxes(self, itemRows=[]):
        """ 
        Creates combbox for each of the fullAxisNames & Processing.
        _comboBoxes = {"row-1": [], "row-2": []}
        """
        logger.debug(f"{self.__repr__()}:_createComboBoxes> called, creating the comboBoxes for the processing and the fullAxisNames.")
        tree = self.tree
        model = self.tree.model()
        self._setColumnCountForContents()

        # starting to create the valid comboBoxes for each row
        for row in itemRows:
            _comboBoxes = []

            # processing comboBox
            comboBox = QtWidgets.QComboBox()
            comboBox.setMaximumHeight(25)
            comboBox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
            comboBox.setMinimumContentsLength(3) # so that collector table header always readable
            comboBox.activated.connect(self._procComboBoxActivated)
            tree.setIndexWidget(model.index(row, self.COL_PROCESSING), comboBox)
            _comboBoxes.append(comboBox)

            # axis selection
            for col in range(self.COL_RANGE, self.COL_AZIMUTH+1):
                comboBox = QtWidgets.QComboBox()
                comboBox.setMaximumHeight(25)
                comboBox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
                comboBox.setMinimumContentsLength(3) # so that collector table header always readable
                comboBox.activated.connect(self._axisComboBoxActivated)

                tree.setIndexWidget(model.index(row, col), comboBox)
                _comboBoxes.append(comboBox)

            self._comboBoxes[f"row-{row}"] = _comboBoxes
        

    def _createRoi(self, itemRows=[]):
        """ 
        Sets up the Roi checkbox in the tree.
        """
        logger.debug(f"{self.__repr__()}:_createRoi> called, creating the Roi checkbox.")
        tree = self.tree
        model = self.tree.model()
        self._setColumnCountForContents()

        # valid row counts for the current model including the header
        for row in itemRows:
            # setting the widget
            widget = roiPlots(label=f"Plot {row+1}")

            tree.setIndexWidget(model.index(row, self.COL_ROI), widget)
            self._rois[f"row-{row}"] = widget


    def _createHistPane(self, itemRows=[]):
        """ 
        Sets up the histPane in the tree.
        """
        logger.debug(f"{self.__repr__()}:_createHistPane> called, creating the histpane.")
        tree = self.tree
        model = self.tree.model()
        self._setColumnCountForContents()
        
        # valid row counts for the current model including the header
        for row in itemRows:
            _histPane = HistPane()
            
            self.sigShowHistory.connect(_histPane.setOptsText)
            tree.setIndexWidget(model.index(row, self.COL_HIST), _histPane)

            self._histPanes[f"row-{row}"] = _histPane


    def _updateWidgets(self, itemRows=[]):
        """ 
        Updates the combos, spinder, history (if en) given the new rti, axes or something else.
        Emits the sigContentsChanged signal.
        """        
        logger.debug(f"{self.__repr__()}:_updateWidgets> called, updading the widgets.")

        if len(itemRows) == 0:
            return
        
        for row, rti in zip(itemRows, self._rtis.values()):
            if row not in self.VALID_ROWS:
                continue

            # create path label
            model = self.tree.model()
            nodePath = '' if rti is None else rti.nodePath
            pathItem = model.item(row, 0)
            if pathItem:
                # reusing path item. If move all items the column size will be lost.
                pathItem.setText(nodePath)
            else:
                pathItem = QtGui.QStandardItem(nodePath)
                pathItem.setEnabled(False)
                model.setItem(row, 0, pathItem)

            pathItem.setToolTip(nodePath)
            if rti is not None:
                pathItem.setIcon(rti.decoration)

            # activate the widgets
            self._populateComboBoxes(row=row, rti=rti)
            self._activateRoi(row=row, rti=rti)
            self._activateHistPane(row=row, rti=rti)

            self._updateRtisInfo()
            self.tree.resizeColumnsFromContents(startCol=self.COL_FIRST_COMBO)

            logger.debug("{}:_updateWidgets> {} sigContentsChanged signal (_updateWidgets)"
                        .format(self.__repr__(), "Blocked" if self.signalsBlocked() else "Emitting"))

        # emit the signal to the evaluator to prepare for plotting
        self.sigContentsChanged.emit(UpdateReason.RTI_CHANGED)         


    def _deleteSpinder(self, row):
        """ removes all spinboxes """
        if self._spinder.menuButton.menu():
            self._spinBox.valueChanged[int].disconnect(self._spinboxValueChanged)
            self.sigSpinderUpdates.disconnect(self._spinder._updateValues)  
            self._spinder.menuButton.setMenu(None)

            # disconnect the signal with roi
            self._roiWidget._clearContents()
            self._roiWidget.sigRoiRegionChanged.disconnect(self._spinBox.setValue)

        self._spinder.menuButton.setEnabled(False)
        self.sigSpinderUpdates.emit({})


    def _createSpinder(self, row):
        """ Creates a spinBox for each dimension that is not selected in a combo box.
        """
        if not self.rtiIsSliceable:
            return
        logger.debug("_createSpinder, array shape: {}".format(self._rti.arrayShape))

        if self._rti and self._rti.isSliceable:
            menu = QtWidgets.QMenu(self._spinder.menuButton)
            actionGroup = QtGui.QActionGroup(self)
            actionGroup.setExclusive(True)
            for axisNr, axisName in enumerate(self._fullAxisNames):
                print("axisName: {}".format(axisName))
                menuBtnFunc = partial(self._createMenuBtnAction, axisNr, axisName)
                action = QtGui.QAction(axisName, 
                                       self,
                                       triggered = menuBtnFunc,
                                       checkable=True)
                actionGroup.addAction(action)
            for action in actionGroup.actions():
                menu.addAction(action)
                
            self._spinder.menuButton.setMenu(menu)
            self._spinder.menuButton.setEnabled(True)
            
            # signal connections
            self._spinBox.valueChanged[int].connect(self._spinboxValueChanged)
            self.sigSpinderUpdates.connect(self._spinder._updateValues)

            # activate roi
            self._roiWidget._createRoi(self.rti[:,:])
            self._roiWidget.sigRoiRegionChanged.connect(self._spinBox.setValue)

            # send signal to activate (default: always activate the last axis)
            self.sigSpinderUpdates.emit(
                {'label': self._fullAxisNames[axisNr],
                 'min': 0, 'max': self._rti.arrayShape[axisNr]-1,
                 'enabled': True if (self._rti.arrayShape[axisNr]>1) else False})


    def _populateComboBoxes(self, row=None, rti=None):
        """ 
        Populates the combo boxes, e.g., axis and proc, with values of the file tree item.
        """
        logger.debug(f"{self.__repr__()}:_populateComboBoxes> called, populating comboBoxes in the row({row}).")

        _comboBoxes = self._comboBoxes[f"row-{row}"]
        for comboBox in _comboBoxes:
            comboBox.clear()

        if row is None or row not in self.VALID_ROWS or rti is None:
            return

        # setup processing combobox and set enabled only when the dimensionality satifies
        procComboBox = _comboBoxes[0]
        procComboBox.addItem('', userData=None)
        procComboBox.setEnabled(False)
        
        if rti:
            for proc in ProcTypes._FULL4PRIC_NAMES.keys():
                procComboBox.addItem(proc)
            if rti.dimensionality == "array" and type(rti).__name__ in ProcTypes._FULL4PRIC_RTIS:
                procComboBox.setEnabled(True)
                procComboBox.setCurrentIndex(1)
        else:
            procComboBox.addItem('', userData=None)
            procComboBox.setEnabled(False)

        # setup axes-related comboboxes
        if not (rti and rti.isSliceable):
            # add an empty item to the axis combo boxes so that resize to contents works
            for comboBoxNr, comboBox in enumerate(_comboBoxes[1:]):
                comboBox.addItem('', userData=None)
                comboBox.setEnabled(False)
            return
        

        for comboBoxNr, comboBox in enumerate(_comboBoxes[1:]):
            # Only add a fake dimension of length 1 if there are fewer dimensions in the RTI than
            # the inspector can show.
            # --- set special range/azimuth index choices ---
            # Attention: always assume range axis comes first and azimuth later.
            if self._hasFakeDimension(rti=rti):
                comboBox.addItem(FAKE_DIM_NAME, userData = FAKE_DIM_OFFSET + comboBoxNr)
            if comboBoxNr == 0:
                for dimName in ["Index", "Propagation", "Depth"]:
                    comboBox.addItem(dimName, userData=dimName)
            elif comboBoxNr == 1:
                for dimName in ["Index", "Distance"]:
                    comboBox.addItem(dimName, userData=dimName)
            else:
                comboBox.addItem("Index")
            comboBox.setEnabled(True)
            comboBox.setCurrentIndex(0)


    def _activateRoi(self, row=None, rti=None):
        pass


    def _activateHistPane(self, row=None, rti=None):
        """ 
        Activates the histPane to display the information and reset the config.
        """
        if row is None or row not in self.VALID_ROWS:
            return
        logger.debug(f"{self.__repr__()}:_activateHistPane> called, activaiting the histPane to display information with row({row}).")

        # make sure everything is on the track.
        _histPanes = self._histPanes[f"row-{row}"]
        _histPanes.clear()

        if rti: # if rti is not None
            self.sigShowHistory.emit(
                {'field': 'success', 'desc': "New file item ({}) added.".format(rti.nodeName)},
                {'color': COLOR_INFO})
        else:
            self.sigShowHistory.emit(
                {'field': 'failure', 'desc': "No item added (None)."},
                {'color': COLOR_INFO})


    def _updateRtisInfo(self):
        """ 
        Updates the _rtisInfo property when a new RTI is set or spin/comboboxes change value .
        """
        logger.debug(f"{self.__repr__()}._updateRtisInfo> updaing the rtis information.")
        
        # information about the dependent dimension
        for key, rti in self._rtis.items():
            if rti is None:
                info = {'slices': '',
                        'name': '',
                        'path': '',
                        'file-name': '',
                        'dir-name': '',
                        'base-name': '',
                        'unit': '',
                        'raw-unit': ''}
            else:
                dirName, baseName = os.path.split(rti.fileName)
                info = {'slices': self.getSlicesString(),
                        'name': rti.nodeName,
                        'path': rti.nodePath,
                        'file-name': rti.fileName,
                        'dir-name': dirName,
                        'base-name': baseName,
                        'unit': '({})'.format(rti.unit) if rti.unit else '',
                        'raw-unit': rti.unit}

            self._rtisInfo[key] = info
            self._rtiInfo = info


    def _updateFuncInfo(self):
        """ Updates the _rtiFuncInfo property when a new RTI is set or any config value changes.
        """
        logger.debug("Updating self._rtiFuncInfo")

        info = {'channels': "[1,1,1,0,0;2,2,1,0,0]",
                'incoh_depth': 10,
                'coh_depth': 5,
                'output_samples': 3200,
                'scale': 20000,
                'blanking': 0,
                'output_phases': True,
                'gainPicker': 2,
                'bandpass': True,
                'presum': True}
        self._rtiFuncInfo = info


    def getSlicesString(self):
        """ Returns a string representation of the slices that are used to get the sliced array.
            For example returns '[:, 5]' if the combo box selects dimension 0 and the spin box 5.
        """
        if not self.rtiIsSliceable:
            return ''

        # The dimensions that are selected in the combo boxes will be set to slice(None),
        # the values from the spin boxes will be set as a single integer value
        nDims = self.rti.nDims
        sliceList = [':'] * nDims

        for spinBox in self._spinBoxes:
            dimNr = spinBox.property("dim_nr")
            sliceList[dimNr] = str(spinBox.value())

        # No need to shuffle combobox dimensions like in getSlicedArrays; all combobox dimensions
        # yield a colon.
        return "[" + ", ".join(sliceList) + "]"
    

    def getSlicedArray(self, copy=True):
        """ 
        Get the sliced array from the rti

        :param copy: If True (the default), a copy is made so that inspectors cannot
            accidentally modify the underlying of the RTIs. You can set copy=False as a
            potential optimization, but only if you are absolutely sure that you don't modify
            the the slicedArray in your inspector! Note that this function calls transpose,
            which can still make a copy of the array for certain permutations.

        :return: ArrayWithMask array with the same number of dimension as the number of
            comboboxes (this can be zero!).

            Returns None if no slice can be made (i.e. the RTI is not sliceable).
        :rtype ArrayWithMask:
        """
        # sanity check on the inputs
        if len(self._rtis) == 0:
            self.sigShowMessage.emit("<collector._getSlicedArrays> no item selected.")
            return None

        for _, rti in self._rtis.items():
            if not rti and not rti.rtiIsSliceable:
                continue

            if np.prod(rti.arrayShape) == 0:
                self.sigShowMessage.emit(f"<collector._getSlicedArrays> selected item ({rti.nodeName}) has zero array elements.")
                continue
        
            # get the sliced array
            slicedArrayRti = rti

            slicedArray = slicedArrayRti[:, :]
            check_is_an_array(slicedArray, np.ndarray)

            # data mask
            if not isinstance(slicedArray, ma.MaskedArray):
                slicedArray = ma.MaskedArray(slicedArray)
            awm = ArrayWithMask.createFromMaskedArray(slicedArray)
            del slicedArray

        return awm
    

    def getSlicedArrays(self, copy=True):
        """ 
        Get the sliced array from the rti

        :param copy: If True (the default), a copy is made so that inspectors cannot
            accidentally modify the underlying of the RTIs. You can set copy=False as a
            potential optimization, but only if you are absolutely sure that you don't modify
            the the slicedArray in your inspector! Note that this function calls transpose,
            which can still make a copy of the array for certain permutations.

        :return: ArrayWithMask array with the same number of dimension as the number of
            comboboxes (this can be zero!).

            Returns None if no slice can be made (i.e. the RTI is not sliceable).
        :rtype ArrayWithMask:
        """
        # sanity check on the inputs
        if len(self._rtis) == 0:
            self.sigShowMessage.emit("<collector._getSlicedArrays> no item selected.")
            return None

        slicedArrays = {}
        for key, rti in self._rtis.items():
            if not rti and not rti.rtiIsSliceable:
                continue

            if np.prod(rti.arrayShape) == 0:
                self.sigShowMessage.emit(f"<collector._getSlicedArrays> selected item ({rti.nodeName}) has zero array elements.")
                continue
        
            # get the sliced array
            slicedArrayRti = rti

            slicedArray = slicedArrayRti[:, :]
            check_is_an_array(slicedArray, np.ndarray)

            # data mask
            if not isinstance(slicedArray, ma.MaskedArray):
                slicedArray = ma.MaskedArray(slicedArray)
            awm = ArrayWithMask.createFromMaskedArray(slicedArray)
            del slicedArray

            slicedArrays[key] = awm

        return slicedArrays
    

    def getSpinYdimSize(self):
        return {'minX': 1, 'maxX': 100}


    def _comboBoxDimensionIndex(self, comboBox):
        """ Returns the dimension index (from the user data) of the current item of the combo box.
        """
        return comboBox.itemData(comboBox.currentIndex())
    

    def _dimensionSelectedInComboBox(self, dimNr):
        """ Returns True if the dimension is selected in one of the combo boxes.
        """
        for combobox in self._comboBoxes:
            if self._comboBoxDimensionIndex(combobox) == dimNr:
                return True
        return False
    

    def tryImportFunc(self, funcName):
        """ Try to import functionality with the key 'funcName'
        """
        try:
            # module = importlib.import_module(COOKIES_MODULE) 
            return getattr(PIK1Module, funcName)
        except Exception as ex:
            ex.traceBackString = traceback.format_exc()
            self._exception = ex
            logger.warning("Unable to import func ({}): {}".format(funcName, ex))
            logger.debug("Traceback: {}".format(ex.traceBackString))


    def getDimSlice(self):
        """ gets the slice indexes """
        if self._spinder.menuButton.isEnabled():
            center = self._spinBox.value()
            step = 5000
            if self._spinder.menuButton.text() == "Range":
                YdimSlice = {'minY': max(1, center-step),
                             'maxY': min(self._rti.arrayShape[0], center+step)}
                XdimSlice = {'minX': 1, 'maxX': self._rti.arrayShape[1]}
            elif self._spinder.menuButton.text() == "Azimuth":
                YdimSlice = {'minY': 1, 'maxY': self._rti.arrayShape[0]}
                XdimSlice = {'minX': max(1, center-step),
                             'maxX': min(self._rti.arrayShape[1], center+step)}
            else:
                YdimSlice = {'minY': 1, 'maxY': self._rti.arrayShape[0]}
                XdimSlice = {'minX': 1, 'maxX': self._rti.arrayShape[1]}
        else:
            YdimSlice = {'minY': 1, 'maxY': self._rti.arrayShape[0]}
            XdimSlice = {'minX': 1, 'maxX': self._rti.arrayShape[1]}

        return YdimSlice, XdimSlice



    ##############
    #    Slot    #
    ##############

    @QtSlot(BaseRti)
    def setRti(self, rti):
        """ 
        Updates the current VisItem from the contents of the repo tree item.

        Is a slot but the signal is usually connected to the Collector, which then calls
        this function directly.
        """
        check_class(rti, BaseRti)
        if rti.nodePath in self._rtis:
            self.sigShowMessage.emit(f"<Collector.setRti> same rti was sent. Ignoring ...")
            return
        
        # check about the current rtis number
        # pop up the nRow=itemRow and reset everything
        if len(self._rtis) >= 1: # > 2 should never happen
            first_key = next(iter(self._rtis))
            del self._rtis[first_key] # delete the first item to mask space for the coming one
            del self._rtisInfo[first_key]
        
        self._rti = rti
        self._rtis[rti.nodePath] = rti
        itemRows = list(range(len(self._rtis)))
        self._clearAndSetAll(axesNames=[], itemRows=itemRows)


    @QtSlot(int)
    def _spinboxValueChanged(self, index, spinBox=None):
        """ called when a spin box value changed """
        if spinBox is None:
            spinBox = self.sender()
        assert spinBox, "spinBox not defined and not the sender"

        self._updateRtiInfo()
        logger.debug("{} sigContentsChanged signal (spinBox)"
                      .format("Blocked" if self.signalsBlocked() else "Emitting"))
        

    @QtSlot(int)
    def _axisComboBoxActivated(self, index, comboBox=None):
        """ Called when a axis combo box was changed by the user.
        """
        if comboBox is None:
            comboBox = self.sender()
        assert comboBox, "comboBox not defined and not the sender"

        blocked = self.blockChildrenSignals(True) # locked
        self._updateRtisInfo()
        logger.debug("{} sigContentsChanged signal (comboBox)"
                    .format("Blocked" if self.signalsBlocked() else "Emitting"))
        self.sigShowMessage.emit("_procComboBoxActivated: called, got {}".format(comboBox.currentText()))
        self.sigShowHistory.emit(
            {'field': 'success', 'desc': "clicked {} and applied.".format(comboBox.currentText())},
            {'color': COLOR_AXIS})
        self.blockChildrenSignals(blocked) # unlocked


    @QtSlot(int)
    def _procComboBoxActivated(self, index, comboBox=None):
        """ Called when a processing combo box was changed by the user.
        """
        if comboBox is None:
            comboBox = self.sender()
        assert comboBox, "comboBox not defined and not the sender"

        blocked = self.blockChildrenSignals(True) # locked
        self._updateRtisInfo()
        self.sigShowMessage.emit("_procComboBoxActivated: called, got {}".format(comboBox.currentText()))
        self.sigShowHistory.emit(
            {'field': 'success', 'desc': "clicked {} and applied.".format(comboBox.currentText())},
            {'color': COLOR_PROC})
        self.blockChildrenSignals(blocked) # unlocked

        # emit the signal and do the processing
        model = self.rti.model
        methodValue = comboBox.currentText()
        self.sigProcessingChanged.emit(methodValue, self.rti, model)
    

    @QtSlot(int, str)
    def _createMenuBtnAction(self, axisNr, axisName):
        print("axisNr, axisName = {}, {}".format(axisNr, axisName))
        dct = {'label': axisName,
               'min': 0, 
               'max':self._rti.arrayShape[axisNr]-1,
               'enabled': True if self._rti.arrayShape[axisNr]>1 else False}
        self.sigSpinderUpdates.emit(dct)


    @QtSlot()
    def _showMoreHistory(self):
        """ 
        Shows/Hides the detailed history widget.
        """
        # sanity check
        if not self._rti:
            logger.error("_showMoreHistory:: error, only when rti is not None, the btn can be activated.")
        else:
            self._histPanes.moreInfoBtn.setEnabled(False)
            # opens the information Dialog
            infoDialog = InfoDialog(config=self._rtiConfig, 
                                    parent=self, 
                                    _histories=self._histPanes._Histories)
            infoDialog.exec_()
            infoDialog.deleteLater() # schedules this object for deletion

            self._histPanes.moreInfoBtn.setEnabled(True)