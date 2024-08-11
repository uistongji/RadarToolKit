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


from .abstractcti import AbstractCti, AbstractCtiEditor
from ...bindings import QtWidgets, Qt
import logging

logger = logging.getLogger(__name__)


class UntypedCti(AbstractCti):
    """ Config Tree Item to store a any type of data as long as it can be edited with a QLineEdit.

        Typically it's better to use 'typed' CTIs, where the data is always internally stored in
        the same type (enforced by _enforceDataType).

        This item is non-editable and can, for instance, be used for introspection.
    """
    def __init__(self, nodeName, defaultData='', doc=''):
        """ Constructor. For the parameters see the AbstractCti constructor documentation.
        """
        super(UntypedCti, self).__init__(nodeName, defaultData)
        self.doc = doc

    def _enforceDataType(self, value):
        """ Since UntypedCti can store any type of data no conversion will be done.
        """
        return value

    def createEditor(self, delegate, parent, option):
        """ Creates an UntypedCtiEditor.
            For the parameters see the AbstractCti constructor documentation.
            Note: since the item is not editable this will never be called.
        """
        return UntypedCtiEditor(self, delegate, parent=parent)

    @property
    def valueColumnItemFlags(self):
        """ Returns the flags determine how the user can interact with the value column.
            Returns Qt.NoItemFlags so that the item is not editable
        """
        return Qt.NoItemFlags


class UntypedCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a QLineEdit for editing UntypedCti objects.

        Only
    """
    def __init__(self, cti, delegate, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters
        """
        super(UntypedCtiEditor, self).__init__(cti, delegate, parent=parent)
        self.lineEditor = self.addSubEditor(QtWidgets.QLineEdit(), isFocusProxy=True)

    def setData(self, data):
        """ Provides the main editor widget with a data to manipulate.
        """
        self.lineEditor.setText(str(data))

    def getData(self):
        """ Gets data from the editor widget.
        """
        return self.lineEditor.text()


