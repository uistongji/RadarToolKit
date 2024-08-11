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


""" Selections of Data Evaluators.
"""


import logging

from .registry import EvaluatorRegItem
from ..bindings import QtWidgets, QtSlot, Qt
from ..widgets.misc import setWidgetSizePolicy
from ..utils.constants import DOCK_MARGIN


logger = logging.getLogger(__name__)



class SelectionPane(QtWidgets.QFrame):

    """ 
    Shows the attributes/neccesary information of the selected file tree item. 
    """

    NO_INSPECTOR_LABEL = '< None >'

    def __init__(self, actionGroup, parent=None):
        super(SelectionPane, self).__init__(parent=parent)

        self.actionGroup = actionGroup
        self._initView()

    
    @property
    def validEvaluators(self):
        evaluator = []
        for name, _ in self.actionGroup.items():
            evaluator.append(name)
        return evaluator
        

    def _initView(self):
        
        self.menuButton = QtWidgets.QPushButton(self.NO_INSPECTOR_LABEL)
        self.menuButton.setMinimumWidth(30)

        evaluatorMenu = QtWidgets.QMenu("Choose Evaluator", parent=self.menuButton)
        for action in self.actionGroup.actions():
            evaluatorMenu.addAction(action)
        self.menuButton.setMenu(evaluatorMenu)

        self.messageLabel = QtWidgets.QLabel("")
        self.messageLabel.setObjectName("inspector_msglabel")
        self.messageLabel.setFrameStyle(QtWidgets.QFrame.Panel)
        self.messageLabel.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.messageLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # setup the layout
        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(2, 0, 5, 0)

        self.mainLayout.addWidget(self.menuButton, stretch=0)
        self.mainLayout.addWidget(self.messageLabel, stretch=1)

        setWidgetSizePolicy(self.menuButton, hor=QtWidgets.QSizePolicy.Minimum)
        setWidgetSizePolicy(self.messageLabel, hor=QtWidgets.QSizePolicy.Ignored)
        setWidgetSizePolicy(
            self, hor=QtWidgets.QSizePolicy.MinimumExpanding, ver=QtWidgets.QSizePolicy.Fixed)
        
    
    def __repr__(self) -> str:
        return f"<{type(self).__name__}"
    
    
    def showMessage(self, msg):
        """ 
        Sets the message label 
        """
        logger.debug(f"{self.__repr__()}:showMessage> called, showing msg: {msg}")
        self.messageLabel.setText(msg)
        self.messageLabel.setToolTip(msg)
            

    @QtSlot(EvaluatorRegItem)
    def updateFromEvalutaor(self, EvaluatorRegItem):
        """ 
        Updates the label from the full name of the EvaluatorRegItem.
        """
        label = self.NO_INSPECTOR_LABEL if EvaluatorRegItem is None else EvaluatorRegItem.name
        self.menuButton.setText(label)

    
    @QtSlot(object)
    def onBtnClicked(self, value):
        print(value)

