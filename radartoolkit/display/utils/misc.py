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


""" Miscellaneous routines. 
"""


import logging
import pprint
import re
import os
import sys
import traceback
from html import escape

from typing import List, Dict, Any, TypeVar

from info import (REPO_NAME, VERSION, ORGANIZATION_NAME, ORGANIZATION_DOMAIN, \
                     DEBUGGING)
from ..bindings import QtCore, QtWidgets
from .check_class import is_a_string
from .six import unichr

logger = logging.getLogger(__name__)



################
# QApplication #
################

def initQApplication():
    """ Initializes the QtWidgets.QApplication instance. Creates one if it doesn't exist.

        Sets RTK specific attributes, such as the OrganizationName, so that the application
        persistent settings are read/written to the correct settings file/winreg. It is therefore
        important to call this function at startup. The RTKApplication constructor does this.

        Returns the application.
    """
    # PyQtGraph recommends raster graphics system for OS-X.
    if 'darwin' in sys.platform:
        graphicsSystem = "raster" # raster, native or opengl
        os.environ.setdefault('QT_GRAPHICSSYSTEM', graphicsSystem)
        logger.debug("Setting QT_GRAPHICSSYSTEM to: {}".format(graphicsSystem))

    app = QtWidgets.QApplication(sys.argv)
    initRTKApplicationSettings(app)
    return app


def initRTKApplicationSettings(app): 
    """ Sets RTK specific attributes, such as the OrganizationName, so that the application
        persistent settings are read/written to the correct settings file/winreg. It is therefore
        important to call this function at startup. The RTKApplication constructor does this.
    """
    assert app, \
        "app undefined. Call QtWidgets.QApplication.instance() or QtCor.QApplication.instance() first."

    logger.debug("Setting RTK QApplication settings.")
    app.setApplicationName(REPO_NAME)
    app.setApplicationVersion(VERSION)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setOrganizationDomain(ORGANIZATION_DOMAIN)



######################
# Exception Handling #
######################

class ResizeDetailsMessageBox(QtWidgets.QMessageBox):
    """ Message box that enlarges when the 'Show Details' button is clicked.
        Can be used to better view stack traces. I could't find how to make a resizeable message
        box but this it the next best thing.

        Taken from:
        http://stackoverflow.com/questions/2655354/how-to-allow-resizing-of-qmessagebox-in-pyqt4
    """
    def __init__(self, detailsBoxWidth=700, detailBoxHeight=300, *args, **kwargs):
        """ Constructor
            :param detailsBoxWidht: The width of the details text box (default=700)
            :param detailBoxHeight: The heights of the details text box (default=700)
        """
        super(ResizeDetailsMessageBox, self).__init__(*args, **kwargs)
        self.detailsBoxWidth = detailsBoxWidth
        self.detailBoxHeight = detailBoxHeight

    def resizeEvent(self, event):
        """ Resizes the details box if present (i.e. when 'Show Details' button was clicked)
        """
        result = super(ResizeDetailsMessageBox, self).resizeEvent(event)

        details_box = self.findChild(QtWidgets.QTextEdit)
        if details_box is not None:
            #details_box.setFixedSize(details_box.sizeHint())
            details_box.setFixedSize(QtCore.QSize(self.detailsBoxWidth, self.detailBoxHeight))

        return result
    

def handleException(exc_type, exc_value, exc_traceback):

    traceback.format_exception(exc_type, exc_value, exc_traceback)

    logger.critical("Bug: uncaught {}".format(exc_type.__name__),
                    exc_info=(exc_type, exc_value, exc_traceback))
    if DEBUGGING:
        logger.info("Quitting application with exit code 1")
        sys.exit(1)
    else:
        # Constructing a QApplication in case this hasn't been done yet.
        if not QtWidgets.QApplication.instance(): # QtWidgets.QApplication / qApp
            _app = QtWidgets.QApplication()

        msgBox = ResizeDetailsMessageBox()
        msgBox.setText("Bug: uncaught {}".format(exc_type.__name__))
        msgBox.setInformativeText(str(exc_value))
        lst = traceback.format_exception(exc_type, exc_value, exc_traceback)
        msgBox.setDetailedText("".join(lst))
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        msgBox.exec_()
        logger.info("Quitting application with exit code 1")
        sys.exit(1)



######################
# QSettings routines #
######################

def getWidgetGeom(widget):
    """ Gets the QWindow or QWidget geometry as a QByteArray.

        Since Qt does not provide this directly we hack this by saving it to the QSettings
        in a temporary location and then reading it from the QSettings.

        :param widget: A QWidget that has a saveGeometry() methods
    """
    settings = QtCore.QSettings()
    settings.beginGroup('temp_conversion')
    try:
        settings.setValue("winGeom", widget.saveGeometry())
        return bytes(settings.value("winGeom"))
    finally:
        settings.endGroup()


def getWidgetState(qWindow):
    """ Gets the QWindow or QWidget state as a QByteArray.

        Since Qt does not provide this directly we hack this by saving it to the QSettings
        in a temporary location and then reading it from the QSettings.

        :param widget: A QWidget that has a saveState() methods
    """
    settings = QtCore.QSettings()
    settings.beginGroup('temp_conversion')
    try:
        settings.setValue("winState", qWindow.saveState())
        return bytes(settings.value("winState"))
    finally:
        settings.endGroup()



######################
# Debugging routines #
######################

def printChildren(obj, indent=""):
    """ Recursively prints the children of a QObject. Useful for debugging.
    """
    children=obj.children()
    if children==None:
        return
    for child in children:
        try:
            childName = child.objectName()
        except AttributeError:
            childName = "<no-name>"

        #print ("{}{:10s}: {}".format(indent, childName, child.__class__))
        print ("{}{!r}: {}".format(indent, childName, child.__class__))
        printChildren(child, indent + "    ")


def printAllWidgets(qApplication, ofType=None):
    """ Prints list of all widgets to stdout (for debugging)
    """
    print ("Application's widgets {}".format(('of type: ' + str(ofType)) if ofType else ''))
    for widget in qApplication.allWidgets():
        if ofType is None or isinstance(widget, ofType):
            print ("  {!r}".format(widget))


################
#    Others    #
################

def removeProcessSerialNumber(argList: List[str]) -> List[str]:
    """ Creates a copy of a list (typically sys.argv) where the strings that
        start with ``-psn_0_`` are removed.

        These are the process serial number used by the OS-X open command
        to bring applications to the front. They clash with argparse.
        See: http://hintsforums.macworld.com/showthread.php?t=11978
    """
    return [arg for arg in argList if not arg.startswith("-psn_0_")]



#####################
# Unsorted routines #
#####################

def widgetSubCheckBoxRect(widget, option):
    """ Returns the rectangle of a check box drawn as a sub element of widget
    """
    opt = QtWidgets.QStyleOption()
    opt.initFrom(widget)
    style = widget.style()
    return style.subElementRect(QtWidgets.QStyle.SE_ViewItemCheckIndicator, opt, widget)


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


class NotSpecified():
    """ Class for the NOT_SPECIFIED constant.
        Is used so that a parameter can have a default value other than None.

        Evaluates to False when converted to boolean.
    """
    def __bool__(self) -> bool:
        """ Always returns False. Called when converting to bool in Python 3.
        """
        return False

NOT_SPECIFIED = NotSpecified()


def isQuoted(s: str) -> bool:
    """ Returns True if the string begins and ends with quotes (single or double).
    """
    return (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"'))


def stringToIdentifier(s: str, white_space_becomes: str = '_') -> str:
    """ Takes a string and makes it suitable for use as an identifier.

        Translates to lower case.
        Replaces white space by the white_space_becomes character (default=underscore).
        Removes and punctuation.
    """
    s = s.lower()
    s = re.sub(r"\s+", white_space_becomes, s) # replace whitespace with underscores
    s = re.sub(r"-", "_", s) # replace hyphens with underscores
    s = re.sub(r"[^A-Za-z0-9_]", "", s) # remove everything that's not a character, a digit or a _
    return s


T = TypeVar('T', Dict[Any, Any], List[Any], str)
def replaceStringsInDict(obj: T, old: str, new: str) -> T:
    """ Recursively searches for a string in a dict and replaces a string by another.
    """
    if isinstance(obj, dict):
        return {key: replaceStringsInDict(value, old, new) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [replaceStringsInDict(value, old, new) for value in obj]
    elif is_a_string(obj):
        return obj.replace(old, new)
    else:
        return obj


def replaceEolChars(attr):
    """ Replace end-of-line characters with unicode glyphs so that all table rows fit on one line.
    """
    return (attr.replace('\r\n', unichr(0x21B5))
            .replace('\n', unichr(0x21B5))
            .replace('\r', unichr(0x21B5)))


def pformat(obj: Any, width: int) -> str:
    """ Pretty print format with RTK default parameter values.
    """
    return pprint.pformat(obj, width=width, depth=2, sort_dicts=False)


def wrapHtmlColor(html: str, color: str) -> str:
    """ Wraps HTML in a span with a certain color
    """
    return '<span style="color:{}; white-space:pre;">{}</span>'\
        .format(color, escape(html, quote=False))
