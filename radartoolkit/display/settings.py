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


import sys
import os

from .bindings import QtCore


DEBUGGING = ('-d' in sys.argv or '--debug' in sys.argv)
TESTING = False
PROFILING = False 

INVISIBLE_ROOT_NAME = '<invisible-root>'
HEADERS = tuple('<first column') # ('<', 'f', ...)
TREE_CELL_SIZE_HINT = QtCore.QSize(100, 20)


"""
Data (bxds & out) -- dir path settings
"""
ISR_DataInPath = os.path.join(os.getcwd(), "Target_Data")
ISR_DataInPath_bxds = os.path.join(ISR_DataInPath,"In/BreakOut") 
ISR_DataOutPath = os.path.join(ISR_DataInPath,"Out")


""" Resources dir, e.g., config file, icons and etc.
"""
RTK = os.getcwd()
RESOURCES = os.path.join(RTK, "radartoolkit/display/resources")
# ------------------- #
ICONS_DIR = os.path.join(RESOURCES, "icons")
SVG_DIR = os.path.join(RESOURCES, "svgs")
FONTS_DIR = os.path.join(RESOURCES, "fonts")
XMLS_DIR = os.path.join(RESOURCES, "xmls")
CSS_DIR = os.path.join(RESOURCES, "css")


# -----CONFIG-FILE------ #
CONFIG_FILE = os.path.join(RESOURCES, "settings/rtk.json")
LOGGING_FILE = os.path.join(RESOURCES, "settings/logging.json") 


""" Setup UI-configs
"""
# --------LOG--------- #
LOG_ICON_SIZE = QtCore.QSize(16, 16)
LOG_DATETIME_COLOR = "Indigo"

# -----FILE-TREE------ #
DOCK_SPACING = 0
DOCK_MARGIN = 0
COL_NODE_NAME_WIDTH = 180
COL_KIND_WIDTH = 50
COL_ELEM_TYPE_WIDTH = 80
COL_SUMMARY_WIDTH = 110
LEFT_DOCK_WIDTH = 440  
RIGHT_DOCK_WIDTH = 320
TOP_DOCK_HEIGHT = 75
TREE_ICON_SIZE = QtCore.QSize(16, 16)

# ---RIGHT-ARROW---- #
CONTIGUOUS = 'contiguous'
DIM_TEMPLATE = "dim-{}"
SUB_DIM_TEMPLATE = "subdim-{}"

if sys.platform == 'linux':
   RIGHT_ARROW = "\u2794"
elif sys.platform == 'win32' or sys.platform == 'cygwin':
   RIGHT_ARROW = "\u2794"
elif sys.platform == "darwin":
   RIGHT_ARROW = "\u279E"
else:
   RIGHT_ARROW = "\u2794"

# ---- Collector ---- #
COLLECTOR_TREE_ICON_SIZE = QtCore.QSize(20, 20)
COLLECTOR_BTN_ICON_SIZE = QtCore.QSize(16, 16)

# ---- Others ---- #
DEFAULT_FUNCS = ["bo", "pik1", "view"]

# ---- MODULE ---- #
COOKIES_MODULE = "radartoolkit.cookies.quality.xlob.RAD.pik1.procs'" 

# ---- COLORS ---- #
DEFAULT_COLORS = ['#FFA07A', '#FF8C00', '#EEE8AA',
                  '#90EE90', '#7FFFD4', '#1E90FF']

# ---- PROCESSING ---- #
PROCEDURE_PARAMS = ['SEASON', 'RADAR', 'FLIGHT',
                   'ORIG_DIR', 'XPED_DIR', 'AUTO-PICK']



SIM_ROW_TITLE, SIM_COL_TITLE = 0, 0  # colspan = 4
SIM_ROW_IMAGE_ASCANS, SIM_COL_IMAGE_ASCANS = 0, 0  # colspan = 2
SIM_ROW_IMAGE_BSCAN, SIM_COL_IMAGE_BSCAN = 0, 2  # colspan = 2
SIM_ROW_IMAGE_PC, SIM_COL_IMAGE_PC = 3, 0  # colspan = 2
SIM_ROW_IMAGE_BP, SIM_COL_IMAGE_BP = 3, 2