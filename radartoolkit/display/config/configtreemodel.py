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


from ..bindings import QtCore, Qt
from ..models.treemodels import BaseTreeModel
from .ctis.abstractcti import ResetMode, DEFAULT_RESET_MODE
from .ctis.groupcti import MainGroupCti
from .utils import type_name
from ..utils.check_class import check_class

import logging
logger = logging.getLogger(__name__)


class ConfigTreeModel(BaseTreeModel):
    """ An implementation QAbstractItemModel that offers access to configuration data for QTreeViews.
        The underlying data is stored as config tree items (AbstractCti descendants)
    """
    HEADERS = ["Name", "Path", "Value", "Default value", "Item class", "Debug info"]
    (COL_NODE_NAME, COL_NODE_PATH,
     COL_VALUE, COL_DEF_VALUE,
     COL_CTI_TYPE, COL_DEBUG) = range(len(HEADERS))

    COL_DECORATION = COL_VALUE  # Column number that contains the decoration.

    INVISIBLE_ROOT_NAME = '<invisible-root>'

    def __init__(self, parent=None):
        """ Constructor
        """
        super(ConfigTreeModel, self).__init__(parent=parent)

        self._autoReset = True
        self._resetMode = DEFAULT_RESET_MODE

        self._invisibleRootTreeItem = MainGroupCti(self.INVISIBLE_ROOT_NAME)
        self._invisibleRootTreeItem.model = self
        # self.dataChanged.connect(self.debug)
        self._refreshBlocked = False

    def flags(self, index):
        """ Returns the item flags for the given index.
        """
        if not index.isValid():
            return 0

        cti = self.getItem(index)

        result = Qt.ItemIsSelectable

        if cti.enabled:
            result |= Qt.ItemIsEnabled

        if index.column() == self.COL_VALUE:
            result |= cti.valueColumnItemFlags

        return result

    def itemData(self, treeItem, column, role=Qt.DisplayRole):
        """ Returns the data stored under the given role for the item.
        """
        if role == Qt.DisplayRole:
            if column == self.COL_NODE_NAME:
                return treeItem.nodeName
            elif column == self.COL_NODE_PATH:
                return treeItem.nodePath
            elif column == self.COL_VALUE:
                return treeItem.displayValue
            elif column == self.COL_DEF_VALUE:
                return treeItem.displayDefaultValue
            elif column == self.COL_CTI_TYPE:
                return type_name(treeItem)
            elif column == self.COL_DEBUG:
                return treeItem.debugInfo
            else:
                raise ValueError("Invalid column: {}".format(column))

        elif role == Qt.EditRole:
            if column == self.COL_VALUE:
                return treeItem.data
            else:
                raise ValueError("Invalid column: {}".format(column))

        elif role == Qt.ToolTipRole:
            if column == self.COL_NODE_NAME or column == self.COL_NODE_PATH:
                return treeItem.nodePath
            elif column == self.COL_VALUE:
                # Give Access to exact values. In particular in scientific-notation spin boxes
                return repr(treeItem.configValue)
            elif column == self.COL_DEF_VALUE:
                return treeItem.displayDefaultValue
            elif column == self.COL_CTI_TYPE:
                return type_name(treeItem)
            elif column == self.COL_DEBUG:
                return treeItem.debugInfo
            else:
                return None

        elif role == Qt.CheckStateRole:
            if column != self.COL_VALUE:
                # The CheckStateRole is called for each cell so return None here.
                return None
            else:
                return treeItem.checkState
        else:
            return super(ConfigTreeModel, self).itemData(treeItem, column, role=role)

    def setItemData(self, treeItem, column, value, role=Qt.EditRole):
        """ Sets the role data for the item at index to value.
        """
        if role == Qt.CheckStateRole:
            if column != self.COL_VALUE:
                return False
            else:
                logger.debug("Setting check state (col={}): {!r}".format(column, value))
                treeItem.checkState = value
                return True

        elif role == Qt.EditRole:
            if column != self.COL_VALUE:
                return False
            else:
                logger.debug("Set Edit value (col={}): {!r}".format(column, value))
                treeItem.data = value
                return True
        else:
            raise ValueError("Unexpected edit role: {}".format(role))

    def setExpanded(self, index, expanded):
        """ Expands the model item specified by the index.
            Overridden from QTreeView to make it persistent (between inspector changes).
        """
        if index.isValid():
            item = self.getItem(index)
            item.expanded = expanded
            # logger.debug("Setting expanded = {} for {}".format(expanded, item))

    def expand(self, index):
        """ Expands the model item specified by the index.
            Overridden from QTreeView to make it persistent (between inspector changes).
        """
        self.setExpanded(index, True)

    def collapse(self, index):
        """ Expands the model item specified by the index.
            Overridden from QTreeView to make it persistent (between inspector changes).
        """
        self.setExpanded(index, False)

    def indexTupleFromItem(self, treeItem):
        """ Return (first column model index, last column model index) tuple for a configTreeItem
        """
        if not treeItem:
            return (QtCore.QModelIndex(), QtCore.QModelIndex())

        if not treeItem.parentItem: 
            return (QtCore.QModelIndex(), QtCore.QModelIndex())

        # Is there a bug in Qt in QStandardItemModel::indexFromItem?
        # It passes the parent in createIndex.

        row = treeItem.childNumber()
        return (self.createIndex(row, 0, treeItem),
                self.createIndex(row, self.columnCount() - 1, treeItem))

    def emitDataChanged(self, treeItem): 
        """ Emits the data changed for the model indices (all columns) for this treeItem
        """
        indexLeft, indexRight = self.indexTupleFromItem(treeItem)
        self.dataChanged.emit(indexLeft, indexRight)

    def getRefreshBlocked(self):
        """ If set the configuration should not be updated.
            This setting is part of the model so that is shared by all CTIs.
        """
        return self._refreshBlocked

    def setRefreshBlocked(self, blocked):
        """ Set to True to indicate that set the configuration should not be updated.
            This setting is part of the model so that is shared by all CTIs.
            Returns the old value.
        """
        wasBlocked = self._refreshBlocked
        logger.debug("Setting refreshBlocked from {} to {}".format(wasBlocked, blocked))
        self._refreshBlocked = blocked
        return wasBlocked

    @property
    def autoReset(self):
        """ Indicates that the model will be (oartially) reset when the RTI or combo change
        """
        return self._autoReset

    @autoReset.setter
    def autoReset(self, value):
        """ Indicates that the model will be (oartially) reset when the RTI or combo change
        """
        self._autoReset = value

    @property
    def resetMode(self):
        """ Determines what is reset if autoReset is True (either axes or all settings)
        """
        return self._resetMode

    @resetMode.setter
    def resetMode(self, value):
        """ Determines what is reset if autoReset is True (either axes or all settings)
        """
        check_class(value, ResetMode)
        self._resetMode = value

    def resetAllSettings(self):
        """ Resets all items in the tree to their default
        """
        logger.debug("Resetting all settings")
        self.invisibleRootTreeItem.resetToDefault(resetChildren=True)
        self.emitDataChanged(self.invisibleRootTreeItem)  # Updates the tree
        self.sigItemChanged.emit(self.invisibleRootTreeItem)  # Updates the inspector

    def resetAllRanges(self):
        """ Resets all (axit/color/ect) range items in the tree to their default
        """
        logger.debug("Resetting all settings")
        self.invisibleRootTreeItem.resetRangesToDefault()
        self.emitDataChanged(self.invisibleRootTreeItem)  # Updates the tree
        self.sigItemChanged.emit(self.invisibleRootTreeItem)  # Updates the inspector
