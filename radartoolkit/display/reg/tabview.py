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


""" Readable Table Viewer.
"""

import logging
import os.path

from ..utils.check_class import check_class, typeName
from .tabmodel import BaseTableModel
from ..bindings import QtCore, QtGui, QtWidgets, Qt
from ..settings import ICONS_DIR
from ..models.togglecolumn import ToggleColumnTableView


logger = logging.getLogger(__name__)
curFileName = os.path.basename(__file__)



class BaseTableView(ToggleColumnTableView):
    """ Editable QTableView that shows the contents of a BaseTableModel.
    """

    def __init__(self, model=None, parent=None):
        """ Constructor

            :param BaseTableModelmodel: a RegistryTableModel that maps the regItems
            :param QWidget parent: the parent widget
        """

        super(BaseTableView, self).__init__(parent)

        check_class(model, BaseTableModel)
        self.setModel(model)

        self.setTextElideMode(QtCore.Qt.ElideMiddle) # Does not work nicely when editing cells.
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSortingEnabled(False)
        self.setTabKeyNavigation(False)
        self.setWordWrap(False)

        Qiv = QtWidgets.QAbstractItemView
        
        self.setEditTriggers(Qiv.NoEditTriggers)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

        self.verHeader = self.verticalHeader()
        self.verHeader.setSectionsMovable(False)
        self.verHeader.hide()

        self.horHeader = self.horizontalHeader()
        self.horHeader.setDefaultAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.horHeader.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.horHeader.setStretchLastSection(False) 

        for col, canStretch in enumerate(model.store.canStretchPerColumn):
            if canStretch:
                self.horHeader.setSectionResizeMode(col, QtWidgets.QHeaderView.Stretch)
            else:
                self.horHeader.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)


    def __repr__(self) -> str:
        return f"<{curFileName}:{type(self).__name__}"
    

    def getCurrentItem(self):
        """ Returns the item of the selected row, or None if none is selected
        """

        curIdx = self.currentIndex()
        return self.model().itemFromIndex(curIdx)
    

    def setCurrentCell(self, row, col=0):
        """ Sets the current row and column.
        """

        cellIdx = self.model().index(row, col)
        if not cellIdx.isValid():
            logger.warning(f"{self.__repr__()}:setCurrentCell> unable to set (row={row}, col={col}) in table.")
        else:
            logger.debug(f"{self.__repr__()}:setCurrentCell> setting (row={row}, col={col}) in table.")
        self.setCurrentIndex(cellIdx)



class TableInfoViewer(BaseTableView):
    """ Descendent inherites from the BaseTableView ancestor.
    """

    def __init__(self, model=None, parent=None):
        super(TableInfoViewer, self).__init__(model, parent)

        self.setAlternatingRowColors(False)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setFocus(Qt.NoFocusReason)


######## DEPRETCHED #########



class TablePicksViewer(BaseTableView):
    """ Descendent inherites from the BaseTableView ancestor.
    """

    def __init__(self, model=None, parent=None):
        super(TablePicksViewer, self).__init__(model, parent)

        self.setAlternatingRowColors(False)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setFocus(Qt.NoFocusReason)