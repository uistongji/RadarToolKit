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
    Abstract Class for the API `iceRadLib` linking.
"""


import sys
import os
import importlib

from ..bindings import QtObject


class Plugin(QtObject):
    """
    Provides a bridge for the packages.
    """

    def __init__(self, 
                 moduleName: str = None,
                 absPythonPath: str = None,
        ) -> None:
        """
        Constructor.
        """
        super(Plugin, self).__init__()

        self._triedImport = False
        self._exceptionImport = None
        self._niceImport = False
        
        self._moduleName = moduleName
        self._absPythonPath = absPythonPath
        self._moduleClass = None

        self._tryToImportModule()


    @property
    def moduleName(self):
        return self._moduleName
    

    @property
    def moduleClass(self):
        return self._moduleClass
    
    @moduleClass.setter
    def moduleClass(self, cls):
        self._moduleClass = cls
    

    @property
    def absPythonPath(self):
        return self._absPythonPath


    @property
    def triedImport(self):
        """
        Returns True if the corresponding module/class has been imported
        (either successfully or not).
        """
        return self._triedImport
    

    @triedImport.setter
    def triedImport(self, value):
        """
        Sets to be True if the module/class has been successfully imported.
        """
        self._triedImport = value


    @property
    def importSuccessfully(self):
        """
        Returns True if the corresponding module/class 
        has been imported successfully else False.
        """
        return self._triedImport and self._exceptionImport is None

    
    def _tryToImportModule(self):
        """
        Tries to import the registered/required package: iceRadLib. 
        Will set the exception property if an error occurred and return the `LOST` signal.

        There are two ways where the module can be used.
        * install the iceRadLib from conda or pip
        * append the iceRadLib into the sys.PYTHONPATH to import

        STEP1:
        * check whether the
        """
        self._triedImport = True
        self.moduleClass  = None

        if self.moduleName is None:
            self._exceptionImport = f"Procedure._tryImportModule:: invalid module name: {self.moduleName}"
            return
        
        else:
            msg = f"Procedure._tryImportModule:: trying to import module: {self.moduleName}"
            self._exceptionImport = None
            print(msg)

            # check whether the iceRadLib has been imported successfully or not
            REQUEST_API = os.environ.get(self.moduleName)
            if REQUEST_API is None:

                # try to import from the absPythonPath
                if self.absPythonPath is not None:
                    absPythonPath = os.path.abspath(self.absPythonPath)
                    if absPythonPath not in sys.path:
                        sys.path.append(absPythonPath)

                try:
                    self.moduleClass = importlib.import_module(self.moduleName)
                    print(f"Procedure._tryImportModule:: module {self.moduleName} loaded successfully.")

                except Exception as ex:
                    msg = f"Procedure._tryImportModule:: unable to import {self.moduleName} due to: {ex}"
                    self._exceptionImport = msg
                    print(msg)


    def find_object(self, name: str, check_type=callable):
        """
        Recursively finds a class/function in a module and its submodules.

        :param name: Name of the class/function to find.
        :return: The class/function if found, otherwise None.
        """
        return self._find_attr(self.moduleClass, name, check_type=check_type)
    

    def _find_attr(self, module, attrName, check_type):
        """
        Helper method to recursively find an attribute in a module and its submodules.

        :param module: The module to search in.
        :param attr_name: Name of the attribute to find.
        :param check_type: Function to check the type of the attribute (e.g., isinstance or callable).
        :return: The attribute if found, otherwise None.
        """
        if hasattr(module, attrName):
            attr = getattr(module, attrName)
            if check_type(attr):
                return attr

        # Recursively check submodules
        for sub_attr_name in dir(module):
            sub_attr = getattr(module, sub_attr_name)
            if isinstance(sub_attr, type(module)):  # Check if it's a submodule
                result = self._find_attr(sub_attr, attrName, check_type)
                if result:
                    return result

        return None




