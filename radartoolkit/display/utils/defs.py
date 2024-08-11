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


""" Various definitions, errors and constants that can be used throughout the program

"""
import sys

CONTIGUOUS = 'contiguous'  # contiguous chunking

# String formatting template for numbered dimension names
DIM_TEMPLATE = "dim-{}"
SUB_DIM_TEMPLATE = "subdim-{}"

# Use different unicode character per platform as it looks better.
if sys.platform == 'linux':
    RIGHT_ARROW = "\u2794"
elif sys.platform == 'win32' or sys.platform == 'cygwin':
    RIGHT_ARROW = "\u2794"
elif sys.platform == 'darwin':
    RIGHT_ARROW = "\u279E"
else:
    RIGHT_ARROW = "\u2794"


class InvalidInputError(Exception):
    """ Exception raised when the input is invalid after editing
    """
    pass


