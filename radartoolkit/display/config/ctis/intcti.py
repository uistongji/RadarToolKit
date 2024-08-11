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


from ..ctis.abstractcti import AbstractCti, AbstractCtiEditor
from ..utils import setWidgetSizePolicy
from ...bindings import QtWidgets, QtSlot
import logging
import numpy as np

logger = logging.getLogger(__name__)


class IntCti(AbstractCti):
    """ Config Tree Item to store an integer. It can be edited using a QSpinBox.
    """
    def __init__(self, nodeName, defaultData=0,
                 minValue = None, maxValue = None, stepSize = 1,
                 prefix='', suffix='', specialValueText=None):
        """ Constructor.

            :param minValue: minimum data allowed when editing (use None for no minimum)
            :param maxValue: maximum data allowed when editing (use None for no maximum)
            :param stepSize: steps between values when editing (default = 1)
            :param prefix: prepended to the start of the displayed value in the spinbox
            :param suffix: prepended to the end of the displayed value in the spinbox
            :param specialValueText: if set, this text will be displayed when the the minValue
                is selected. It is up to the cti user to interpret this as a special case.

            For the (other) parameters see the AbstractCti constructor documentation.
        """
        super(IntCti, self).__init__(nodeName, defaultData)

        self.minValue = minValue
        self.maxValue = maxValue
        self.stepSize = stepSize
        self.prefix = prefix
        self.suffix = suffix
        self.specialValueText = specialValueText


    def _enforceDataType(self, data):
        """ Converts to int so that this CTI always stores that type.
        """
        return int(data)


    def _dataToString(self, data):
        """ Conversion function used to convert the (default)data to the display value.
        """
        if self.specialValueText is not None and data == self.minValue:
            return self.specialValueText
        else:
            return "{}{}{}".format(self.prefix, data, self.suffix)


    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return ("enabled = {}, min = {}, max = {}, step = {}, specVal = {}"
                .format(self.enabled, self.minValue, self.maxValue, self.stepSize, self.specialValueText))


    def createEditor(self, delegate, parent, option):
        """ Creates a IntCtiEditor.
            For the parameters see the AbstractCti constructor documentation.
        """
        return IntCtiEditor(self, delegate, parent=parent)



class IntCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a QSpinbox for editing IntCti objects.
    """
    def __init__(self, cti, delegate, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters
        """
        super(IntCtiEditor, self).__init__(cti, delegate, parent=parent)

        spinBox = QtWidgets.QSpinBox(parent)
        spinBox.setKeyboardTracking(False)
        setWidgetSizePolicy(spinBox, QtWidgets.QSizePolicy.Expanding, None)

        if cti.minValue is None:
            spinBox.setMinimum(np.iinfo('i').min)
        else:
            spinBox.setMinimum(cti.minValue)

        if cti.maxValue is None:
            spinBox.setMaximum(np.iinfo('i').max)
        else:
            spinBox.setMaximum(cti.maxValue)

        spinBox.setSingleStep(cti.stepSize)
        spinBox.setPrefix(cti.prefix)
        spinBox.setSuffix(cti.suffix)

        if cti.specialValueText is not None:
            spinBox.setSpecialValueText(cti.specialValueText)

        self.spinBox = self.addSubEditor(spinBox, isFocusProxy=True)
        self.spinBox.valueChanged.connect(self.commitChangedValue)


    def finalize(self):
        """ Called at clean up. Is used to disconnect signals.
        """
        self.spinBox.valueChanged.disconnect(self.commitChangedValue)
        super(IntCtiEditor, self).finalize()


    @QtSlot(int)
    def commitChangedValue(self, value):
        """ Commits the new value to the delegate so the inspector can be updated
        """
        #logger.debug("Value changed: {}".format(value))
        self.delegate.commitData.emit(self)


    def setData(self, data):
        """ Provides the main editor widget with a data to manipulate.
        """
        self.spinBox.setValue(data)


    def getData(self):
        """ Gets data from the editor widget.
        """
        return self.spinBox.value()

