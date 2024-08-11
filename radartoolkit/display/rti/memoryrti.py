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


""" Store and Tree items for representing data that is stored in memory.
    The memory-RTIs store the attributes per-object (instead of returning an emtpy dictionary)
"""

from .baserti import BaseRti
from .fileiconfactory import FileIconFactory
from ..utils.check_class import (check_is_an_array, is_a_sequence, is_an_array, 
                                 is_a_mapping, check_is_a_sequence, check_is_a_mapping, typeName)
from ..utils.misc import pformat
from ..utils.defs import DIM_TEMPLATE, SUB_DIM_TEMPLATE
from .baserti import shapeToSummary, lengthToSummary

import logging
import numpy as np

logger = logging.getLogger(__name__)

ICON_COLOR_MEMORY = FileIconFactory.COLOR_MEMORY


def _createFromObject(obj, *args, **kwargs):
    """ Creates an rti given an object. Auto-detects its class. 
        *args and **kwargs paraemeters are passed to the rti constructor.
    """
    if is_a_sequence(obj):
        return SequenceRti(obj, *args, **kwargs)
    elif is_a_mapping(obj):
        return MappingRti(obj, *args, **kwargs)
    elif is_an_array(obj):
        return ArrayRti(obj, *args, **kwargs)
    elif isinstance(obj, bytearray):
        return ArrayRti(np.array(obj), *args, **kwargs)
    else:
        return ScalarRti(obj, *args, **kwargs)
    

def getMissingDataValue(obj):
    """ Returns obj.fill_value or None if obj doesn't have a fill_value property.

        Typically masked arrays have a fill_value and regular Numpy arrays don't.
        If array is None, this funcion returns None, indicating no fill value.

        :param array: None or a numpy array (masked or regular.
        :return: None or value that represents missing data
    """
    if obj is None:
        return None
    else:
        try:
            return obj.fill_value # Masked arrays
        except AttributeError:
            return None # Regular Numpy arrays and scalar have no missing data value


class ScalarRti(BaseRti):
    """ stores a *.npy or *.mat scalar """
    _defaultIconGlyph = FileIconFactory.SCALAR

    def __init__(self, scalar, nodeName='', iconColor=ICON_COLOR_MEMORY, fileName='', attributes=None):
        super(ScalarRti, self).__init__(nodeName=nodeName, iconColor=iconColor, fileName=fileName)
        self._scalar = scalar
        self._attributes = {} if attributes is None else attributes
    
    @property
    def attributes(self):
        return self._attributes
    
    @property
    def isSliceable(self):
        return super().isSliceable
    
    @property
    def arrayShape(self):
        """ Returns the shape of the wrapper array. Will always be an empty tuple()
        """
        return tuple()

    @property
    def dimensionality(self):
        """ String that describes if the RTI is an array, scalar, field, etc.
        """
        return "scalar"
    
    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        return typeName(self._scalar)

    @property
    def missingDataValue(self):
        """ Returns the value to indicate missing data.
        """
        return getMissingDataValue(self._scalar)

    @property
    def summary(self):
        """ Returns a summary of the contents of the RTI. In this case the scalar as a string
        """
        return str(self._scalar)
    
    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).
            The scalar will be wrapped in an array with one element so it can be inspected.
        """
        return self._scalar
    
    def hasChildren(self):
        """ returns False. Leaf nodes never have children. """
        return False
    

class FieldRti(BaseRti):
    """ Repository Tree Item (rti) that contains a field in a structured numpy array """
    _defaultIconGlyph = FileIconFactory.FIELD

    def __init__(self, array, nodeName, iconColor=ICON_COLOR_MEMORY, fileName='', attributes=None):
        """ Constructor.
            The name of the field must be given to the nodeName parameter.
            The attributes can be set so the parent's attributes can be reused.
        """
        super(FieldRti, self).__init__(nodeName, iconColor, fileName)
        check_is_an_array(array, allow_none=True)

        self._array =  array
        fieldName = self.nodeName

        # dtype.fields returns a tuple with (dtype, offset, shape) so we use its first element.
        self._fieldDtype = self._array.dtype.fields[fieldName][0]

        self._attributes = {} if attributes is None else attributes

    @property
    def attributes(self):
        """ The attribute dictionary.
            Reimplemented from BaseRti: he attribute dictionary is stored per-object instead of
            per-class.
        """
        return self._attributes

    @property
    def _isStructured(self):
        """ Returns True if the variable has a structured type, otherwise returns False.
        """
        return bool(self._fieldDtype.names)

    @property
    def isSliceable(self):
        """ Returns True if the underlying array is not None.
        """
        return self._array is not None
    
    @property
    def nDims(self):
        """ The number of dimensions of the underlying array
        """
        return self._array.ndim + len(self._subArrayShape)

    @property
    def _subArrayShape(self):
        """ Returns the shape of the sub-array.
            An empty tuple is returned for regular fields, which have no sub array.
        """
        return self._fieldDtype.shape

    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
            If the field contains a subarray the shape may be longer than 1.
        """
        return self._array.shape + self._subArrayShape

    @property
    def dimensionality(self):
        """ String that describes if the RTI is an array, scalar, field, etc.
        """
        return "field"
    
    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        if self._array is None:
            return super(FieldRti, self).elementTypeName
        else:
            return '<structured>' if self._fieldDtype.names else str(self._fieldDtype)
        
    @property
    def dimensionNames(self):
        """ Returns a list with the dimension names of the underlying NCDF variable
        """
        mainArrayDims = [DIM_TEMPLATE.format(dimNr) for dimNr in range(self._array.ndim)]
        nSubDims = len(self._subArrayShape)
        subArrayDims = [SUB_DIM_TEMPLATE.format(dimNr) for dimNr in range(nSubDims)]
        return mainArrayDims + subArrayDims

    @property
    def missingDataValue(self):
        """ Returns the value to indicate missing data.
        """
        value =  getMissingDataValue(self._array)
        fieldNames = self._array.dtype.names

        # If the missing value attibute is a list with the same length as the number of fields,
        # return the missing value for field that equals the self.nodeName.
        if hasattr(value, '__len__') and len(value) == len(fieldNames):
            idx = fieldNames.index(self.nodeName)
            return value[idx]
        else:
            return value
    
    def hasChildren(self):
        """ Returns True if the variable has a structured type, otherwise returns False.
        """
        return self._isStructured
    
    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).
            Applies the index on the array that contain this field and then selects the
            current field. In pseudo-code, it returns: self.array[index][self.nodeName].
        """
        logger.debug("FieldRti.__getitem__, index={!r}".format(index))
        fieldName = self.nodeName
        slicedArray = self._array[fieldName].__getitem__(index)
        return slicedArray

    def _fetchAllChildren(self):
        """ Fetches all fields that this variable contains.
            Only variables with a structured data type can have fields.
        """
        assert self.canFetchChildren(), "canFetchChildren must be True"
        childItems = []

        # Add fields in case of an array of structured type.
        if self._isStructured:
            for fieldName in self._fieldDtype.names:
                childItem = FieldRti(self._array[self.nodeName], nodeName=fieldName,
                                     iconColor=self.iconColor, fileName=self.fileName)
                childItems.append(childItem)
        return childItems 
    
    @property
    def summary(self):
        """ Returns a summary of the contents of the RTI.  E.g. 'array 20 x 30' elements.
        """
        if self.isSliceable:
            return shapeToSummary(self.arrayShape)
        else:
            return ""
        

class ArrayRti(BaseRti):
    """ represents a numpy array (or None for undefined/unopened nodes) """
    _defaultIconGlyph = FileIconFactory.ARRAY

    def __init__(self, array, nodeName='', iconColor=ICON_COLOR_MEMORY, fileName='', attributes=None):
        """ Constructor.
            :param array: the underlying array. May be undefined (None)
            :type array: numpy.ndarray or None
        """
        super(ArrayRti, self).__init__(nodeName, iconColor, fileName)
        check_is_an_array(array, allow_none=True)
        self._array = array
        self._attributes = {} if attributes is None else attributes

    @property
    def attributes(self):
        """ The attribute dictionary.

            Reimplemented from BaseRti: the attribute dictionary is stored per-object.
        """
        return self._attributes

    @property
    def _isStructured(self):
        """ Returns True if the variable has a structured type, otherwise returns False.
        """
        return self._array is not None and bool(self._array.dtype.names)
    
    @property
    def isSliceable(self):
        """ returns True if the underlying array is not None """
        return self._array is not None
    
    @property
    def nDims(self):
        """ The number of dimensions of the underlying array
        """
        # Will only be called if self.isSliceable is True, so self._array will not be None
        return self._array.ndim

    @property
    def arrayShape(self):
        """ returns the shape of the underlying array """
        # Will only be called if self.isSliceable is True, so self._array will not be None
        return self._array.shape

    @property
    def dimensionality(self):
        """ string that describes if the RTI is an array, scalar, field, etc """
        return "array" if self._array is not None else ""
    
    @property
    def elementTypeName(self):
        """ string representation of the element type """
        if self._array is None:
            return super(ArrayRti, self).elementTypeName
        else:
            return '<structured>' if self._isStructured else str(self._array.dtype)

    @property
    def missingDataValue(self):
        """ returns the value to indicate missing data """
        return getMissingDataValue(self._array)
    
    @property
    def summary(self):
        """ returns a summary of the contents of the RTI.  E.g. 'array 20 x 30' elements """
        if self.isSliceable:
            return shapeToSummary(self.arrayShape)
        else:
            return ""
    
    def hasChildren(self):
        """ Returns True if the variable has a structured type, otherwise returns False.
        """
        return self._isStructured
    
    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).
            Passes the index through to the underlying array.
        """
        # Will only be called if self.isSliceable is True, so self._array will not be None
        return self._array.__getitem__(index)
    
    def _fetchAllChildren(self):
        """ Fetches all fields that this variable contains.
            Only variables with a structured data type can have fields.
        """
        assert self.canFetchChildren(), "canFetchChildren must be True"

        childItems = []

        # Add fields in case of an array of structured type.
        if self._isStructured:
            for fieldName in self._array.dtype.names:
                childItem = FieldRti(self._array, nodeName=fieldName, iconColor=self.iconColor,
                                     fileName=self.fileName)
                childItems.append(childItem)
        return childItems
    

class SliceRti(ArrayRti):
    """ Represents a slice of a numpy array (even before it's further sliced in the collector)

        Inherits from ArrayRti and changes little. It overrides only the icon to indicate that the
        underlying data is the same as its parent.
    """
    # Use ARRAY icon here, the FIELD icon should be used when the number of dimension is equal
    # to the array to which the field belongs. A slice decreases the number of dimensions.
    _defaultIconGlyph = FileIconFactory.ARRAY
    #_defaultIconGlyph = RtiIconFactory.FIELD


class SequenceRti(BaseRti):
    """ Represents a sequence (e.g. a list or a tuple).

        A sequence is always one-dimensional.
    """
    _defaultIconGlyph = FileIconFactory.SEQUENCE

    def __init__(self, sequence, nodeName='', iconColor=ICON_COLOR_MEMORY, fileName='', attributes=None):
        """ Constructor.
            :param sequence: the underlying sequence. May be undefined (None)
            :type array: None or a Python sequence (e.g. list or tuple)
        """
        super(SequenceRti, self).__init__(nodeName, iconColor, fileName)
        check_is_a_sequence(sequence, allow_none=True)
        self._sequence = sequence
        #self._array = NOT_SPECIFIED # To cache the sequence converted to a numpy array.
        self._attributes = {} if attributes is None else attributes

    @property
    def attributes(self):
        """ The attribute dictionary.
            Reimplemented from BaseRti: the attribute dictionary is stored per-object.
        """
        return self._attributes

    @property
    def dimensionality(self):
        """ String that describes if the RTI is an array, scalar, field, etc.
        """
        return typeName(self._sequence)

    @property
    def typeName(self):
        return typeName(self._sequence)

    @property
    def summary(self):
        """ Returns a summary of the contents of the RTI.  E.g. 'array 20 x 30' elements.
        """
        if self._sequence is None:
            return ""
        else:
            return lengthToSummary(len(self._sequence))

    def quickLook(self, width: int):
        """ Returns a string representation fof the RTI to use in the Quik Look pane.

            We print all data, even if it is large, since it is already in memory, and it is
            assumed to be quick.
        """
        if self._sequence is None:
            return ""
        else:
            return pformat(self._sequence, width)

    def _fetchAllChildren(self):
        """ Adds a child item for each column
        """
        childItems = []
        for nr, elem in enumerate(self._sequence):
            childItem = _createFromObject(elem, nodeName="elem-{}".format(nr),
                                          iconColor=self.iconColor, fileName=self.fileName)
            childItems.append(childItem)
        return childItems
    

class MappingRti(BaseRti):
    """ represents a mapping (e.g. a dictionary) """
    _defaultIconGlyph = FileIconFactory.FOLDER

    def __init__(self, dictionary,
                 nodeName='', iconColor=ICON_COLOR_MEMORY, fileName='', attributes=None):
        """ Constructor.
            The dictionary may be None for under(or None for undefined/unopened nodes)
        """
        super(MappingRti, self).__init__(nodeName=nodeName, iconColor=iconColor, fileName=fileName)
        check_is_a_mapping(dictionary, allow_none=True)
        self._dictionary = dictionary
        self._attributes = {} if attributes is None else attributes

    @property
    def attributes(self):
        """ The attribute dictionary.
            Reimplemented from BaseRti: the attribute dictionary is stored per-object.
        """
        return self._attributes

    @property
    def dimensionality(self):
        """ String that describes if the RTI is an array, scalar, field, etc.
        """
        return ""  # Return empty string to be in line with directories, groups, etc

    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        if self._dictionary is None:
            return super(MappingRti, self).elementTypeName
        else:
            return '' # A dictionary has no single element type
            #return type_name(self._dictionary)

    @property
    def summary(self):
        """ Returns a summary of the contents of the RTI.  E.g. 'array 20 x 30' elements.
        """
        return ""  # Don't show length info, so it has the same behaviour as directory and groups.
        # if self._dictionary is None:
        #     return ""
        # else:
        #     return lengthToSummary(len(self._dictionary))

    def _fetchAllChildren(self):
        """ Adds a child item for each item
        """
        childItems = []
        logger.debug("_fetchAllChildren of {!r} ({}):  {!r}"
                     .format(self, self.iconColor, self.fileName))

        if self.hasChildren():
            for key, value in sorted(self._dictionary.items()):
                childItem = _createFromObject(value, nodeName=str(key), iconColor=self.iconColor,
                                              fileName=self.fileName)
                childItems.append(childItem)
        return childItems
    

class IMArrayRti(ArrayRti): # IM: InterMediate
    """ calls a function that yields a Numpy array when the RTI is opened """
    
    def __init__(self, nodeName='', fun=None):
        """ Constructor. Initializes as an ArrayRTI with None as underlying array.
        """
        super(IMArrayRti, self).__init__(nodeName, ICON_COLOR_MEMORY)
        assert callable(fun), "fun parameter should be callable."
        self._fun = fun

    def hasChildren(self):
        """ Returns True if the item has (fetched or unfetched) children
            Returns True so that the function can be called, even though the array has no children.
        """
        return True
    
    def _openResources(self):
        """ evaluates the function to result an array """
        arr = self._fun()
        check_is_an_array(arr)
        self._array = arr

    def _closeResources(self):
        self._array = None
