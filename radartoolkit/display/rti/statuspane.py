#!/usr/bin.env python

from ..bindings import QtWidgets, Qt
from .detailpanes import DetailTablePane
from .filetreemodel import FileTreeModel

import logging

logger = logging.getLogger(__name__)


class StatusPane(DetailTablePane):

    _label = "Status"

    HEADERS = ['Processed', 'Status']
    (COL_STATUS_PROC, COL_STATUS) = range(len(HEADERS))

    LEFT_HEADERS = ['_Raw', '_CoherentStacking', '_PulseCompression',
                    '_IncoherentStacking', '_PDF']


    def __init__(self, fileTreeView, parent=None):
        
        super(StatusPane, self).__init__(fileTreeView, parent=parent)

        self.table.setWordWrap(True)
        self.table.addHeaderContextMenu(enabled={'Name': False, 'Value': False},
                                        checked={'Type': False})

        tableHeader = self.table.horizontalHeader()
        tableHeader.resizeSection(self.COL_STATUS_PROC, 125)
        tableHeader.resizeSection(self.COL_STATUS, 150)


    def _drawContents(self, currentRti=None):

        logger.debug("Called _drawContents of StatusPane: {}".format(currentRti))
        table = self.table
        table.setUpdatesEnabled(False)
        try:
            table.clearContents()
            verticalHeader = table.verticalHeader()
            verticalHeader.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

            if currentRti is None:
                return
            
            fileModel = self._fileTreeView.model()
            statusNames = FileTreeModel.HEADERS[14:18]
            table.setRowCount(len(statusNames))

            for row, statusName in enumerate(statusNames):
                nameItem = QtWidgets.QTableWidgetItem(statusName)
                nameItem.setToolTip(statusName)
                table.setItem(row, self.COL_STATUS_PROC, nameItem)
                itemDataText = fileModel.itemData(currentRti, row)
                statusItem = QtWidgets.QTableWidgetItem(itemDataText)
                statusItem.setToolTip(fileModel.itemData(currentRti, row, role=Qt.ToolTipRole))
                table.setItem(row, self.COL_STATUS, statusItem)
                table.resizeRowToContents(row)
            
            verticalHeader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        
        finally:
            table.setUpdatesEnabled(True)