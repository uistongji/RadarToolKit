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


""" featured-style status bar
"""


from ..bindings import QtWidgets, QtCore, QtSignal

import logging


logger = logging.getLogger(__name__)



class RTKStatusBar(QtWidgets.QStatusBar):

    def __init__(self, parent=None, msg=None):
        super(RTKStatusBar, self).__init__(parent)

        self.showMessage(msg)


    def showMessage(self, item='', msg='', level='INFO', timeout=0):
        super(RTKStatusBar, self).showMessage(msg, timeout)

    