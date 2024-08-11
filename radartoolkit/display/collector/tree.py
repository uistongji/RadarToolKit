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


""" Collector Tree Widget.
"""

import logging
import warnings
import numpy as np

from ..bindings import Qt, QtGui, QtWidgets
from ..settings import COLLECTOR_TREE_ICON_SIZE
from ..models.togglecolumn import ToggleColumnTreeView
from .qts import Spinder


logger = logging.getLogger(__name__)


class TreeUpdateReason(object):
    PROCESS_ITEM_CHANGED = "process item changed"
    DATA_SLICE_RANGE_CHANGED = "data slice range changed"



class CollectorTree(ToggleColumnTreeView):
    """ Tree widget for collecting the selected data. Includes an internal tree model.

        NOTE: this class is not meant to be used directly but is 'private' to the Collector().
        That is, plugins should interact with the Collector class, not the CollectorTree()
    """

    def __init__(self, parent=None):

        super(CollectorTree, self).__init__(parent=parent)

        # set as default values for the row and the column
        model = QtGui.QStandardItemModel(2, 1) # only set 2 available cells
        self.setModel(model)
        self.setTextElideMode(Qt.ElideMiddle) # ellipsis aprear in the middle of the text

        self.setRootIsDecorated(False) # disable expand/collapse triangle
        self.setUniformRowHeights(True)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setAnimated(True)
        self.setAllColumnsShowFocus(True)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.setIconSize(COLLECTOR_TREE_ICON_SIZE)

        treeHeader = self.header()
        treeHeader.setStretchLastSection(True) # false
        treeHeader.setSectionsMovable(False)

        treeHeader.resizeSection(0, 250) # for item path: treeHeader.resizeSection(0, 300)
        treeHeader.setSectionResizeMode(QtWidgets.QHeaderView.Interactive) # don't set to stretch

        labels = [''] * model.columnCount()
        labels[0] = 'Path'
        model.setHorizontalHeaderLabels(labels)

        # enabled, checked properties 
        # enabled = dict((name, False) for name in self.HEADERS)
        # checked = dict((name, True) for name in self.HEADERS)
        # self.addHeaderContextMenu(checked=checked, enabled=enabled, checkable={})


    def __repr__(self) -> str:
        return f"<{type(self).__name__}"
    

    def resizeColumnsFromContents(self, startCol=None):
        """ Resize columns depending on their contents.

            The width of the first column (showing the path) will not be changed
            The columns containing combo boxes will be set to the size hints of these combo boxes
            The remaining width (if any) is devided over the spin boxes.
            The last widget will be stretched and set to fit the collector size.
        """
        logger.debug(f"{self.__repr__()}:resizeColumnsFromContents> called.")
        numCols = self.model().columnCount()
        startCol = 0 if startCol is None else max(startCol, 0)

        # set columns with comboboxes to theri size hints.
        row = 0
        header = self.header()
        for col in range(startCol, numCols):
            indexWidget = self.indexWidget(self.model().index(row, col))
            if indexWidget:
                if isinstance(indexWidget, QtWidgets.QComboBox):
                    header.resizeSection(col, indexWidget.sizeHint().width())

        # collect size hints of spin boxes and indices of all other columns
        indexSpin = []
        indexNonSpin = []
        spinBoxSizeHints = []
        spinBoxMaximums = []
        for col in range(0, numCols):
            indexWidget = self.indexWidget(self.model().index(row, col))
            if indexWidget and isinstance(indexWidget, (QtWidgets.QSpinBox, Spinder)):
                spinBoxSizeHints.append(indexWidget.spinBox.sizeHint().width())
                spinBoxMaximums.append(max(0, indexWidget.spinBox.maximum()))
                indexSpin.append(col)
            else:
                indexNonSpin.append(col)

        headerWidth = self.header().width()
        spinBoxSizeHints = np.array(spinBoxSizeHints)
        spinBoxTotalSizeHints = np.sum(np.array(spinBoxSizeHints))
        colWidths = np.array([self.header().sectionSize(idx) for idx in range(numCols)])
        if len(indexSpin) == 0:
            remainingSize = max(0, headerWidth - np.sum(colWidths[0:numCols-1]))
            if remainingSize == 0:
                return
            header.resizeSection(numCols, round(remainingSize))
            return

        nonSpinBoxTotalWidth = np.sum(colWidths[indexNonSpin])
        remainingTotal = max(0, headerWidth - nonSpinBoxTotalWidth - spinBoxTotalSizeHints)


        with warnings.catch_warnings():
            # Ignore divide by zero warnings when all elements have the same value
            warnings.simplefilter("ignore")
            spinBoxWeights = np.maximum(0.5, np.log10(np.array(spinBoxMaximums)))
            normSpinBoxWeights = spinBoxWeights / np.sum(spinBoxWeights)
            extraWidthPerSpinBox = remainingTotal * normSpinBoxWeights
            newSpinBoxWidths = spinBoxSizeHints + extraWidthPerSpinBox

        logger.debug("Dividing the remaining width over the spinboxes.")
        logger.debug("Header width               : {}".format(headerWidth))
        logger.debug("Column widths              : {}".format(colWidths))
        logger.debug("Width of non-spinboxes     : {}".format(nonSpinBoxTotalWidth))
        logger.debug("Total size hint spinboxes  : {}".format(spinBoxTotalSizeHints))
        logger.debug("Remaining width to divide  : {}".format(remainingTotal))
        logger.debug("Spinbox maximums           : {}".format(spinBoxMaximums))
        logger.debug("Normalized spinbox weights : {}".format(normSpinBoxWeights))
        logger.debug("Extra width per spin box   : {}".format(extraWidthPerSpinBox))
        logger.debug("New spinbox widths         : {}".format(newSpinBoxWidths))

        # Divide the remaining width over the spin boxes using the log(nrElements) as weights.
        # If the remaining total is less than zero, just set the widths to the size hints (a
        # horizontal scrollbar will appear).
        for idx, newWidth in zip(indexSpin, newSpinBoxWidths):
            header.resizeSection(idx, round(newWidth))





################### Processing Parameters Tree Widget ###################