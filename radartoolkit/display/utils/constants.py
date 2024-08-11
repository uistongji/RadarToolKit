#!/usr/bin.env python

import sys
from ..bindings import QtGui

# --- File Tree View Constants ---
COL_NODE_NAME_WIDTH = 180
COL_KIND_WIDTH = 50
COL_ELEM_TYPE_WIDTH = 80
COL_SUMMARY_WIDTH = 110


# Spacing and margin in dock widgets in pixels. Is now set in style sheet margin.
DOCK_SPACING = 0
DOCK_MARGIN  = 0

if sys.platform == 'linux':
    MONO_FONT = 'Monospace'
    FONT_SIZE = 10
elif sys.platform == 'win32' or sys.platform == 'cygwin':
    MONO_FONT = 'Courier'
    FONT_SIZE = 10
elif sys.platform == 'darwin':
    MONO_FONT = 'Courier'
    FONT_SIZE = 13
else:
    MONO_FONT = 'Courier'
    FONT_SIZE = 13

COLOR_ERROR = '#FF0000' # red

QCOLOR_REGULAR = QtGui.QColor('black')
QCOLOR_NOT_IMPORTED = QtGui.QColor('grey')
QCOLOR_ERROR = QtGui.QColor(COLOR_ERROR)