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


""" Base class for pane that shows the information of the currently selected RTI.
"""

from ..bindings import QtWidgets, QtCore
from radartoolkit.display.rti.baserti import BaseRti
from ..models.togglecolumn import ToggleColumnTableWidget
from ..utils.check_class import check_class
from ..widgets.basepanel import BasePanel
from ..settings import DEBUGGING, DOCK_MARGIN, DOCK_SPACING, LEFT_DOCK_WIDTH

import logging

logger = logging.getLogger(__name__)

class DetailBasePane(BasePanel):

    _label = "Details"

    def __init__(self, fileTreeView, parent=None):
        
        super(DetailBasePane, self).__init__()

        self._isConnected = False
        self._fileTreeView = fileTreeView
        
        self.contentsLayout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom)
        self.contentsLayout.setSpacing(DOCK_SPACING)
        self.contentsLayout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)
        self.setLayout(self.contentsLayout)

    @classmethod
    def classLabel(cls):
        return cls._label
    
    @property
    def isConnected(self):
        "Returns True if this pane is connected to the currentChanged signal of the fileTreeView"
        return self._isConnected

    def sizeHint(self):
        """ The recommended size for the widget."""
        return QtCore.QSize(LEFT_DOCK_WIDTH, 250)

    def itemChanged(self, rti):
        """ Updates the content when the current repo tree item changes.
            The rti parameter can be None when no RTI is selected in the repository tree.
        """
        check_class(rti, (BaseRti, int), allow_none=True)
        assert type(rti) != int, "rti: {}".format(rti)
        try:
            self._drawContents(rti)
        except Exception as ex:
            if DEBUGGING:
                raise
            logger.exception(ex)

    def _drawContents(self, currentRti=None):
        """ Draws the contents for the current RTI. Descendants should override this.
            Descendants should draw 'empty' contents if currentRti is None. No need to
            handle exceptions though, these are handled by the called (currentChanged).
        """
        pass

    def marshall(self):
        """ Returns a dictionary to save in the persistent settings
        """
        raise NotImplementedError("Not implemented. Please override")

    def unmarshall(self, cfg):
        """ Initializes itself from a config dict form the persistent settings.
        """
        raise NotImplementedError("Not implemented. Please override")



class DetailTablePane(DetailBasePane):
    """ Base class for inspectors that consist of a single QTableWidget
    """
    _label = "Details Table"

    HEADERS = []

    def __init__(self, fileTreeView=None, parent=None):
        
        super(DetailTablePane, self).__init__(fileTreeView, parent=parent)

        self.table = ToggleColumnTableWidget()
        self.contentsLayout.addWidget(self.table)

        self.table.setWordWrap(False)
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("alternate-background-color: #F5F5F5; background-color: white")
        
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        tableHeader = self.table.horizontalHeader()
        tableHeader.setSectionResizeMode(QtWidgets.QHeaderView.Interactive) # don't set to stretch
        tableHeader.setStretchLastSection(True)

    def marshall(self):
        """ Returns a dictionary to save in the persistent settings
        """
        cfg = dict(tableHeaders=self.table.marshall())
        return cfg

    def unmarshall(self, cfg):
        """ Initializes itself from a config dict form the persistent settings.
        """
        self.table.unmarshall(cfg.get('tableHeaders'))

