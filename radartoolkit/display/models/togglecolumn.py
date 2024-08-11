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


from ..bindings import QtWidgets, Qt, QtGui
from ..utils.funcs import getWidgetState

import base64, logging


logger = logging.getLogger(__name__)



class ToggleColumnMixIn(object):
    """ Adds actions to a QTableView that can show/hide columns
        by right clicking on the header.

        Has functionality for reading/writing from persitent settings.
    """

    def addHeaderContextMenu(self, checked = None, checkable = None, enabled = None):
        """ Adds the context menu from using header information

            checked can be a header_name -> boolean dictionary. If given, headers
            with the key name will get the checked value from the dictionary.
            The corresponding column will be hidden if checked is False.

            checkable can be a header_name -> boolean dictionary. If given, header actions
            with the key name will get the checkable value from the dictionary. (Default True)

            enabled can be a header_name -> boolean dictionary. If given, header actions
            with the key name will get the enabled value from the dictionary. (Default True)
        """

        checked = checked if checked is not None else {}
        checkable = checkable if checkable is not None else {}
        enabled = enabled if enabled is not None else {}

        horizontal_header = self.horizontalHeader()
        horizontal_header.setContextMenuPolicy(Qt.ActionsContextMenu)

        self.toggle_column_actions_group = QtGui.QActionGroup(self)
        self.toggle_column_actions_group.setExclusive(False)
        self.__toggle_functions = []  # for keeping references

        for col in range(horizontal_header.count()):
            column_label = self.model().headerData(col, Qt.Horizontal, Qt.DisplayRole)
            action = QtGui.QAction(str(column_label),
                                   self.toggle_column_actions_group,
                                   checkable = checkable.get(column_label, True),
                                   enabled = enabled.get(column_label, True),
                                   toolTip = "Shows or hides the {} column".format(column_label))
            func = self.__makeShowColumnFunction(col)
            self.__toggle_functions.append(func) # keep reference
            horizontal_header.addAction(action)
            is_checked = checked.get(column_label, not horizontal_header.isSectionHidden(col))
            horizontal_header.setSectionHidden(col, not is_checked)
            action.setChecked(is_checked)
            action.toggled.connect(func)


    def getHeaderContextMenuActions(self):
        """ Returns the actions of the context menu of the header
        """

        return self.horizontalHeader().actions()


    def __makeShowColumnFunction(self, column_idx):
        """ Creates a function that shows or hides a column."""

        show_column = lambda checked: self.setColumnHidden(column_idx, not checked)
        return show_column


    def marshall(self):
        """ Returns an ascii string with the base64 encoded tree header state.
        """

        return base64.b64encode(getWidgetState(self.horizontalHeader())).decode('ascii')


    def unmarshall(self, dataStr):
        """ Initializes itself from a config dict form the persistent settings.
        """

        if dataStr is None:
            logger.debug("Tree headers state empty, so not restored: {}".format(self))
            return

        headerBytes = base64.b64decode(dataStr)
        horizontal_header = self.horizontalHeader()
        header_restored = horizontal_header.restoreState(headerBytes)
        if not header_restored:
            logger.warning("Tree headers state not restored: {}".format(self))

        # update actions so context menus are (un)checked properly
        for col, action in enumerate(horizontal_header.actions()):
            isChecked = not horizontal_header.isSectionHidden(col)
            action.setChecked(isChecked)



class ToggleColumnTableWidget(QtWidgets.QTableWidget, ToggleColumnMixIn):
    """ A QTableWidget where right clicking on the header allows the user to show/hide columns
    """

    pass



class ToggleColumnTableView(QtWidgets.QTableView, ToggleColumnMixIn):
    """ A QTableView where right clicking on the header allows the user to show/hide columns
    """

    pass



class ToggleColumnTreeWidget(QtWidgets.QTreeWidget, ToggleColumnMixIn):
    """ A QTreeWidget where right clicking on the header allows the user to show/hide columns
    """

    def horizontalHeader(self):
        """ Returns the horizontal header (of type QHeaderView).

            Override this if the horizontalHeader() function does not exist.
        """

        return self.header()



class ToggleColumnTreeView(QtWidgets.QTreeView, ToggleColumnMixIn):
    """ A QTreeView where right clicking on the header allows the user to show/hide columns
    """

    def horizontalHeader(self):
        """ Returns the horizontal header (of type QHeaderView).

            Override this if the horizontalHeader() function does not exist.
        """

        return self.header()