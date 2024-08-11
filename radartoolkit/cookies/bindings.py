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


"""
    Harmonize PySide6 API bindings.
    Basically this script is to provide a linker to the main RTK software.
"""

import os
import sys

import logging
logger = logging.getLogger(__name__)


API_PYSIDE6 = "PySide6"
REQUEST_PYSIDE6 = os.environ.get('QT_API')

# determine whether any QT_APIs environment variables exist
# if not the PySide6, then discard.
if REQUEST_PYSIDE6 != API_PYSIDE6:
    REQUEST_PYSIDE6 = None

# see if module is already imported
if REQUEST_PYSIDE6 is None:
    if 'PySide6' in sys.modules:
        REQUEST_PYSIDE6 = API_PYSIDE6


""" Try to import and do the imports if everything goes well.
"""
# try to import
if REQUEST_PYSIDE6 is None:
    try:
        import PySide6
        REQUEST_PYSIDE6 = API_PYSIDE6
    except ModuleNotFoundError:
        print(f"Required module not found: {API_PYSIDE6}. Link to the RTK main software unsuccessfully.")


# do the imports
if REQUEST_PYSIDE6 == API_PYSIDE6:

    from PySide6.QtCore import Signal as QtSignal, Slot as QtSlot, QObject as QtObject
    from PySide6 import QtCore, QtWidgets

    
else:
    raise RuntimeError(
        "Unable to import the required Qt bindings: {}".format(API_PYSIDE6))


