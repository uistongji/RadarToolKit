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


""" Defines a global RTI registry to register repository tree item plugins.
"""

import logging
import os
import fnmatch

from ..settings import DEBUGGING
from ..reg.basereg import BaseRegItem, BaseRegistry, RegType
from .fileiconfactory import FileIconFactory, ICON_COLOR_UNDEF
from ..utils.check_class import check_class, is_a_color_str, is_a_color_str
# from .rtis import RawBinaryArrayRti



logger = logging.getLogger(__name__)


class RtiRegItem(BaseRegItem):
    """ 
    Class to keep track of a registered File Tree Items.
    """
    FIELDS = BaseRegItem.FIELDS[:1] + ['iconColor', 'globs'] + BaseRegItem.FIELDS[1:]
    TYPES = BaseRegItem.TYPES[:1] + [RegType.ColorStr, RegType.String] + BaseRegItem.TYPES[1:]
    LABELS  = BaseRegItem.LABELS[:1] + ['Icon Color', 'Globs'] + BaseRegItem.LABELS[1:]
    STRETCH = BaseRegItem.STRETCH[:1] + [False, True] + BaseRegItem.STRETCH[1:]

    # Display Icon in the main column
    COL_DECORATION = 0   

    def __init__(self, name='', absClassName='', pythonPath='', iconColor=ICON_COLOR_UNDEF, globs='', info=''):
        """ 
        Constructor. See the ClassRegItem class doc string for the parameter help.
        """
        super(RtiRegItem, self).__init__(name=name, absClassName=absClassName, pythonPath=pythonPath)
        check_class(globs, str)
        assert is_a_color_str(iconColor), \
            "Icon color for {} is not a color string: {!r}".format(self, iconColor)

        self._data['iconColor'] = iconColor
        self._data['globs'] = globs
        self._data['info'] = info


    def __str__(self):
        return "<RtiRegItem: {}>".format(self.name)


    @property
    def iconColor(self):
        """ 
        Icon color hex string.
        """
        return self._data['iconColor']


    @property
    def globList(self):
        """ 
        Returns list of globs by splitting the globs string at the colons (:).
        """
        return self._data['globs'].split(';')
    

    @property
    def decoration(self):
        """ The displayed icon.
        """
        rtiIconFactory = FileIconFactory.singleton()

        if self._exception:
            return rtiIconFactory.getIcon(
                rtiIconFactory.ERROR, isOpen=False, color=rtiIconFactory.COLOR_ERROR)
        else:
            if self._cls is None:
                return rtiIconFactory.getIcon(
                    rtiIconFactory.ERROR, isOpen=False, color=rtiIconFactory.COLOR_UNKNOWN)
            else:
                return rtiIconFactory.getIcon(
                    self.cls._defaultIconGlyph, isOpen=False, color=self.iconColor)


    def pathNameMatchesGlobs(self, path):
        """ Returns True if the file path matches one of the globs

            Matching is case-insensitive. See the Python fnmatch module for further info.
        """
        for glob in self.globList:
            if DEBUGGING:
                logger.debug("  glob '{}' -> match = {}".format(glob, fnmatch(path, glob)))
            if fnmatch(path, glob):
                return True
        return False
    

    def getFileDialogFilter(self):
        """ Returns a filters that can be used to construct file dialogs filters,
            for example: 'Text File (*.txt;*.text)'
        """
        # Remove any path info from the glob. E.g. '/mypath/prefix*1.nc' becomes '*.nc'
        extensions = ['*' + os.path.splitext(glob)[1] for glob in self.globList]
        return '{} ({})'.format(self.name, ';'.join(extensions))



class FileRegistry(BaseRegistry):
    """ 
    Class that can be used to register repository tree items (RTIs).

    Maintains a name to RtiClass mapping and an extension to RtiClass mapping.
    The extension in the extensionToRti assure that a unique RTI is used as default mapping,
    the extensions in the RtiRegItem class do not have to be unique and are used in the
    filter in the getFileDialogFilter function.
    """

    ITEM_CLASS = RtiRegItem
    DIRECTORY_REG_ITEM = RtiRegItem('Directory', 
                                    'display.rti.rtis.DirectoryRti',
                                    iconColor=ICON_COLOR_UNDEF)


    def __init__(self):
        super(FileRegistry, self).__init__()
        self._extensionMap = {}

    
    def getRtiRegItemByExtension(self, filePath):
        """ Returns the first RtiRegItem class where filePath matches one of the globs patherns.
            Returns None if no class registered for the extension.
        """
        logger.debug("{} getRtiRegItemByExtenstion, filePath: {}".format(self, filePath))
        for rtiRegItem in self._items:
            if rtiRegItem.pathNameMatchesGlobs(filePath):
                return rtiRegItem
        return None
 

    def getFileDialogFilter(self):
        """ Returns a filter that can be used in open file dialogs,
            for example: 'All files (*);;mat (*.mat);;py(*.py);;binary(*.bin)'
        """        
        filters = []
        for regRti in self.items:
            filters.append(regRti.getFileDialogFilter())
        return ';;'.join(filters)
    
    
    def extraItemsForOpenAsMenu(self):
        """ Creates list of RtiRegItem to append to the 'open-as' and 'reload-as menus
        """
        return [self.DIRECTORY_REG_ITEM]


    def getDefaultSaveItems(self):
        """ 
        Returns a list when the default plugins in the file tree item registry for 'save' functionality.
        """
        plugins = self.getDefaultItems()[2:4]
        return plugins
    
    
    def getDefaultItems(self):
        """ 
        Returns a list with the default plugins in the file tree item registry.
        """
        plugins = [
            RtiRegItem('Hicars2 Raw File [bxds.bin]',
                       'display.rti.rtis.HicarsRawFileRti',
                       iconColor="#FFC450",
                       globs='.'),

            RtiRegItem('Hicars2 PIK1 File [MagLoResInco*]',
                       'display.rti.rtis.HicarsPIK1FileRti',
                       iconColor="#5ECD8B",
                       globs='.'),

            RtiRegItem('Matlab Binary File[*.mat]',
                       'display.rti.rtis.MatlabFileRti',
                       iconColor="#D55276",
                       globs='*.mat'),
            
            RtiRegItem('Numpy Binary File [*.npy]',
                       'display.rti.rtis.NumpyBinaryFileRti',
                       iconColor="#F1A7B5",
                       globs='*.npy'),
            
            RtiRegItem('Nc File [*.nc]',
                       'display.rti.rtis.NcFileRti',
                       iconColor="#B4D4F8",
                       globs='*.nc'
                       )
                    ]
        return plugins

        
    
    


def createGlobalRegistryFunction():
    """ Closure to create the RtiRegistry singleton
    """
    globReg = FileRegistry()

    def accessGlobalRegistry():
        return globReg
    
    return accessGlobalRegistry


globalFileRegistry = createGlobalRegistryFunction()
globalFileRegistry.__doc__ = "Function that returns the FileRegistry singleton common to all windows."




    
