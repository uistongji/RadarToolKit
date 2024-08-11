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
# We would like to acknowledge the contributions from the PRIC and the UTIG.


""" HiCARS2 Legacy Radar Data Breakout.
"""

import logging

from ..utils.plugin import Plugin
from ..bindings import QtSignal, QtCore

logger = logging.getLogger(__name__)


class PIK1Plugins(Plugin):

    DEFAULT_API = ""
    DEFAULT_ABSPYPATH = ""

    def __init__(self, moduleName=None, absPythonPath=None, **kwargs) -> None:
        """
        Constructor.
        """
        moduleName = self.DEFAULT_API if moduleName is None else moduleName
        absPythonPath = self.DEFAULT_ABSPYPATH if absPythonPath is None else absPythonPath

        super(PIK1Plugins, self).__init__(moduleName=moduleName, 
                                           absPythonPath=absPythonPath,
                                           **kwargs
                                        )
        

    def _run(self, name, check_type, *args, **kwargs):
        try:
            if self.importSuccessfully:
                logger.debug(f"Imported module {self.moduleName} successfully. Trying to find object {name} ...")
                
                obj = self.find_object(name=name, check_type=check_type)
                print(f"obj: {obj}")
                if obj is None:
                    return None            
                return obj(*args, **kwargs)        

            else:
                ex = f'module {self.moduleName} not being imported sucessfully: {self._exceptionImport}'
                print(ex) 
        except Exception as ex:
            pass
        

    @staticmethod
    def _getFuncNames(name):
        """
        name: str
            type(BaseRti).__name__: ["HicarsRawFileRti", "HicarsPIK1FileRti"]
        """
        if name == "Raw":
            return "readRawData"
        
        elif name == "Pulse Compression":
            return "runDechirp"

        elif name == "Coherent Stacking":
            return "runCohStack"
        
        elif name == "Incoherent Stacking":
            return "run_incoh_stack"
        
        elif name == "Unfocused-SAR":
            return "run_incoh_stack"
    



class PIK1Thread(QtCore.QThread):

    update_progress = QtSignal(object)
    finished_progress = QtSignal(dict, str, object)
    error_progress = QtSignal(str)
    work_done = QtSignal(object)

    def __init__(self, itemName, checkType, fileName, parentIndex, *args, **kwargs):
        super(PIK1Thread, self).__init__()

        self.funcName = PIK1Plugins._getFuncNames(itemName)
        self.checkType = checkType
        self.fileName = fileName
        self.parentIndex = parentIndex
        self.args = args
        self.kwargs = kwargs


    def run(self):
        print(f"<PIK1Thread.run> called, running the PIK1 procedure for {self.fileName} ...")
        
        pik1Plugins = PIK1Plugins()
        results, kind = pik1Plugins._run(self.funcName, 
                                         self.checkType, self.fileName,
                                         *self.args, **self.kwargs)
        self.finished_progress.emit(results, kind, self.parentIndex)
        self.work_done.emit(self)


