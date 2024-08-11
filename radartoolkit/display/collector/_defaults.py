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


""" Default Values for Basic Processing.
"""


class Peach(object):

    _defaultSlicedStep = 15000 # the interval of dataset to be handed
    _maxRois = 2 # the number of maximum rois
    
    TOP_DOCK_HEIGHT = 50 # 75

    # all the displays in the collector tree 
    _NAME_EN, _ROI_EN, _PROC_EN, _AXIS_EN, _HISTORY_EN =\
        True, True, True, True, True

    _COL_COUNT = sum([int(_NAME_EN), int(_PROC_EN), int(_HISTORY_EN)])


STREAM_TO_SAMPLES = {
    'RADnh3': 3437,
    "RADnh5": 3200
    }


class ProcTypes(object):
    
    _FULL4PRIC_RTIS_BACKUP = [
        'bxdBinRti',
        'cohBinRti', 
        'pcBinRti',
        'incohBinRti',
        'unfocBinRti'
    ] 

    _FULL4PRIC_RTIS = [
        "RawBinaryArrayRti",
        'CohBinaryArrayRti', 
        'PcBinaryArrayRti',
        'InBinaryArrayRti',
        'UnfocBinaryArrayRti'
    ] 


    _FULL4PRIC_NAMES = {
        '-': '', # original: Raw
        'Coherent Stacking': 'run_coh_stack',
        'Pulse Compression': 'run_denoise_and_dechirp',
        'Incoherent Stacking': 'run_incoh_stack',
        'Unfocused-SAR': ''
    }
    
    