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
    File Registry Items for Loading in the Filehub Widget.
"""


import logging
import os
import numpy as np
import scipy.io as io

from .memoryrti import ArrayRti, MappingRti
from .fileiconfactory import FileIconFactory, \
            ICON_COLOR_UNDEF, ICON_COLOR_UNKNOWN, ICON_COLOR_MEMORY, \
            ICON_COLOR_MAT, ICON_COLOR_RUNNING
from ..utils.check_class import check_is_an_array
from .baserti import BaseRti
from .registry import globalFileRegistry
from ..bindings import QtCore


logger = logging.getLogger(__name__)

ALLOW_PICKLE = False




def createExpansiveRtis(kind):
    """
    Returns the BaseRegItem concerning the type.
    """
    if kind == "Raw":
        return RawBinaryArrayRti
    
    elif kind == "Pulse Compression":
        return PcBinaryArrayRti
    
    elif kind == "Coherent Stacking":
        return CohBinaryArrayRti
    
    elif kind == "Incoherent Stacking":
        return IncohBinaryArrayRti
    
    elif kind == "Unfocused-SAR":
        return UnfocBinaryArrayRti
    


def getExpansiveTasksName():
    """
    Returns a list that contains the long running BaseRti items' names.
    """
    names = {"HicarsRawFileRti": 'raw', 
            #  "HicarsPIK1FileRti": 'pik1'
                }
    return names
    


def _detectRtiFromFileName(fileName):
    """ 
    Determines the type of RepoTreeItem to use given a file or directory name.
    Uses a DirectoryRti for directories without a registered extension and an UnknownFileRti
    if the file extension doesn't match one of the registered RTI globs.

    Returns (cls, regItem) tuple. Both the cls ond the regItem can be None.
    If the file is a directory without a registered extension, (DirectoryRti, None) is returned.
    If the file extension is not in the registry, (UnknownFileRti, None) is returned.
    If the cls cannot be imported (None, regItem) returned. regItem.exception will be set.
    Otherwise (cls, regItem) will be returned.

        Note that directories can have an extension (e.g. extdir archives). So it is not enough to
        just test if a file is a directory.
    """

    fullPath = os.path.normpath(os.path.abspath(fileName))
    rtiRegItem = globalFileRegistry().getRtiRegItemByExtension(fullPath)

    if rtiRegItem is None:
        if os.path.isdir(fileName):
            # if 'BreakOut' in fileName:
            #     cls = BxdsDirectoryRti
            # elif 'Processed' in fileName:
            #     cls = ProcDirectoryRti
            # else:
                cls = DirectoryRti
        else:
            logger.debug("No file RTI registered for path: {}".format(fullPath))
            cls = UnknownFileRti
    else:
         cls = rtiRegItem.getClass(tryImport=True) # cls can be None
    return cls, rtiRegItem



def createRtiFromFileName(fileName):
    """ 
    Determines the type of RepoTreeItem to use given a file or directory name and creates it.
    Uses a DirectoryRti for directories without registered extensions and an UnknownFileRti if the file
    extension doesn't match one of the registered RTI extensions.
    """

    cls, rtiRegItem = _detectRtiFromFileName(fileName)
    assert not (cls is None and rtiRegItem is None), "cls and rtiRegItem both none."

    iconColor = rtiRegItem.iconColor if rtiRegItem else ICON_COLOR_UNKNOWN

    if cls is None:
        logger.warning("Unable to import plugin {}: {}"
                       .format(rtiRegItem.name, rtiRegItem.exception))
        rti = UnknownFileRti.createFromFileName(fileName, ICON_COLOR_UNKNOWN)
        rti.setException(rtiRegItem.exception)
    else:
        logger.debug("Calling createFromFileName: {} ({}, {})".format(cls, fileName, iconColor))
        rti = cls.createFromFileName(fileName, iconColor)

    assert rti, "Sanity check failed (createRtiFromFileName). Please report this bug."
    return rti




class UnknownFileRti(BaseRti):
    """ 
    A repository tree item that represents a file of unknown type.
    The file is not opened.
    """
    _defaultIconGlyph = FileIconFactory.FILE

    def __init__(self, nodeName='', iconColor=ICON_COLOR_UNKNOWN, fileName=''):
        """ Constructor
        """
        super(UnknownFileRti, self).__init__(
            nodeName=nodeName, iconColor=iconColor, fileName=fileName)
        self._checkFileExists()


    def hasChildren(self):
        """ Returns False. Leaf nodes never have children. """
        return False
    


class LongRunningRti(BaseRti):
    """
    The repository tree item for the long-running tree item
    that represents a file which requires massive computational loads. 
    The file cannot be open yet.
    """

    _defaultIconGlyph = FileIconFactory.SEQUENCE

    def __init__(self, nodeName='', iconColor=ICON_COLOR_RUNNING, fileName=''):
        super(LongRunningRti, self).__init__(nodeName, iconColor, fileName)
        self._checkFileExists()
        self._ready = False


    def hasChildren(self):
        return False




class DirectoryRti(BaseRti):
    """ 
    A directory in the repository data tree
    """
    _defaultIconGlyph = FileIconFactory.FOLDER
    _defaultIconColor = FileIconFactory.COLOR_UNKNOWN


    def __init__(self, nodeName='', iconColor=ICON_COLOR_UNKNOWN, fileName=''):
        
        super(DirectoryRti, self).__init__(
            nodeName=nodeName, iconColor=iconColor, fileName=fileName)
        self._checkFileExists()


    def _fetchAllChildren(self):
        """ Gets all sub directories and files within the current directory.
            Does not fetch hidden files.
        """
        childItems = []
        fileNames = sorted(os.listdir(self._fileName), key=lambda s: s.lower())       
        absFileNames = [os.path.join(self._fileName, fn) for fn in fileNames]

        for fileName, absFileName in zip(fileNames, absFileNames):
            if not fileName.startswith('.'):
                childItem = createRtiFromFileName(absFileName)
                childItems.append(childItem)

        return childItem


    



""" In the new version, I don't care how well the user can understand, 
    but just offer any possible processing methods.
    
     HiCARS2 Rtis in support of radar processing:
    bxdsBinRti, cohBinRti, pcBinRti, incohBinRti. -> hicars2BinRti(MappingRti)
    * I have to mention that, in order to proceed correctly, 
      any steps made follow the right flows.
    e.g., bxdsBinRti -> cohBinRti -> pcBinRti -> unfocBinRti(incohBinRti) (x)
    * Maybe ... I don't need to consider this, 
      cause it only depends how well the usr can understand ... Right?
    e.g., bxdsBinRti, cohBinRti, pcBinRti, incohBinRti, unfocBinRti ... (equally)
"""



class HicarsRawFileRti(MappingRti):
    """ 
    HiCARS2 mapping binary file, directly loaded from the fileWidget, 
    Returns a dict with 2 channels dataset.
    """
    _defaultIconGlyph = FileIconFactory.PROC_BXDS

    def __init__(self, nodeName='', fileName='', iconColor=ICON_COLOR_MEMORY):
        super(HicarsRawFileRti, self).__init__(None,
                                             nodeName=nodeName, 
                                             fileName=fileName,
                                             iconColor=iconColor)
        self._checkFileExists()
        

    def hasChildren(self):
        """
        Returns True if the item has (fetched or unfetched) children.
        """
        return True
    

    def _openResources(self):
        self._dictionary = {}


    def _closeResources(self):
        self._dictionary = None



class RawBinaryArrayRti(ArrayRti):

    def __init__(self, array=None, nodeName='', fileName='', parentIndex=QtCore.QModelIndex()):
        super(RawBinaryArrayRti, self).__init__(array, 
                                                nodeName=nodeName, 
                                                fileName=fileName)
        self._checkFileExists()
        self.parentIndex = parentIndex

    
    def hasChildren(self):
        """
        Returns True so that the file can be opened, even though the array has no children.
        """
        return True
    

    def _openResources(self):
        arr = np.load(self._fileName, allow_pickle=ALLOW_PICKLE)
        check_is_an_array(arr)
        self._array = arr


    def _closeResources(self):
        self._array = None



class CohBinaryArrayRti(ArrayRti):

    def __init__(self, array=None, nodeName='', fileName='', parentIndex=QtCore.QModelIndex()):
        super(CohBinaryArrayRti, self).__init__(array, 
                                                nodeName=nodeName, 
                                                fileName=fileName)
        self._checkFileExists()
        self.parentIndex = parentIndex

    
    def hasChildren(self):
        """
        Returns True so that the file can be opened, even though the array has no children.
        """
        return True
    

    def _openResources(self):
        arr = np.load(self._fileName, allow_pickle=ALLOW_PICKLE)
        check_is_an_array(arr)
        self._array = arr


    def _closeResources(self):
        self._array = None



class IncohBinaryArrayRti(ArrayRti):

    def __init__(self, array=None, nodeName='', fileName='', parentIndex=QtCore.QModelIndex()):
        super(CohBinaryArrayRti, self).__init__(array, 
                                                nodeName=nodeName, 
                                                fileName=fileName)
        self._checkFileExists()
        self.parentIndex = parentIndex

    
    def hasChildren(self):
        """
        Returns True so that the file can be opened, even though the array has no children.
        """
        return True
    

    def _openResources(self):
        arr = np.load(self._fileName, allow_pickle=ALLOW_PICKLE)
        check_is_an_array(arr)
        self._array = arr


    def _closeResources(self):
        self._array = None




class UnfocBinaryArrayRti(ArrayRti):

    def __init__(self, array=None, nodeName='', fileName='', parentIndex=QtCore.QModelIndex()):
        super(CohBinaryArrayRti, self).__init__(array, 
                                                nodeName=nodeName, 
                                                fileName=fileName)
        self._checkFileExists()
        self.parentIndex = parentIndex

    
    def hasChildren(self):
        """
        Returns True so that the file can be opened, even though the array has no children.
        """
        return True
    

    def _openResources(self):
        arr = np.load(self._fileName, allow_pickle=ALLOW_PICKLE)
        check_is_an_array(arr)
        self._array = arr


    def _closeResources(self):
        self._array = None
        



class PcBinaryArrayRti(ArrayRti):

    def __init__(self, array=None, nodeName='', fileName='', parentIndex=QtCore.QModelIndex()):
        super(CohBinaryArrayRti, self).__init__(array, 
                                                nodeName=nodeName, 
                                                fileName=fileName)
        self._checkFileExists()
        self.parentIndex = parentIndex

    
    def hasChildren(self):
        """
        Returns True so that the file can be opened, even though the array has no children.
        """
        return True
    

    def _openResources(self):
        arr = np.load(self._fileName, allow_pickle=ALLOW_PICKLE)
        check_is_an_array(arr)
        self._array = arr


    def _closeResources(self):
        self._array = None



class HicarsPIK1FileRti(MappingRti):
    
    _defaultIconGlyph = FileIconFactory.PROC_PIK1

    def __init__(self, nodeName='', fileName='', iconColor=ICON_COLOR_MEMORY):
        super(HicarsPIK1FileRti, self).__init__(None,
                                                nodeName=nodeName, 
                                                fileName=fileName,
                                                iconColor=iconColor)
        self._checkFileExists()


    def hasChildren(self):
        """
        Returns True if the item has (fetched or unfetched) children.
        """
        return True
    

    def _openResources(self):
        self._dictionary = {}

        fileSize = os.path.getsize(self._fileName)
        if fileSize == 0:
            msg = f"Requested pik1 file is empty: {self._fileName}"
            raise Exception(msg)

        nSamples = 3200
        nTraces = fileSize // (4*nSamples)
        data = np.memmap(self._fileName, '>i4', mode='r', shape=(nTraces, nSamples))
        self._dictionary["pik1"] = data


    def _closeResources(self):
        self._dictionary = None



class PIK1BinaryArrayRti(ArrayRti):

    def __init__(self, nodeName='', fileName=''):
        super(PIK1BinaryArrayRti, self).__init__(None, 
                                                 nodeName=nodeName, 
                                                 fileName=fileName)
        self._checkFileExists()


    def _openResources(self):
        arr = np.load(self._fileName, allow_pickle=ALLOW_PICKLE)
        check_is_an_array(arr)
        self._array = arr


    def _closeResources(self):
        self._array = None



class MatlabFileRti(MappingRti):
    """ Read data from a MATLAB file using the scipy.io.loadmat function.

        Note: v4 (Level 1.0), v6 and v7 to 7.2 matfiles are supported.

        From version 7.3 onward matfiles are stored in HDF-5 format. You can read them with the
        RTK hDF-5 plugin (which uses on h5py)
    """
    _defaultIconGlyph = FileIconFactory.FILE    

    def __init__(self, nodeName='', fileName='', iconColor=ICON_COLOR_MAT):
        """ Constructor. Initializes as an MappingRti with None as underlying dictionary.
        """
        super(MatlabFileRti, self).__init__(None, nodeName=nodeName, fileName=fileName,
                                            iconColor=iconColor)
        self._checkFileExists()    


    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children
        """
        return True


    def _openResources(self):
        """ Uses numpy.loadtxt to open the underlying file
        """
        self._dictionary = io.loadmat(self._fileName)


    def _closeResources(self):
        """ Closes the underlying resources
        """
        self._dictionary = None





class NumpyBinaryFileRti(ArrayRti):
    """ 
    Reads a single Numpy array from a binary file (.npy) using numpy.load().

    The file must have been saved with numpy.save() A TypeError is raised if this is not the
    The allow_pickle is set to False, therefore no object arrays can be read.
    """
    _defaultIconGlyph = FileIconFactory.FILE

    def __init__(self, nodeName='', iconColor=ICON_COLOR_UNDEF, fileName=''):
        super(NumpyBinaryFileRti, self).__init__(None, nodeName=nodeName, 
                                                 iconColor=iconColor, 
                                                 fileName=fileName)
        self._checkFileExists()


    def hasChildren(self):
        return True
    
    
    def _openResources(self):
        arr = np.load(self._fileName, allow_pickle=ALLOW_PICKLE)
        check_is_an_array(arr)
        self._array = arr


    def _closeResources(self):
        self._array = None















