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


""" Miscellaneous functions and classes using Qt
"""


from __future__ import print_function

import logging
import os.path

from ..bindings import QtWidgets


logger = logging.getLogger(__name__)


def setWidgetSizePolicy(widget, hor=None, ver=None):
    """ 
    Sets horizontal and/or vertical size policy on a widget. 
    """

    sizePolicy = widget.sizePolicy()
    logger.debug("widget {} size policy Befor: {} {}"
                 .format(widget, sizePolicy.horizontalPolicy(), sizePolicy.verticalPolicy()))

    if hor is not None:
        sizePolicy.setHorizontalPolicy(hor)

    if ver is not None:
        sizePolicy.setVerticalPolicy(ver)

    widget.setSizePolicy(sizePolicy)

    sizePolicy = widget.sizePolicy()
    logger.debug("widget {} size policy AFTER: {} {}"
                 .format(widget, sizePolicy.horizontalPolicy(), sizePolicy.verticalPolicy()))


def processEvents():
    """ Processes all pending events for the calling thread until there are no more events to
        process.
    """

    QtWidgets.QApplication.instance().processEvents()


def setApplicationQtStyle(styleName):
    """ sets the Qt style (e.g. to 'fusion') """

    _qApp = QtWidgets.QApplication.instance()
    logger.debug("Setting Qt style to: {}".format(styleName))
    _qApp.setStyle(QtWidgets.QStyleFactory.create(styleName))
    if _qApp.style().objectName().lower() != styleName.lower():
        logger.warning(
            "Setting style failed: actual style {!r} is not the specified style {!r}"
            .format(_qApp.style().objectName(), styleName))


def setApplicationStyleSheet(fileName):
    """ reads the style sheet from file and set it as application style sheet. """

    fileName = os.path.abspath(fileName)
    logger.debug("Reading qss from: {}".format(fileName))
    try:
        with open(fileName) as input:
            qss = input.read()
    except Exception as ex:
        logger.warning("Unable to read style sheet from '{}'. Reason: {}".format(fileName, ex))
        return
    QtWidgets.QApplication.instance().setStyleSheet(qss)