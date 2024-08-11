#!/usr/bin.env python

from ..bindings import QtWidgets, Qt
from .detailpanes import DetailTablePane
from ..utils.six import unichr
from .filetreemodel import FileTreeModel

import logging
logger = logging.getLogger(__name__)

def replace_eol_chars(attr):
    """ Replace end-of-line characters with unicode glyphs so that all table rows fit on one line.
    """
    return (attr.replace('\r\n', unichr(0x21B5))
            .replace('\n', unichr(0x21B5))
            .replace('\r', unichr(0x21B5)))


class AttributesPane(DetailTablePane):

    _label = "Attributes"

    HEADERS = ["Name", "Value"]
    (COL_ATTR_NAME, COL_VALUE) = range(len(HEADERS))

    LEFT_HEADERS = ['_Transect', '_Season', '_Flight', '_Project',
                    '_Set', '_Stream', '_Area', '_Summary', '_ItemClass', '_Type']

    def __init__(self, fileTreeView=None, parent=None):
        
        super(AttributesPane, self).__init__(fileTreeView, parent=parent)

        self.table.setWordWrap(True)
        self.table.addHeaderContextMenu(enabled={'Name': False, 'Value': False},
                                        checked={'Type': False})

        tableHeader = self.table.horizontalHeader()
        tableHeader.resizeSection(self.COL_ATTR_NAME, 125)
        tableHeader.resizeSection(self.COL_VALUE, 150)


    def _drawContents(self, currentRti=None):
        """ Draws the attributes of the currentRTI
        """
        table = self.table
        table.setUpdatesEnabled(False)
        try:
            table.clearContents()
            verticalHeader = table.verticalHeader()
            verticalHeader.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

            if currentRti is None:
                return
            
            fileModel = self._fileTreeView.model()
            proNames = FileTreeModel.HEADERS[:13]
            table.setRowCount(len(proNames))

            for row, proName in enumerate(proNames):
                nameItem = QtWidgets.QTableWidgetItem(proName)
                nameItem.setToolTip(proName)
                table.setItem(row, self.COL_ATTR_NAME, nameItem) 
                itemDataText = replace_eol_chars(fileModel.itemData(currentRti, row))
                propItem = QtWidgets.QTableWidgetItem(itemDataText)
                propItem.setToolTip(fileModel.itemData(currentRti, row, role=Qt.ToolTipRole))
                table.setItem(row, self.COL_VALUE, propItem)
                table.resizeRowToContents(row)
        

            verticalHeader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        finally:
            table.setUpdatesEnabled(True)

