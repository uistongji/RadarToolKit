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


""" Functions dealing with type check and classes import.
"""

from . import six
import logging, numbers, re
import numpy as np
import numpy.ma as ma
from typing import Any, Dict, Type, Optional

logger = logging.getLogger(__name__)

KIND_LABEL = dict(
    b = 'boolean',
    i = 'signed integer',
    u = 'unsigned integer',
    f = 'floating-point',
    c = 'complex floating-point',
    m = 'timedelta',
    M = 'datetime',
    O = 'object',
    S = 'byte/string',
    U = 'unicode',
    V = 'compound', # is more clear to end users than 'void'
)

DEFAULT_NUM_FORMAT = '{!r}' if six.PY2 else '{}'

def is_a_sequence(var, allow_none=False):
    """ Returns True if var is a list or a tuple (but not a string!)
    """
    return isinstance(var, (list, tuple)) or (var is None and allow_none)


def is_an_array(var, allow_none=False):
    """ Returns True if var is a numpy array.
    """
    return isinstance(var, np.ndarray) or (var is None and allow_none)


def check_class(obj, target_class, allow_none = False):
    """ Checks that the  obj is a (sub)type of target_class.
        Raises a TypeError if this is not the case.

        :param obj: object whos type is to be checked
        :type obj: any type
        :param target_class: target type/class
        :type target_class: any class or type
        :param allow_none: if true obj may be None
        :type allow_none: boolean
    """
    if not isinstance(obj, target_class):
        if not (allow_none and obj is None):
            raise TypeError("obj must be a of type {}, got: {}"
                            .format(target_class, type(obj)))


def check_is_an_array(var, allow_none=False):
    """ Calls is_an_array and raises a type error if the check fails.
    """
    if not is_an_array(var, allow_none=allow_none):
        raise TypeError("var must be a NumPy array, however type(var) is {}"
                        .format(type(var)))




def array_is_structured(array):
    """ Returns True if the array has a structured data type.
    """
    return bool(array.dtype.names)


def array_has_real_numbers(array):
    """ Uses the dtype kind of the numpy array to determine if it represents real numbers.

        That is, the array kind should be one of: i u f

        Possible dtype.kind values.

    """
    kind = array.dtype.kind
    return kind in 'iuf'


def to_string(var, masked=None, decode_bytes='utf-8', maskFormat='', strFormat='{}',
              intFormat='{}', numFormat=DEFAULT_NUM_FORMAT, noneFormat='{!r}', otherFormat='{}'):
    """ Converts var to a python string or unicode string so Qt widgets can display them.

        If var consists of bytes, the decode_bytes is used to decode the bytes.

        If var consists of a numpy.str_, the result will be converted to a regular Python string.
        This is necessary to display the string in Qt widgets.

        For the possible format string (replacement fields) see:
            https://docs.python.org/3/library/string.html#format-string-syntax

        :param masked: if True, the element is masked. The maskFormat is used.
        :param decode_bytes': string containing the expected encoding when var is of type bytes
        :param strFormat' : new style format string used to format strings
        :param intFormat' : new style format string used to format integers
        :param numFormat' : new style format string used to format all numbers except integers.
        :param noneFormat': new style format string used to format Nones.
        :param maskFormat': override with this format used if masked is True.
            If the maskFormat is empty, the format is never overriden.
        :param otherFormat': new style format string used to format all other types
    """
    #logger.debug("to_string: {!r} ({})".format(var, type(var)))

    # Decode and select correct format specifier.
    if is_binary(var):
        fmt = strFormat
        try:
            decodedVar = var.decode(decode_bytes, 'replace')
        except LookupError as ex:
            # Add URL to exception message.
            raise LookupError("{}\n\nFor a list of encodings in Python see: {}"
                              .format(ex, "pass"))
    elif is_text(var):
        fmt = strFormat
        decodedVar = six.text_type(var)
    elif is_a_string(var):
        fmt = strFormat
        decodedVar = str(var)
    elif isinstance(var, numbers.Integral):
        fmt = intFormat
        decodedVar = var
    elif isinstance(var, numbers.Number):
        fmt = numFormat
        decodedVar = var
    elif var is None:
        fmt = noneFormat
        decodedVar = var
    else:
        fmt = otherFormat
        decodedVar = var

    if maskFormat != '{}':
        try:
            allMasked = all(masked)
        except TypeError as ex:
            allMasked = bool(masked)

        if allMasked:
            fmt = maskFormat

    try:
        result = fmt.format(decodedVar)
    except Exception:
        result = "Invalid format {!r} for: {!r}".format(fmt, decodedVar)

    #if masked:
    #    logger.debug("to_string (fmt={}): {!r} ({}) -> result = {!r}".format(maskFormat, var, type(var), result))

    return result


def is_binary(var, allow_none=False):
    """ Returns True if var is a binary (bytes) objects

        Result             py-2  py-3
        -----------------  ----- -----
        b'bytes literal'   True  True
         'string literal'  True  False
        u'unicode literal' False False

        Also works with the corresponding numpy types.
    """
    return isinstance(var, six.binary_type) or (var is None and allow_none)


def is_text(var, allow_none=False):
    """ Returns True if var is a unicode text

        Result             py-2  py-3
        -----------------  ----- -----
        b'bytes literal'   False False
         'string literal'  False True
        u'unicode literal' True  True

        Also works with the corresponding numpy types.
    """
    return isinstance(var, six.text_type) or (var is None and allow_none)



def is_a_string(var, allow_none=False):
    """ Returns True if var is a string (ascii or unicode)

        Result             py-2  py-3
        -----------------  ----- -----
        b'bytes literal'   True  False
         'string literal'  True  True
        u'unicode literal' True  True

        Also returns True if the var is a numpy string (numpy.string_, numpy.unicode_).
    """
    return isinstance(var, six.string_types) or (var is None and allow_none)


def array_kind_label(array):
    """ Returns short string describing the array data type kind
    """
    return KIND_LABEL[array.dtype.kind]


def check_is_a_string(var, allow_none=False):
    """ Calls is_a_string and raises a type error if the check fails.
    """
    if not is_a_string(var, allow_none=allow_none):
        raise TypeError("var must be a string, however type(var) is {}"
                        .format(type(var)))



COLOR_REGEXP = re.compile('^#[0-9A-Fa-f]{6}$')  # Hex color string representation

def is_a_color_str(colorStr, allow_none=False):
    """ Returns True if colorStr is a string starting with '#' folowed by 6 hexadecimal digits.
    """
    if not is_a_string(colorStr, allow_none=allow_none):
        return False

    return COLOR_REGEXP.match(colorStr)


def check_is_a_sequence(var, allow_none=False):
    """ Calls is_a_sequence and raises a type error if the check fails.
    """
    if not is_a_sequence(var, allow_none=allow_none):
        raise TypeError("var must be a list or tuple, however type(var) is {}"
                        .format(type(var)))



def is_a_mapping(var, allow_none=False):
    """ Returns True if var is a dictionary
    """
    return isinstance(var, dict) or (var is None and allow_none)



def check_is_a_mapping(var, allow_none=False):
    """ Calls is_a_mapping and raises a type error if the check fails.
    """
    if not is_a_mapping(var, allow_none=allow_none):
        raise TypeError("var must be a dict, however type(var) is {}"
                        .format(type(var)))

def is_a_bxds(var):
    pass

def is_a_xds(var):
    pass

def is_a_ct(var):
    pass


#############
# Type info #
#############

def typeName(var: Any) -> str:
    """ Returns the name of the type of var.
    """
    return type(var).__name__