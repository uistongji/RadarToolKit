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

from ..bindings import QtWidgets


class NotSpecified(object):
    """ Class for NOT_SPECIFIED constant.
        Is used so that a parameter can have a default value other than None.

        Evaluate to False when converted to boolean.
    """
    def __nonzero__(self):
        """ Always returns False. Called when to converting to bool in Python 2.
        """
        return False

    def __bool__(self):
        """ Always returns False. Called when to converting to bool in Python 3.
        """
        return False



NOT_SPECIFIED = NotSpecified()



def setWidgetSizePolicy(widget, horPolicy=None, verPolicy=None):
    """ Sets the size policy of a widget.
    """
    sizePolicy = widget.sizePolicy()

    if horPolicy is not None:
        sizePolicy.setHorizontalPolicy(horPolicy)

    if verPolicy is not None:
        sizePolicy.setVerticalPolicy(verPolicy)

    widget.setSizePolicy(sizePolicy)
    return sizePolicy


def widgetSubCheckBoxRect(widget, option):
    """ Returns the rectangle of a check box drawn as a sub element of widget
    """
    opt = QtWidgets.QStyleOption()
    opt.initFrom(widget)
    style = widget.style()
    return style.subElementRect(QtWidgets.QStyle.SE_ItemViewItemCheckIndicator, opt, widget)



def type_name(var):
    """ Returns the name of the type of variable."""
    return type(var).__name__

    