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


""" Error Msg Widget for displaying.
"""

from .abstract import AbstractInspector
from ..utils.check_class import check_is_a_string
from ..config.ctis.groupcti import MainGroupCti


class ErrorMsgInspector(AbstractInspector):

    
    def __init__(self, collector, msg, parent=None):

        super(ErrorMsgInspector, self).__init__(collector, parent=parent)

        check_is_a_string(msg)
        self.msg = msg

        self._config = self._createConfig()
        self.setCurrentIndex(self.ERROR_PAGE_IDX)


    @classmethod
    def axesNames(cls):
        return tuple()


    def _createConfig(self):
        """ Creates a config tree item (CTI) hierarchy containing default children.
        """
        rootItem = MainGroupCti('message inspector')
        return rootItem


    def updateContents(self, reason=None, initiator=None):
        """ Override updateContents. Shows the error error message
        """
        self.setCurrentIndex(self.ERROR_PAGE_IDX)
        self._showError(msg=self.msg)

           





