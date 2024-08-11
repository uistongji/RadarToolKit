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


""" Base display pane for file items.
"""

import logging
import numpy as np

from ..bindings import QtWidgets, QtCore, QtGui, Qt
from ..settings import DEBUGGING, DOCK_MARGIN, DOCK_SPACING, LEFT_DOCK_WIDTH
from ..widgets.basepanel import BasePanel
from ..models.togglecolumn import ToggleColumnTableWidget
from ..utils.check_class import check_class
from ..utils.constants import MONO_FONT, FONT_SIZE
from display.rti.baserti import BaseRti
from ..rti.filetreemodel import FileTreeModel
from ..utils.misc import replaceEolChars


logger = logging.getLogger(__name__)


class BasePane(BasePanel):
    """ 
    Base class for plugins that show details of the current file tree item.
    """

    _label = "Details"

    def __init__(self, fileTreeView, parent=None):
        """ Constructor takes a reference to the file tree view it monitors
        """
        super(BasePane, self).__init__(parent=parent)

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
    
    

class BaseTablePane(BasePane):
    """ Base class for inspectors that consist of a single QTableWidget
    """
    _label = "Details Table"
    HEADERS = []

    def __init__(self, fileTreeView=None, parent=None):
        
        super(BaseTablePane, self).__init__(fileTreeView, parent=parent)

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




class DerivativesPane(BasePane):
    """ Widgets that holds the derivates, namely the QuickLook & Connections,
        which controls by the buttonMenu.
    """
    _label = "Derivatives"
    FIRST_SUBPANE_LABEL = '<Select Sub-Derivatives Pane>'
    SUBPANE_LABELS = ["Quick Look", "Connections"]

    def __init__(self, fileTreeView, parent=None):
        super(DerivativesPane, self).__init__(fileTreeView, parent=parent)

        self.menuButton = QtWidgets.QPushButton(self.FIRST_SUBPANE_LABEL)
        self.menuButton.setMinimumWidth(20)
        self.menuButton.setMaximumHeight(21)
        derivsMenu = QtWidgets.QMenu("Select Derivatives", parent=self.menuButton)
        
        # setup actions
        actionGroup = QtGui.QActionGroup(self)
        actionGroup.setExclusive(True)

        self.quickLookAction = QtGui.QAction(self.SUBPANE_LABELS[0], self, checkable=True)
        self.quickLookAction.triggered.connect(self._updateQuickLookFromBtnMenu)
        actionGroup.addAction(self.quickLookAction)

        self.connectAction = QtGui.QAction(self.SUBPANE_LABELS[1], self, checkable=True)
        self.connectAction.triggered.connect(self._updateConnectFromBtnMenu)
        actionGroup.addAction(self.connectAction)

        for action in actionGroup.actions():
            derivsMenu.addAction(action)
        self.menuButton.setMenu(derivsMenu)

        self.derivPane = QtWidgets.QStackedWidget(self)
        self.quickLookPane = QuickLookPane(fileTreeView)
        self.connectionPane = ConnectionsPane(fileTreeView)

        self.derivPane.addWidget(self.quickLookPane)
        self.derivPane.addWidget(self.connectionPane)

        vLayout = QtWidgets.QVBoxLayout()
        vLayout.addWidget(self.menuButton)
        vLayout.addWidget(self.derivPane)
        self.contentsLayout.addLayout(vLayout)

    def _drawContents(self, currentRti=None, _index=None):
        
        if _index is None:
            self.menuButton.setText(self.FIRST_SUBPANE_LABEL)
        else:
            self.menuButton.setText(self.SUBPANE_LABELS[_index-1])

        self._currentRti = currentRti
        if self._currentRti is None:
            self.quickLookPane.editor.clear()
            # self.connectionPane.canvas.clear() # 
        else:
            widget = self.derivPane.widget(_index)
            widget._drawContents(self._currentRti)
            self.derivPane.setCurrentIndex(_index)
            
    def _updateQuickLookFromBtnMenu(self):
        index = 1
        if self.derivPane.currentIndex() == index:
            return
        else:
            self._drawContents(_index=index)
    
    def _updateConnectFromBtnMenu(self):
        index = 2
        if self.derivPane.currentIndex() == index:
            return 
        else:
            self._drawContents(_index=index)



class QuickLookPane(BasePane):
    """ Shows the string representation of the RTI contents.
    """
    _label = "Quick Look"

    def __init__(self, fileTreeView, parent=None):
        super(QuickLookPane, self).__init__(fileTreeView, parent=parent)

        self._currentRti = None

        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.editor.setFont(QtGui.QFont(MONO_FONT, FONT_SIZE))

        self.contentsLayout.addWidget(self.editor)

    def _drawContents(self, currentRti=None):
        """ Draws the attributes of the currentRTI
        """
        self._currentRti = currentRti
        if self._currentRti is None:
            self.editor.clear()
        else:
            editorCharWidth =  self.editor.width() / self.editor.fontMetrics().averageCharWidth()
            oldLineWidth = np.get_printoptions()['linewidth']
            np.set_printoptions(linewidth=editorCharWidth)
            try:
                self.editor.setPlainText(self._currentRti.quickLook(editorCharWidth))
            finally:
                np.set_printoptions(linewidth=oldLineWidth)

    def resizeEvent(self, event):
        """ Called when the panel is resized. Will update the line length of the editor.
        """
        self.itemChanged(self._currentRti) # call itemChanged so it handles exceptions
        super(QuickLookPane, self).resizeEvent(event)



class ConnectionsPane(BasePane):
    """ Shows the connections of the currently selected RTI.
    """
    def __init__(self, fileTreeView, parent=None):
        super(ConnectionsPane, self).__init__(fileTreeView, parent=parent)

        self.canvas = QtWidgets.QWidget()
        self.contentsLayout.addWidget(self.canvas)



class PropertiesPane(BaseTablePane):
    """ Shows the properties of the currently selected file tree item.
    """
    _label = "Properties"

    HEADERS = ["Name", "Value"] 
    (COL_PROP_NAME, COL_VALUE) = range(len(HEADERS))

    def __init__(self, fileTreeView, parent=None):
        super(PropertiesPane, self).__init__(fileTreeView, parent=parent)

        self.table.addHeaderContextMenu(
            enabled={'Name': False, 'Value': False}) # diables action
        self.table.setTextElideMode(Qt.ElideMiddle)

        tableHeader = self.table.horizontalHeader()
        tableHeader.resizeSection(self.COL_PROP_NAME, 120)
        tableHeader.resizeSection(self.COL_VALUE, 160)

    def _drawContents(self, currentRti=None):
        """ draws the properties of the currentRti """
        table = self.table
        table.setUpdatesEnabled(False)
        try:
            table.clearContents()
            verticalHeader = table.verticalHeader()
            verticalHeader.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

            if currentRti is None:
                return
            
            fileModel = self._fileTreeView.model()
            propNames = FileTreeModel.HEADERS
            table.setRowCount(len(propNames))

            for row, propName in enumerate(propNames):
                nameItem = QtWidgets.QTableWidgetItem(propName)
                nameItem.setToolTip(propName)
                table.setItem(row, self.COL_PROP_NAME, nameItem)
                itemDataText = replaceEolChars(fileModel.itemData(currentRti, row))
                propItem = QtWidgets.QTableWidgetItem(itemDataText)
                propItem.setToolTip(fileModel.itemData(currentRti, row, role=Qt.ToolTipRole))
                table.setItem(row, self.COL_VALUE, propItem)
                table.resizeRowToContents(row)

            verticalHeader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        finally:
            table.setUpdatesEnabled(True)




class RelativesPane(BaseTablePane):
    """ Shows the relatives of the currently selected file tree item.
        :: Information requires database to provide
    """
    _label = "Relatives"

    HEADERS = ["Name", "Value"]
    (COL_RELAT_NAME, COL_VALUE) = range(len(HEADERS))

    RELATIVES_NAME = ["Project", "Set", "Transect", "Stream", "Area", 
                      "Status",  "Source"] 
    # Status: unknown source / archived source from the database 
    #         returns [unknown]/[archived]
    # ----------------------------------------------------------
    # Source: (unknown)  operated and loaded by user
    #         (archived) detected and loaded from the database

    def __init__(self, fileTreeView, parent=None):
        super(RelativesPane, self).__init__(fileTreeView, parent)

        self.table.addHeaderContextMenu(
            enabled={'Name': False, 'Value': False}) # diables action
        self.table.setTextElideMode(Qt.ElideMiddle)

        tableHeader = self.table.horizontalHeader()
        tableHeader.resizeSection(self.COL_RELAT_NAME, 120)
        tableHeader.resizeSection(self.COL_VALUE, 160)

    def _drawContents(self, currentRti=None):
        """ draws the relatives of the currentRti """
        table = self.table
        table.setUpdatesEnabled(False)
        try:
            table.clearContents()
            verticalHeader = table.verticalHeader()
            verticalHeader.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

            if currentRti is None:
                return
            
            fileModel = self._fileTreeView.model()
            table.setRowCount(len(self.RELATIVES_NAME))

            for row, relatName in enumerate(self.RELATIVES_NAME):
                nameItem = QtWidgets.QTableWidgetItem(relatName)
                nameItem.setToolTip(relatName)
                table.setItem(row, self.COL_RELAT_NAME, nameItem)
                # setup the value item
                if relatName not in fileModel.itemRelatives(currentRti):
                    itemDataText = ''
                else:
                    itemDataText = fileModel.itemRelatives(currentRti)[relatName]
                relatItem = QtWidgets.QTableWidgetItem(itemDataText)
                table.setItem(row, self.COL_VALUE, relatItem)
                table.resizeRowToContents(row)
            
            verticalHeader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        finally:
            table.setUpdatesEnabled(True)
        







