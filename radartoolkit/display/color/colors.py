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


""" Color Libaray
"""


from ..utils.singletonmaxin import SingletonMixin

import logging
import os.path
from os import listdir
from cmlib import CmLib, CmLibModel, DATA_DIR

logger = logging.getLogger(__name__)


DEF_FAV_COLOR_MAPS = [
    'SciColMaps/Oleron', 'SciColMaps/Nuuk', 'SciColMaps/Acton', 'CET/CET-CBL2', 'MatPlotLib/Gray',
    'CET/CET-C2', 'CET/CET-R2', 'MatPlotLib/BrBG', 'MatPlotLib/Tab20', 'MatPlotLib/Magma',
    'MatPlotLib/Tab10', 'MatPlotLib/Cubehelix', 'MatPlotLib/Viridis', 'MatPlotLib/Coolwarm']

DEFAULT_COLOR_MAP = "MatPlotLib/Magma"
assert DEFAULT_COLOR_MAP in DEF_FAV_COLOR_MAPS, "Default color map not in default favorites."



class CmLibSingleton(CmLib, SingletonMixin):

    def __init__(self, **kwargs):

        super(CmLibSingleton, self).__init__(**kwargs)

        logger.debug("CmLib singleton: {}".format(self))

        cmDataDir = DATA_DIR
        logger.info("Importing color map library from: {}".format(cmDataDir))

        excludeList = ['ColorBrewer2']
        for path in listdir(cmDataDir):
            if path in excludeList:
                logger.debug("Not importing catalogue from exlude list: {}".format(excludeList))
                continue

            fullPath = os.path.join(cmDataDir, path)
            if os.path.isdir(fullPath):
                self.load_catalog(fullPath)

        logger.debug("Number of color maps: {}".format(len(self.color_maps)))



class CmLibModelSingleton(CmLibModel, SingletonMixin):

    def __init__(self, **kwargs):

        super(CmLibModelSingleton, self).__init__(CmLibSingleton.instance(), **kwargs)
    
        