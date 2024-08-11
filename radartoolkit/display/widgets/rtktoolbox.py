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
# AUTHOR: Jiaying Zhou, Chen Lv (supervisor: Tong Hao), Tongji University


""" RTKToolBox for Antarctic Map Viewer and Radar Data Viewer
"""


import os
import logging

from ..archives.databse_tab import databse_tab
from ..map.map_widget import MapWholeWidget
from ..bindings import QtWidgets, QtSignal, QtGui, QtSlot
from ..settings import ICONS_DIR


logger = logging.getLogger(__name__)
curFileName = os.path.basename(__file__)



class RTKToolBox(QtWidgets.QToolBox):
    """ 
    :param sigBtnClicked: signal emits (filePath, fileType(if possible))) when `btn_Load.clicked`
    """
    
    sigBtnLoadClicked = QtSignal(str, str)
    sigShowMessages = QtSignal(str)
    sigTableChanged = QtSignal(str)


    def __init__(self, rtkWin, syncSignal=None, parent=None):
        """ constructor """

        super(RTKToolBox, self).__init__(parent=parent)
        self._rtkWin = rtkWin
        self.syncSignal = syncSignal
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(254, 254, 254))
        self.setPalette(p)

        self._setupViews()

        # --- signal-slot connection ---
        self.db_tab.sigShowMessage.connect(self.onShowMessages) # messages from the db_tab
        self.db_tab.database.sigShowMessage.connect(self.onShowMessages) # messages from the db
        self.antarc_map.map_db.sigShowMessage.connect(self.onShowMessages) # messages from the map_db
        self.db_tab.tableChanged.connect(self.onTableChanged)


    def __repr__(self) -> str:
        return f"<{curFileName}:{type(self).__name__}"


    @property
    def rtkWin(self):
        return self._rtkWin
    

    @property
    def mapItem(self):
        return self._mapItem
    

    @property
    def CHAXItem(self):
        return self._CHAXItem


    def _setupViews(self):
      
        self.antarc_map = MapWholeWidget(self.rtkWin.mapViewer)
        self.db_tab = databse_tab(self.syncSignal)
        # ----------- EOF ------------
        self._makeToolBox()


    def _makeToolBox(self):
        self._mapItem = self.addItem(self.antarc_map, 'Antarctic Map')
        self._CHAXItem = self.addItem(self.rtkWin.fileHub, 'Radar DataSet') 
        self._dbItem = self.addItem(self.db_tab, 'Radar DataBase')

        self.setItemToolTip(0, 'Show Antartic Map, eg. DEM, Distribution of Transects and etc.')
        self.setItemToolTip(1, 'Ice Sounding Radar Dataset')
        self.setItemToolTip(2, 'Radar DataBase: manage radar data information ')

        self.setItemIcon(0, QtGui.QIcon(os.path.join(ICONS_DIR, 'mountain.png')))
        self.setItemIcon(1, QtGui.QIcon(os.path.join(ICONS_DIR, 'radar-file.png')))
        self.setItemIcon(2, QtGui.QIcon(os.path.join(ICONS_DIR, 'database.png')))

    
    @QtSlot(str)
    def onShowMessages(self, msg):
        self.sigShowMessages.emit(msg)
    

    @QtSlot(str)
    def onTableChanged(self, msg):
        self.sigTableChanged.emit(msg)
        