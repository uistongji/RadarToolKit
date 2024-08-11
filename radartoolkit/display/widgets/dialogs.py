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


import logging
import copy
import os

from display.bindings import QtCore, QtWidgets, QtGui, QtSlot, QtSignal
from display.settings import ICONS_DIR
from display.utils.constants import MONO_FONT, FONT_SIZE
from display.reg.tabmodel import TableInfoModel
from display.reg.tabview import TableInfoViewer


logger = logging.getLogger(__name__)
curFileName = os.path.basename(__file__)



class PluginsDialog(QtWidgets.QDialog):
    """ Dialog window that allows users to configure the installed plugins.
    """

    def __init__(self, label, registry,  parent=None):
        super(PluginsDialog, self).__init__(parent=parent)



class InfoDialog(QtWidgets.QDialog):
    """ Dialog window shows the collector related information
    """

    def __init__(self, config=None, parent=None, _histories=[]):
        super(InfoDialog, self).__init__(parent=parent)

        self._config = config
        self._histories = _histories

        self.resize(QtCore.QSize(800, 600))

        # setup the window title
        self.setWindowTitle("More Of Collector")

        layout = QtWidgets.QHBoxLayout(self)

        # setup the detailed information widget
        font = QtGui.QFont()
        font.setFamily(MONO_FONT)
        font.setFixedPitch(True)
        font.setPointSize(FONT_SIZE)

        self.editor = QtWidgets.QTextEdit()
        self.editor.setReadOnly(True)
        
        self.editor.setWordWrapMode(QtGui.QTextOption.WordWrap)
        self.editor.clear()

        # setup the main view
        self._tableModel = TableInfoModel(self._histories)
        self.tableView = TableInfoViewer(self._tableModel)
        
        self.colConfigWidget = ColConfigWidget()
        self.colConfigWidget._configTreeModel.setInvisibleRootItem(self._config)

        self.saveBtn = QtWidgets.QPushButton("Save")
        self.saveBtn.clicked.connect(self.accept)

        self.cancelBtn = QtWidgets.QPushButton("Cancel")
        self.cancelBtn.clicked.connect(self.reject)

        # We use a button layout instead of a QButtonBox because there always will be a default
        # button (e.g. the Save button) that will light up, even if another widget has the focus.
        # From https://doc.qt.io/archives/qt-4.8/qdialogbuttonbox.html#details
        #   However, if there is no default button set and to preserve which button is the default
        #   button across platforms when using the QPushButton::autoDefault property, the first
        #   push button with the accept role is made the default button when the QDialogButtonBox
        #   is shown,

        self.btnsLayout = QtWidgets.QHBoxLayout()
        self.btnsLayout.addWidget(self.cancelBtn)
        self.btnsLayout.addWidget(self.saveBtn)

        # layout of the right pane
        vrlayout = QtWidgets.QVBoxLayout()
        vrlayout.addWidget(self.colConfigWidget)
        vrlayout.addLayout(self.btnsLayout)

        # layout of the left pane
        vllayout = QtWidgets.QVBoxLayout() 
        vllayout.addWidget(self.tableView)
        vllayout.addWidget(self.editor)

        layout.addLayout(vllayout)
        layout.addLayout(vrlayout)

        # --- connect signal-slot --- #
        self.tableView.selectionModel().currentChanged.connect(self.currentItemChanged)
        self.tableView.model().sigItemChanged.connect(self._updateEditor)

        self.tableView.setFocus(QtCore.Qt.NoFocusReason)


    def __repr__(self) -> str:
        return f"<{curFileName}:{type(self).__name__}"
    
    
    def accept(self):
        """ Saves changes of the parameters, e.g., processing, roi, ...
        """

        logger.debug(f"{self.__repr__()}:accept> called. Updating from the changes.")
        pass


    def getCurrentRegItem(self):
        """ Returns the item that is currently selected in the table.
            Can return None if there is no data in the table
        """

        return self.tableView.getCurrentItem()
    

    @QtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def currentItemChanged(self, currentIndex=None, _previousIndex=None):
        """ Updates the description text widget when the user clicks on a selector in the table.
            The _currentIndex and _previousIndex parameters are ignored.
        """

        regItem = self.getCurrentRegItem()
        self._updateEditor(regItem)
    
    
    def _updateEditor(self, infoItem=None):
        """ Updates the editor with contents of the currently selected information
        """

        self.editor.clear()

        if infoItem is None:
            return
        else:
            header = "<h3>{}</h3>".format(infoItem._headerText)
            self.editor.setHtml("{}{}<br>{}".\
                format(header, infoItem._statusTexts, infoItem._detailedTexts))