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


from ..bindings import QtWidgets, QtCore
from .togglecolumn import ToggleColumnTreeView
from .treemodels import BaseTreeModel
from ..utils.check_class import check_class
from ..settings import TREE_ICON_SIZE



class RTKTreeView(ToggleColumnTreeView):
    """ QTreeView that defines common functionality, look and feel for all tree views in RTK.

        The model must be a BaseTreeModel
    """

    def __init__(self, treeModel=None, parent=None):
        """ Constructor
        """
        super(RTKTreeView, self).__init__()

        if treeModel is not None:
            self.setModel(treeModel)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

        # Setting animated to False because closing an RTI (instead of simply collapsing it) with
        # animation on is very ugly. Closing entails removing children from the tree. In that case
        # all the items below the closed node are then redrawn, which results in a lot of flicker.
        self.setAnimated(False)
        self.setAllColumnsShowFocus(True)
        self.setIconSize(TREE_ICON_SIZE)

        treeHeader = self.header()
        treeHeader.setSectionsMovable(True)
        treeHeader.setSectionResizeMode(QtWidgets.QHeaderView.Interactive) # don't set to stretch
        treeHeader.setStretchLastSection(True)


    def setModel(self, model):
        """ Sets the model.
            Checks that the model is a
        """
        check_class(model, BaseTreeModel)
        super(RTKTreeView, self).setModel(model)


    def setCurrentIndex(self, currentIndex):
        """ Sets the current item to be the item at currentIndex.
            Also select the row as to give consistent user feedback.
            See also the notes at the top of this module on current item vs selected item(s).
        """
        selectionModel = self.selectionModel()
        selectionFlags = (QtCore.QItemSelectionModel.ClearAndSelect |
                          QtCore.QItemSelectionModel.Rows)
        selectionModel.setCurrentIndex(currentIndex, selectionFlags)


    def getRowCurrentIndex(self, row=0):
        """ Returns the index of column 0 of the current item in the underlying model.
            See also the notes at the top of this module on current item vs selected item(s).
        """
        curIndex = self.currentIndex()
        col0Index = curIndex.sibling(curIndex.row(), row)
        return col0Index


    def getCurrentItem(self):
        """ Find the current tree item (and the current index while we're at it)
            Returns a tuple with the current item, and its index. The item may be None.
            See also the notes at the top of this module on current item vs selected item(s).
        """
        currentIndex = self.getRowCurrentIndex()
        currentItem = self.model().getItem(currentIndex)
        return currentItem, currentIndex


    def expandPath(self, path):
        """ Follows the path and expand all nodes along the way.
            Returns (item, index) tuple of the last node in the path (the leaf node). This can be
            reused e.g. to select it.
        """
        iiPath = self.model().findItemAndIndexPath(path)
        for (item, index) in iiPath[1:]:
            assert index.isValid(), "Sanity check: invalid index in path for item: {}".format(item)
            self.expand(index)

        leaf = iiPath[-1]
        return leaf


    def expandBranch(self, index=None, expanded=True):
        """ Expands or collapses the node at the index and all it's descendants.

            If expanded is True the nodes will be expanded, if False they will be collapsed.

            If parentIndex is None, the invisible root will be used (i.e. the complete forest will
            be expanded).
        """
        treeModel = self.model()
        if index is None:
            index = QtCore.QModelIndex()

        if index.isValid():
            self.setExpanded(index, expanded)

        for rowNr in range(treeModel.rowCount(index)):
            childIndex = treeModel.index(rowNr, 0, parentIndex=index)
            self.expandBranch(index=childIndex, expanded=expanded)