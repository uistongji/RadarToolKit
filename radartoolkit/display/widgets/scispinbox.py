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


from ..bindings import QtGui, QtWidgets

import logging, re
import numpy as np

logger = logging.getLogger(__name__)

REGEXP_FLOAT = re.compile(r'(([+-]?\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)')


def ValidFloatString(string):
    match = REGEXP_FLOAT.search(string)
    return match.groups()[0] == string if match else False



class FloatValidator(QtGui.QValidator):

    def validate(self, string, position):
        if ValidFloatString(string):
            return (QtGui.QValidator.Acceptable, string, position)
        
        if string == "" or string[position-1] in 'e.-+':
            return (QtGui.QValidator.Intermediate, string, position)
        return (QtGui.QValidator.Invalid, string, position)
    
    def fixup(self, text):
        match = REGEXP_FLOAT.search(text)
        return match.groups()[0] if match else ""



class ScientificDoubleSpinBox(QtWidgets.QDoubleSpinBox):

    def __init__(self,
                 precision=6,
                 largeStepFactor=10,
                 smallStepsPerLargeStep=10,
                 *args, **kwargs):
        """ Constructor.

            In contrast to the QDoubleSpinbox the (page)up/down let the value grow exponentially.
            That is, the spinbox value is multiplied by a small step factor when the up-arrow is
            pressed, and by a larger factor if page-up is pressed. A large step multiplies the value
            spinbox value with largeStepFactor (default 10). The smallStepsPerLargeStep does then
            specify how many up-arrow key presses are needed to increase to largeStepFactor.

            :param precision: The precision used in the scientific notation.
            :param largeStepFactor: default 10
            :param smallStepsPerLargeStep: default 10
        """

        self.precision = precision
        super(ScientificDoubleSpinBox, self).__init__(*args, **kwargs)
        self.setMinimum(np.finfo('d').min)
        self.setMaximum(np.finfo('d').max)
        self.validator = FloatValidator()
        self.setDecimals(323)

        self._smallStepFactor = None
        self._smallStepsPerLargeStep = None
        self._largeStepFactor = largeStepFactor
        self.smallStepsPerLargeStep = smallStepsPerLargeStep


    def validate(self, text, position):
        result = self.validator.validate(text, position)
        return result 

    
    def fixup(self, text):
        result = self.validator.fixup(text)
        return result

    
    def valueFromText(self, text):
        return float(text)
    

    def textFromValue(self, value):
        return "{:.{precission}g}".format(value, precission=self.precision)


    @property
    def largeStepFactor(self):
        """ The spinbox will be multiplied with this factor whenever page up is pressed.
        """

        return self._largeStepFactor


    @largeStepFactor.setter
    def largeStepFactor(self, largeStepFactor):
        """ The spinbox will be multiplied with this factor whenever page up is pressed.
        """

        self._largeStepFactor = largeStepFactor


    @property
    def smallStepFactor(self):
        """ The spinbox will be multiplied with this factor whenever page up is pressed.
            Read-only property. Setting is done via largeStepFactor and smallStepsPerLargeStep.
        """

        return self._smallStepFactor  


    @property
    def smallStepsPerLargeStep(self):
        """ The number of small steps that go in a large one.

            The spinbox value is increased with a small step when the up-arrow is pressed, and by
            a large step if page-up is pressed. A large step increases the value increases the
            spinbox value with largeStepFactor (default 10). The smallStepsPerLargeStep does then
            specify how many up-arrow key presses are needed to increase to largeStepFactor.
        """

        return self._smallStepsPerLargeStep


    @smallStepsPerLargeStep.setter
    def smallStepsPerLargeStep(self, smallStepsPerLargeStep):
        """ Sets the number of small steps that go in a large one.

        """

        self._smallStepsPerLargeStep = smallStepsPerLargeStep
        self._smallStepFactor = np.power(self.largeStepFactor, 1.0 / smallStepsPerLargeStep)



    def stepBy(self, steps):
        """ Function that is called whenever the user triggers a step. The steps parameter
            indicates how many steps were taken, e.g. Pressing Qt::Key_Down will trigger a call to
            stepBy(-1), whereas pressing Qt::Key_Prior will trigger a call to stepBy(10).
        """

        oldValue = self.value()

        if oldValue == 0:
            newValue = steps
        elif steps == 1:
            newValue = self.value() * self.smallStepFactor
        elif steps == -1:
            newValue = self.value() / self.smallStepFactor
        elif steps == 10:
            newValue = self.value() * self.largeStepFactor
        elif steps == -10:
            newValue = self.value() / self.largeStepFactor
        else:
            raise ValueError("Invalid step size: {!r}, value={}".format(steps, oldValue))

        newValue = float(newValue)

        if newValue < self.minimum():
            newValue = self.minimum()

        if newValue > self.maximum():
            newValue = self.maximum()

        try:
            self.setValue(newValue)
        except Exception:
            logger.warning("Unable to set spinbox to: {!r}".format(newValue))
            self.setValue(oldValue)
