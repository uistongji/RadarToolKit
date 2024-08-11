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


""" RadarToolKit(RTK) information
"""


import sys

DEBUGGING = ('-d' in sys.argv or '--debug' in sys.argv)
TESTING = True   
PROFILING = False

VERSION = '0.1.0'
REPO_NAME = "radartoolkit"
SCRIPT_NAME = "radartoolkit"
PACKAGE_NAME = "radartoolkit"
PROJECT_NAME = "RadarToolKit(RTK)-Ice Sounding Radar"
SHORT_DESCRIPTION = "Radar Data Organizing, Processing, Viewing and Picking Toolkit."

ORGANIZATION_NAME = "uis.tongji"
ORGANIZATION_DOMAIN = "uis.tongji"

EXIT_CODE_SUCCESS = 0
EXIT_CODE_ERROR = 1
EXIT_CODE_COMMAND_ARGS = 2
EXIT_CODE_RESTART = 66 # Indicates the program is being 'restarted'

KEY_PROGRAM = '_program'
KEY_VERSION = '_version'
