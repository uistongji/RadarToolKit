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


import numpy as np


def ImportClass(FullPath):
    """ Imports from a dot seperated name.
        The full path contains packages and module.
        e.g.: "ISR_Tool.ImagePlot"

        If the module doesn't exist, an ImportedError is raised.
        If the class doesn't exsit, an AttributeError is raised.
    """

    parts = FullPath.rsplit('.', 1)

    if len(parts) == 2:
        ModuleName, ClassName = parts
        ModuleName = str(ModuleName)
        ClassName = str(ClassName)

        module = __import__(ModuleName, fromlist=[ClassName])
        cls = getattr(module, ClassName)

        return cls
    
    elif len(parts) == 1:
        raise ImportError("FullPath should contain a module.")
    else:
        assert False, "Bug: Parts should have 1 or elements: {}".format(parts)


def is_an_array(var, allow_none=False):
    """ Returns True if var is a numpy array.
    """
    return isinstance(var, np.ndarray) or (var is None and allow_none)



