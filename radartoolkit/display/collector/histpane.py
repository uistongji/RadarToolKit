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


""" Histories Display embedded in the Collector Tree Widget.
"""

import os
import logging
from datetime import datetime
from pyqtgraph.functions import mkColor

from ..bindings import QtWidgets, QtGui, QtCore, QtSlot
from ..utils.check_class import check_class
from ..settings import ICONS_DIR, COLLECTOR_TREE_ICON_SIZE
from ..reg.tabmodel import BaseInfoItem


logger = logging.getLogger(__name__)


class HistPane(QtWidgets.QWidget):
    """ 
    Widget to display history information in the collector tree cell 
        
    :: The HistoryWidget only shows the user's interaction on the collector items,
    e.g., new data input, processing combobox clicked, ROI changing and axis combobox clicked.
    """

    def __init__(self, parent=None):
        """ Constructor.
        """
        super(HistPane, self).__init__(parent)

        self._maxLength = 30
        self._Histories = [] 
        self.attrOpts = {
            'color': '#4682B4',
            'justify': 'center'
        }
        self._Open = False

        self._setupView()
        self.label.setText("<span style='color: #4682B4; font-weight: bold'>No File Item Selected</span>")
        
        # DEBUG:
        self.setOptsText({'nodeid': 1, 'field':'question'})
        self.setOptsText({'nodeid': 2, 'field': 'sucess'})
        self.setOptsText({'nodeid': 3, 'field': 'failure'})


    def __repr__(self) -> str:
        return f"<{type(self).__name__}"
    

    def sizeHint(self):
        return super().sizeHint()


    @property
    def maxLength(self):
        return self._maxLength
    

    def _setupView(self):

        # setup the message display label
        self.label = QtWidgets.QLabel("")
        # self.label.setFrameStyle(QtWidgets.QFrame.Panel)
        # self.label.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.label.setAlignment(QtCore.Qt.AlignCenter)

        # setup the button to show more information
        self.moreInfoBtn = QtWidgets.QPushButton(
            QtGui.QIcon(os.path.join(ICONS_DIR, "robot.png")), "")
        self.moreInfoBtn.setIconSize(COLLECTOR_TREE_ICON_SIZE)
        self.moreInfoBtn.setFixedSize(23, 23)
        self.moreInfoBtn.setFlat(True)
        self.moreInfoBtn.setEnabled(False)
        
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.setSpacing(1)
        self.mainLayout.setContentsMargins(2, 0, 2, 0)
        self.setLayout(self.mainLayout)

        self.mainLayout.addWidget(self.label)
        self.mainLayout.addWidget(self.moreInfoBtn)
    

    @QtSlot(dict, dict)
    def setOptsText(self, sourceDict, styledDict=None):
        """
        Set the text and text properties in the label. Accepts optional arguments for auto-generating
        a CSS style string:

        styledDict:
        ==================== ==============================
        color                (str) example: '#CCFF00'
        size                 (str) example: '8pt'
        bold                 (bool)
        italic               (bool)
        ==================== ==============================
        """
        opts = self.attrOpts
        if styledDict is not None:
            for k in styledDict:
                opts[k] = styledDict[k]
        optList = []

        color = self.attrOpts['color']
        if color is None:
            color = 'black' # the default color css
        color = mkColor(color)
        optList.append('color: ' + color.name(QtGui.QColor.NameFormat.HexArgb))
        if 'size' in opts:
            optList.append('font-size: ' + opts['size'])
        if 'bold' in opts and opts['bold'] in [True, False]:
            optList.append('font-weight: ' + {True:'bold', False:'normal'}[opts['bold']])
        if 'italic' in opts and opts['italic'] in [True, False]:
            optList.append('font-style: ' + {True:'italic', False:'normal'}[opts['italic']])

        check_class(sourceDict, dict, allow_none=False)
        if 'desc' not in sourceDict:
            sourceDict['desc'] = ''
        if 'field' not in sourceDict:
            sourceDict['field'] = 'question'

        full = f"<span style='font-weight: bold'>{sourceDict['field']}: </span>" + \
            "<span style='%s'>%s</span>" % ('; '.join(optList), sourceDict['desc'])
        self.label.setText(full)

        sourceDict['styles'] = styledDict
        self.infoWrapper(sourceDict)


    def infoWrapper(self, sourceDict):
        """ 
        Checks the length of the history, if more than the limitation, 
        then pop up from the beginning 
        """
        check_class(sourceDict, dict, allow_none=True)
        if not isinstance(sourceDict, dict):
            logger.info(f"{self.__repr__()}:infoWrapper> unable to append, since source is empty.")
            return
        else:
            if len(self._Histories) > self.maxLength:
                self._Histories.pop(0)

            # parse information
            if 'nodeid' not in sourceDict:
                sourceDict['nodeid'] = len(self._Histories)
            sourceDict['timeStamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._Histories.append(BaseInfoItem(sourceDict))


    def clear(self):
        self.label.setText("<span style='color: #4682B4; font-weight: bold'>No File Item Selected</span>")
        self._Histories = []
        

