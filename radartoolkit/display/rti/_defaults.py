#!/usr/bin.env python

""" set defaults value for better interpretating
    the type of rti-item with relevant processing methods.
"""

import enum


STREAM_TO_SAMPLES = {
    'RADnh3': 3437,
    "RADnh5": 3200
    }

class ProcTypes(object):
    
    _FULL4PRIC_RTIS = [
        'bxdBinRti',
        'cohBinRti', 
        'pcBinRti',
        'incohBinRti',
        'unfocBinRti'
    ] 


    _FULL4PRIC_NAMES = {
        '-': '', # original: Raw
        'Coherent Stacking': 'run_coh_stack',
        'Pulse Compression': 'run_denoise_and_dechirp',
        'Incoherent Stacking': 'run_incoh_stack',
        'Unfocused-SAR': ''
    }





    

