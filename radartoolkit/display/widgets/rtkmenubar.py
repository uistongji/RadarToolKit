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


""" 
    RTK Main Menu Bar 
"""


import os, platform
import logging

from ..bindings import QtWidgets, QtGui
from ..settings import ICONS_DIR

logger = logging.getLogger(__name__)
curFileName = os.path.basename(__file__)



class RTKMenuBar(QtWidgets.QMenuBar):
    """ Creates a menu bar for rtk.
    """

    def __init__(self, parent=None):
        super(RTKMenuBar, self).__init__(parent)
        self._win = parent
        self._menus = {}
        self._keysMenu = ["Open File As ...", "Open Recent",
                          "Browse Direcoty ...", "Browse File .."]

        if platform.system() == 'Darwin':
            self.setNativeMenuBar(False)


    def __repr__(self) -> str:
        return f"<{curFileName}:{type(self).__name__}:"
    
    
    @property
    def win(self):
        return self._win
    
    
    @property
    def keysMenu(self):
        return self._keysMenu
    

    def _setupSubMenus(self, menuName, _cfg):
        subMenu = self._menus[menuName]
        for _Nr, value in enumerate(_cfg):
            func = getattr(self.win, value['handler'])
            if value['expanded']:
                _menu = subMenu.addMenu(value['actionName'])
                if value['actionName'] in self.keysMenu:
                    self._menus[value['actionName']] = _menu
                _menu.aboutToShow.connect(func)
            else:
                action = QtGui.QAction(value['actionName'], self)
                action.setToolTip(value['toolTip'])
                action.setShortcut(QtGui.QKeySequence(value['shortCut']))
                action.triggered.connect(func)
                if value['decoration']:
                    action.setIcon(os.path.join(ICONS_DIR, value['decoration']))
                subMenu.addAction(action)
            if value['addSeparator']:
                subMenu.addSeparator()


    def unmarshall(self, cfg):
        if cfg is None:
            logger.debug(f"{self.__repr__}:unmarshall>: called, cfg is empty. Returning.")
            return
        else:
            logger.debug(f"{self.__repr__}:unmarshall>: called, unmarshall menu bar settings.")
            for menuName, menuCfg in cfg.items():
                self._menus[menuName] = self.addMenu(menuName)
                self._setupSubMenus(menuName, menuCfg)


    def marshall(self):
        pass



    
