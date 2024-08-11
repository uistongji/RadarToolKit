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


from .abstractcti import AbstractCti
from .groupcti import GroupCtiEditor
from ...bindings import Qt
import logging

logger = logging.getLogger(__name__)


class BoolCti(AbstractCti):
    """ Config Tree Item to store an boolean. It can be edited using a check box
    """

    def __init__(self, nodeName, defaultData, expanded=True,
                 childrenDisabledValue=False):
        """ Constructor. For the parameters see the AbstractCti constructor documentation.

            If the data is equal to childrenDisabledValue, the node's children will be
            disabled.

            (The data will always be a bool so if childrenDisabledValue == None,
            the children will never be disabled.)
        """
        super(BoolCti, self).__init__(nodeName, defaultData, expanded=expanded)
        self.childrenDisabledValue = childrenDisabledValue

    @property
    def debugInfo(self):
        """ Returns a string with debugging information
        """
        return "{} (enabled={}, childDisabledVal={})".format(self.configValue, self.enabled,
                                                             self.childrenDisabledValue)

    def _enforceDataType(self, data):
        """ Converts to bool so that self.data always is of that type.
        """
        return bool(data)

    @property
    def data(self):
        """ Returns the data of this item.
        """
        return self._data

    @data.setter
    def data(self, data):
        """ Sets the data of this item.
            Does type conversion to ensure data is always of the correct type.
        """
        # Descendants should convert the data to the desired type here
        self._data = self._enforceDataType(data)

        # logger.debug("BoolCti.setData: {} for {}".format(data, self))
        enabled = self.enabled
        self.enableBranch(enabled and self.data != self.childrenDisabledValue)
        self.enabled = enabled

    @property
    def displayValue(self):
        """ Returns empty string since a checkbox will displayed in the value-column instead.
        """
        return ""

    def insertChild(self, childItem, position=None):
        """ Inserts a child item to the current item.

            Overridden from BaseTreeItem.
        """
        childItem = super(BoolCti, self).insertChild(childItem, position=None)

        enableChildren = self.enabled and self.data != self.childrenDisabledValue
        # logger.debug("BoolCti.insertChild: {} enableChildren={}".format(childItem, enableChildren))
        childItem.enableBranch(enableChildren)
        childItem.enabled = enableChildren
        return childItem

    @property
    def valueColumnItemFlags(self):
        """ Returns Qt.ItemIsUserCheckable so that a check box will be drawn in the config tree.
            Note that the flags include Qt.ItemIsEditable; this makes the reset button will appear.
        """
        return Qt.ItemIsUserCheckable | Qt.ItemIsEditable

    @property
    def checkState(self):
        """ Returns Qt.Checked or Qt.Unchecked.
        """
        if self.data is True:
            return Qt.Checked
        elif self.data is False:
            return Qt.Unchecked
        else:
            raise ValueError("Unexpected data: {!r}".format(self.data))

    @checkState.setter
    def checkState(self, checkState):
        """ Sets the data to given a Qt.CheckState (Qt.Checked or Qt.Unchecked).
        """
        if checkState == Qt.Checked:
            logger.debug("BoolCti.checkState setting to True")
            self.data = True
        elif checkState == Qt.Unchecked:
            logger.debug("BoolCti.checkState setting to False")
            self.data = False
        else:
            raise ValueError("Unexpected check state: {!r}".format(checkState))

    def enableBranch(self, enabled):
        """ Sets the enabled member to True or False for a node and all it's children
        """
        self.enabled = enabled

        # Disabled children and further descendants
        enabled = enabled and self.data != self.childrenDisabledValue

        for child in self.childItems:
            child.enableBranch(enabled)

    def createEditor(self, delegate, parent, _option):
        """ Creates a hidden widget so that only the reset button is visible during editing.
            :type option: QStyleOptionViewItem
        """
        return GroupCtiEditor(self, delegate, parent=parent)


class BoolGroupCti(AbstractCti):
    """ Config Tree Item to store a nullable boolean (True, False or None).

        It can be edited using a tri-state check box. However, the user can not set the value
        to partially checked directly, it will only be partially checked if some of its children
        are checked and others are not! This is a bug/behavior of Qt that won't be fixed.
        See: https://bugreports.qt.io/browse/QTBUG-7674 and
             http://comments.gmane.org/gmane.comp.lib.qt.general/925
    """

    def __init__(self, nodeName, defaultData=None, expanded=True):
        """ Constructor. For the parameters see the AbstractCti constructor documentation.
        """
        super(BoolGroupCti, self).__init__(nodeName, defaultData, expanded=expanded)

    def _enforceDataType(self, data):
        """ Converts to bool so that self.data always is of that type.
        """
        return None if data is None else bool(data)

    @property
    def displayValue(self):
        """ Returns empty string since a checkbox will displayed in the value column instead.
        """
        return ""

    @property
    def valueColumnItemFlags(self):
        """ Returns Qt.ItemIsUserCheckable so that a check box will be drawn in the config tree.
            Note that the flags include Qt.ItemIsEditable; this makes the reset button will appear.
        """
        # return Qt.ItemIsTristate | Qt.ItemIsUserCheckable | Qt.ItemIsEditable
        return Qt.ItemIsUserCheckable | Qt.ItemIsEditable

    @property
    def checkState(self):
        """ Returns Qt.Checked or Qt.Unchecked if all children are checked or unchecked, else
            returns Qt.PartiallyChecked
        """
        # commonData = self.childItems[0].data if self.childItems else Qt.PartiallyChecked
        commonData = None

        for child in self.childItems:
            if isinstance(child, BoolCti):
                if commonData is not None and child.data != commonData:
                    return Qt.PartiallyChecked
                commonData = child.data

        if commonData is True:
            return Qt.Checked
        elif commonData is False:
            return Qt.Unchecked
        else:
            raise AssertionError("Please report this bug: commonData: {!r}".format(commonData))

    @checkState.setter
    def checkState(self, checkState):
        """ Sets the data to given a Qt.CheckState (Qt.Checked or Qt.Unchecked).
        """
        logger.debug("checkState setter: {}".format(checkState))
        if checkState == Qt.Checked:
            commonData = True
        elif checkState == Qt.Unchecked:
            commonData = False
        elif checkState == Qt.PartiallyChecked:
            commonData = None
            # This never occurs, see remarks above in the classes' docstring
            assert False, "This never happens. Please report if it does."
        else:
            raise ValueError("Unexpected check state: {!r}".format(checkState))

        for child in self.childItems:
            if isinstance(child, BoolCti):
                child.data = commonData

    def createEditor(self, delegate, parent, _option):
        """ Creates a hidden widget so that only the reset button is visible during editing.
            :type option: QStyleOptionViewItem
        """
        return GroupCtiEditor(self, delegate, parent=parent)
