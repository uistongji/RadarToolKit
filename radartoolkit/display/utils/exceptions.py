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



class ISRExceptions(Exception):
    
    """
    Base class for exceptions for ISR_Tool
    """
    pass

class VoidValueError(ISRExceptions):
    
    """
    void return or void input error
    """

    def __init__(self):
        self.errormsg = "Void return or input error."

    def __str__(self):
        return self.errormsg

        

class InvalidDataError(Exception):
    """ Exception that should be raised if the inspector cannot handle this type of data.
        Can be used to distuingish the situation from other exceptions an then, for example,
        draw an empty plot instead of the error message pane.
    """
    pass

class InvalidInputError(Exception):

    pass
