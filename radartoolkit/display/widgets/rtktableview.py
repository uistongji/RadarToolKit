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


from __future__ import print_function

import logging
from ..bindings import QtWidgets, Qt


logger = logging.getLogger(__name__)



class RTKTableView(QtWidgets.QTableView):
    """ QTableView that defines common functionality for rtk
    """

    def __init__(self, *args, **kwargs):
        """ Constructor
        """
        super(RTKTableView, self).__init__(*args, **kwargs)


    def keyPressEvent(self, event):
        """ Overrides key press events to capture Ctrl-C
        """

        if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            self.copySelectionToClipboard()
        else:
            super(RTKTableView, self).keyPressEvent(event)
        return


    def copySelectionToClipboard(self):
        """ Copies selected cells to clipboard.

            Only works for ContiguousSelection
        """

        if not self.model():
            logger.warning("Table contains no data. Copy to clipboard aborted.")
            return

        if self.selectionMode() not in [QtWidgets.QTableView.SingleSelection,
                                        QtWidgets.QTableView.ContiguousSelection]:
            logger.warning("Copy to clipboard does not work for current selection mode: {}"
                           .format(self.selectionMode()))
            return

        selectedIndices = self.selectionModel().selectedIndexes()
        logger.info("Copying {} selected cells to clipboard.".format(len(selectedIndices)))

        # selectedIndexes() can return unsorted list so we sort it here to be sure.
        selectedIndices.sort(key=lambda idx: (idx.row(), idx.column()))

        # Unflatten indices into a list of list of indicides
        allIndices = []
        allLines = []
        lineIndices = []  # indices of current line
        prevRow = None
        for selIdx in selectedIndices:
            if prevRow != selIdx.row() and prevRow is not None: # new line
                allIndices.append(lineIndices)
                lineIndices = []
            lineIndices.append(selIdx)
            prevRow = selIdx.row()
        allIndices.append(lineIndices)
        del lineIndices

        # Convert to tab-separated lines so it can be pasted in Excel.
        lines = []
        for lineIndices in allIndices:
            line = '\t'.join([str(idx.data()) for idx in lineIndices])
            lines.append(line)
        txt = '\n'.join(lines)
        QtWidgets.QApplication.clipboard().setText(txt)