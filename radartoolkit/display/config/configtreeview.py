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


from .ctis.abstractcti import ResetMode
from ..config.configitemdelegate import ConfigItemDelegate
from ..config.configtreemodel import ConfigTreeModel
from ..bindings import QtWidgets, QtCore, QtGui, QtSlot
from ..widgets.basepanel import BasePanel
from ..models.rtktreeview import RTKTreeView
from ..settings import DOCK_MARGIN, DOCK_SPACING, ICONS_DIR, RIGHT_DOCK_WIDTH
import logging
import os.path

logger = logging.getLogger(__name__)


class ConfigWidget(BasePanel):

    def __init__(self, configTreeModel, parent=None):

        super(ConfigWidget, self).__init__(parent=parent)

        self.modeActionGroup = QtGui.QActionGroup(self)
        self.modeActionGroup.setExclusive(True)

        self.modeAllAction = QtGui.QAction("Reset All", self.modeActionGroup)
        self.modeAllAction.setToolTip("Changes button reset mode to reset all settings")
        self.modeAllAction.setCheckable(True)
        self.modeAllAction.triggered.connect(lambda: self.setResetMode(ResetMode.All))

        self.modeRangeAction = QtGui.QAction("Reset Ranges", self.modeActionGroup)
        self.modeRangeAction.setToolTip("Changes button reset mode to reset axes")
        self.modeRangeAction.setCheckable(True)
        self.modeRangeAction.triggered.connect(lambda: self.setResetMode(ResetMode.Ranges))

        # Sanity check that actions have been added to action group
        assert self.modeActionGroup.actions(), "Sanity check. resetActionGroup is empty"

        self.resetAllAction = QtGui.QAction("Reset All", self)
        self.resetAllAction.setToolTip("Resets all settings.")
        self.resetAllAction.setIcon(QtGui.QIcon(os.path.join(ICONS_DIR, 'reset.png')))
        self.resetAllAction.setShortcut("Ctrl+=")

        self.resetRangesAction = QtGui.QAction("Reset Ranges", self)
        self.resetRangesAction.setToolTip(
            "Resets range of all plots, color scales, table column/row sizes etc.")
        self.resetRangesAction.setIcon(QtGui.QIcon(os.path.join(ICONS_DIR, 'reset.png')))
        self.resetRangesAction.setShortcut("Ctrl+0")

        self.resetButtonMenu = QtWidgets.QMenu()
        self.resetButtonMenu.addAction(self.resetAllAction)
        self.resetButtonMenu.addAction(self.resetRangesAction)
        self.resetButtonMenu.addSection("Default")
        self.resetButtonMenu.addAction(self.modeAllAction)
        self.resetButtonMenu.addAction(self.modeRangeAction)

        """ Widgets.
        """
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setSpacing(DOCK_SPACING)
        self.mainLayout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)
        self.configTreeView = ConfigTreeView(configTreeModel, parent=self)
        self.mainLayout.addWidget(self.configTreeView)

        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addLayout(self.buttonLayout)

        self.autoCheckBox = QtWidgets.QCheckBox("Auto")
        self.autoCheckBox.setToolTip("Auto reset when a new item or axis is selected.")
        self.autoCheckBox.setChecked(True)

        self.resetButton = QtWidgets.QToolButton()
        self.resetButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.resetButton.setDefaultAction(self.resetButtonMenu.defaultAction())
        self.resetButton.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
        self.resetButton.setMenu(self.resetButtonMenu)

        # Set font size to the same as used for push buttons
        dummyButton = QtWidgets.QPushButton("dummy")
        fontSize = dummyButton.font().pointSize()
        del dummyButton

        logger.debug("Setting QToolButtons font size to: {} point".format(fontSize))
        font = self.resetButton.font()
        font.setPointSizeF(fontSize)
        self.resetButton.setFont(font)

        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.autoCheckBox)
        self.buttonLayout.addWidget(self.resetButton)
        self.buttonLayout.addStretch()

        self.autoCheckBox.stateChanged.connect(self.setAutoReset)
        self.resetRangesAction.triggered.connect(self.configTreeView.resetAllRanges)
        self.resetAllAction.triggered.connect(self.configTreeView.resetAllSettings)

        self.setResetMode(self.configTreeView.resetMode)


    def setAutoReset(self, value):
        self.configTreeView.autoReset = value


    def setResetMode(self, resetMode):
        if resetMode == ResetMode.All:
            self.resetButton.setDefaultAction(self.resetAllAction)
            self.modeAllAction.setChecked(True)
        elif resetMode == ResetMode.Ranges:
            self.resetButton.setDefaultAction(self.resetRangesAction)
            self.modeRangeAction.setChecked(True)
        else:
            raise ValueError("Unexpected resetMode: {}".format(resetMode))

        self.configTreeView.resetMode = resetMode


    def marshall(self):

        cfg = dict(
            autoRange=self.autoCheckBox.isChecked(),
            resetMode=self.configTreeView.resetMode.value,
        )
        return cfg


    def unmarshall(self, cfg):

        if 'autoRange' in cfg:
            self.autoCheckBox.setChecked(cfg['autoRange'])

        if 'resetMode' in cfg:
            self.setResetMode(ResetMode(cfg['resetMode']))




class ConfigTreeView(RTKTreeView):
    """ Tree widget for manipulating a tree of configuration options.
    """

    def __init__(self, configTreeModel, parent=None):

        super(ConfigTreeView, self).__init__(treeModel=configTreeModel, parent=parent)

        self._configTreeModel = configTreeModel

        self.expanded.connect(configTreeModel.expand)
        self.collapsed.connect(configTreeModel.collapse)

        treeHeader = self.header()
        treeHeader.resizeSection(ConfigTreeModel.COL_NODE_NAME, round(RIGHT_DOCK_WIDTH * 0.5))
        treeHeader.resizeSection(ConfigTreeModel.COL_VALUE, round(RIGHT_DOCK_WIDTH * 0.5))

        headerNames = self.model().horizontalHeaders
        enabled = dict((name, True) for name in headerNames)
        enabled[headerNames[ConfigTreeModel.COL_NODE_NAME]] = False  # Name cannot be unchecked
        enabled[headerNames[ConfigTreeModel.COL_VALUE]] = False  # Value cannot be unchecked
        checked = dict((name, False) for name in headerNames)
        checked[headerNames[ConfigTreeModel.COL_NODE_NAME]] = True  # Checked by default
        checked[headerNames[ConfigTreeModel.COL_VALUE]] = True  # Checked by default
        self.addHeaderContextMenu(checked=checked, enabled=enabled, checkable={})

        self.setRootIsDecorated(True)
        self.setUniformRowHeights(True)
        self.setItemDelegate(ConfigItemDelegate())
        self.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)

    def sizeHint(self):
        return QtCore.QSize(RIGHT_DOCK_WIDTH, 500)


    @QtSlot(QtWidgets.QWidget, QtWidgets.QAbstractItemDelegate.EndEditHint)
    def closeEditor(self, editor, hint):
        """ Finalizes, closes and releases the given editor.
        """
        # It would be nicer if this method was part of ConfigItemDelegate since createEditor also
        # lives there. However, QAbstractItemView.closeEditor is sometimes called directly,
        # without the QAbstractItemDelegate.closeEditor signal begin emitted, e.g when the
        # currentItem changes. Therefore we cannot connect the QAbstractItemDelegate.closeEditor
        # signal to a slot in the ConfigItemDelegate.
        configItemDelegate = self.itemDelegate()
        configItemDelegate.finalizeEditor(editor)

        super(ConfigTreeView, self).closeEditor(editor, hint)


    def expandBranch(self, index=None, expanded=True):
        """ Expands or collapses the node at the index and all it's descendants.
            If expanded is True the nodes will be expanded, if False they will be collapsed, and if
            expanded is None the expanded attribute of each item is used.
            If parentIndex is None, the invisible root will be used (i.e. the complete forest will
            be expanded).
        """
        configModel = self.model()
        if index is None:
            # index = configTreeModel.createIndex()
            index = QtCore.QModelIndex()

        if index.isValid():
            if expanded is None:
                item = configModel.getItem(index)
                self.setExpanded(index, item.expanded)
            else:
                self.setExpanded(index, expanded)

        for rowNr in range(configModel.rowCount(index)):
            childIndex = configModel.index(rowNr, configModel.COL_NODE_NAME, parentIndex=index)
            self.expandBranch(index=childIndex, expanded=expanded)


    @property
    def autoReset(self):
        """ Indicates that the model will be (oartially) reset when the RTI or combo change
        """
        return self._configTreeModel.autoReset

    @autoReset.setter
    def autoReset(self, value):
        """ Indicates that the model will be (oartially) reset when the RTI or combo change
        """
        self._configTreeModel.autoReset = value

    @property
    def resetMode(self):
        """ Determines what is reset if autoReset is True (either axes or all settings)
        """
        return self._configTreeModel.resetMode

    @resetMode.setter
    def resetMode(self, value):
        """ Determines what is reset if autoReset is True (either axes or all settings)
        """
        self._configTreeModel.resetMode = value

    def resetAllSettings(self):
        """ Resets all settings
        """
        logger.debug("Resetting all settings")
        self._configTreeModel.resetAllSettings()

    def resetAllRanges(self):
        """ Resets all (axis/color/etc) range settings.
        """
        logger.debug("Resetting all range settings")
        self._configTreeModel.resetAllRanges()
