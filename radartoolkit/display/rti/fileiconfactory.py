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


import logging
import os

from ..bindings import QtCore, QtGui, QtSvg
from ..settings import SVG_DIR

logger = logging.getLogger(__name__)


ICON_COLOR_PROC_BXDS  = "#FFEE99" # bxds.bin
ICON_COLOR_PROC_PIK1  = "#D88F08" # MagLoResInco*.bin
ICON_COLOR_PROC_META  = "#D88F08" # MagLoResInco*.meta

ICON_COLOR_PIK1   = ""
ICON_COLOR_NUMPY  = "#B0E0E6"
ICON_COLOR_MAT    = "#B0C4DE"
ICON_COLOR_JSON   = "#D88FD8"
ICON_COLOR_PANDAS = "#880088"

ICON_COLOR_UNDEF      = '#FFFFFF' # White to indicate something went wrong
ICON_COLOR_ERROR      = '#FF0000'
ICON_COLOR_UNKNOWN    = '#999999'
ICON_COLOR_MEMORY     = '#CCEEFF'
ICON_COLOR_RUNNING    = 'red'


class FileIconFactory(object):
    """ A factory class that generates QIcons for use in the File Tree. """
    ICONS_DIRECTORY = SVG_DIR

    """ File State """
    OPEN = "open"
    CLOSED = "closed"


    """ Registered glyph names """
    TRANSPARENT = "transeparent"
    ERROR = "error"
    FOLDER = "folder"
    FILE = "file"
    ARRAY = "array"
    FIELD = "field"
    DIMENSION = "dimension"
    SEQUENCE = "sequence"
    SCALAR = "scalar"
    PROC_BXDS = "proc-bxds"
    PROC_PIK1 = "proc-pik1"
    PROC_META = "proc-meta"


    """ Icon colors from constants defined above """
    COLOR_UNDEF = ICON_COLOR_UNDEF
    COLOR_UNKNOWN = ICON_COLOR_UNKNOWN
    COLOR_ERROR      = ICON_COLOR_ERROR
    COLOR_MEMORY     = ICON_COLOR_MEMORY    

    _singleInstance = None

    def __init__(self):

        self._icons = {}
        self._registry = {}
        self.renderSize = [16, 24, 32, 64]

        self.colorsToBeReplaced = ('#008BFF', '#00AAFF')

        self.registerIcon(None, None)
        self.registerIcon("", None)
        self.registerIcon("transparent_1x1.svg", self.TRANSPARENT)
        self.registerIcon("warning-sign.svg", self.ERROR)
        self.registerIcon("folder-open.svg",  self.FOLDER, True)
        self.registerIcon("folder-close.svg", self.FOLDER, False)
        self.registerIcon("file.svg",         self.FILE, True)
        self.registerIcon("file-inverse.svg", self.FILE, False)
        self.registerIcon("th-large.svg",     self.ARRAY)
        self.registerIcon("asterisk.svg",     self.FIELD)
        self.registerIcon("move.svg",         self.DIMENSION)
        self.registerIcon("align-left.svg",   self.SEQUENCE)
        self.registerIcon("leaf.svg",         self.SCALAR)
        self.registerIcon("leaf.svg", self.PROC_BXDS)
        self.registerIcon("leaf.svg", self.PROC_PIK1)
        self.registerIcon("leaf.svg", self.PROC_META)
    
    @classmethod
    def singleton(cls):
        """ Returns the RtiIconFactory singleton.
        """
        if cls._singleInstance is None:
            cls._singleInstance = cls()
        return cls._singleInstance
    
    def registerIcon(self, fileName, glyph, isOpen=None):
        """ Register an icon SVG file given a filename, optionally with the open/close state.
            :param fileName: filename to the SVG file.
                             If the filename is a relative path, the ICONS_DIRECTORY will be prepended.
            :param glyph: a string describing the glyph (e.g. 'file', 'array')
            :param isOpen: boolean that indicates if the RTI is open or closed.
                            If None, the icon will be registered for open is both True and False
            :return: QIcon
        """

        if fileName and not os.path.isabs(fileName):
            fileName = os.path.join(self.ICONS_DIRECTORY, fileName)
        
        if isOpen is None:
            self._registry[(glyph, True)] = fileName
            self._registry[(glyph, False)] = fileName
        else:
            self._registry[(glyph, isOpen)] = fileName
    
    def getIcon(self, glyph, isOpen, color=None):
        """ Returns a QIcon given a glyph name, open/closed state and color.

            The reslulting icon is cached so that it only needs to be rendered once.

            :param glyph: name of a registered glyph (e.g. 'file', 'array')
            :param isOpen: boolean that indicates if the RTI is open or closed.
            :param color: '#RRGGBB' string (e.g. '#FF0000' for red)
            :return: QtGui.QIcon
        """
        try:
            fileName = self._registry[(glyph, isOpen)]
        except KeyError:
            raise
        return self.loadIcon(fileName, color=color)

    def loadIcon(self, fileName, color=None):
        """ Reads SVG from a file name and creates an QIcon from it.

            Optionally replaces the color. Caches the created icons.

            :param fileName: absolute path to an icon file.
                If False/empty/None, None returned, which yields no icon.
            :param color: '#RRGGBB' string (e.g. '#FF0000' for red)
            :return: QtGui.QIcon
        """
        if not fileName:
            return None

        key = (fileName, color)
        if key not in self._icons:
            try:
                with open(fileName, 'r') as input:
                    svg = input.read()
                self._icons[key] = self.createIconFromSvg(svg, color=color)
            except Exception as ex:
                logger.warning("Unable to read icon: {}".format(ex))
        return self._icons[key]

    def createIconFromSvg(self, svg, color=None, colorsToBeReplaced=None):
        """ Creates a QIcon given an SVG string.

            Optionally replaces the colors in colorsToBeReplaced by color.

            :param svg: string containing Scalable Vector Graphics XML
            :param color: '#RRGGBB' string (e.g. '#FF0000' for red)
            :param colorsToBeReplaced: optional list of colors to be replaced by color
                If None, it will be set to the fill colors of the snip-icon libary
            :return: QtGui.QIcon
        """
        if colorsToBeReplaced is None:
            colorsToBeReplaced = self.colorsToBeReplaced

        if color:
            for oldColor in colorsToBeReplaced:
                svg = svg.replace(oldColor, color)

        """ change color of an svg in pyqt. """
        qByteArray = QtCore.QByteArray(svg.encode('utf-8'))  
        svgRenderer = QtSvg.QSvgRenderer(qByteArray)
        icon = QtGui.QIcon()
        for size in self.renderSize:
            pixMap = QtGui.QPixmap(QtCore.QSize(size, size))
            pixMap.fill(QtCore.Qt.transparent)
            pixPainter = QtGui.QPainter(pixMap)
            pixPainter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)
            pixPainter.setRenderHint(QtGui.QPainter.Antialiasing, True)
            svgRenderer.render(pixPainter)
            pixPainter.end()
            icon.addPixmap(pixMap)  

        return icon



        

    


