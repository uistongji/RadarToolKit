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


from .abstractcti import AbstractCtiEditor, AbstractCti
from ..utils import NOT_SPECIFIED
from ..utils import setWidgetSizePolicy
from ...bindings import QtCore, QtWidgets, QtSlot, Qt
from ...utils.check_class import check_class
import logging, copy


logger = logging.getLogger(__name__)



class ChoiceCti(AbstractCti):
    """ Config Tree Item to store a choice between strings.

        A QCombobox will pop-up if the user clicks on the cell to edit it.
    """
    def __init__(self, nodeName, defaultData=0, configValues=None, displayValues=None,
                 editable=False, insertPolicy=QtWidgets.QComboBox.InsertAtBottom,
                 completer=NOT_SPECIFIED):
        """ Constructor.

            The defaultData is an integers that is used to store the currentIndex.
            The displayValues parameter must be a list of strings, which will be displayed in the
            combo box. The configValues should be a list of the same size with the configValues
            that each 'choice' represents, e.g. choice 'dashed' maps to configValue Qt.DashLine.
            If displayValues is None, the configValues are used as displayValues.

            The defaultData can be set to a negative value, e.g. use -1 to select the last item
            by default. However, it will be converted to a positive value in the constructor.

            :param defaultData: the default index in the combobox that is used for editing
            :param configValues: list of configValue items to populate the combobox with
            :param displayValues: list of possible displayValue items.
                If None the config values are used as display values as well.
            :param editable: if True the combobox will be editable
            :param insertPolicy: determines where user-inserted items should appear in the combobox
                must be of type QtWidgets.QComboBox.InsertPolicy
            :param completer: a QCompleter that will be used by the combobox for auto-completion.
                If NotSpecified a default completer is used, i.e. case-insensitive auto-completion.
                Use None, 0 or False to disable auto-completion.

            For the  parameters see the AbstractCti constructor documentation.
        """

        check_class(insertPolicy, QtWidgets.QComboBox.InsertPolicy)
        if completer: # completer may be False
            check_class(completer, QtWidgets.QCompleter)

        self.editable = editable
        self.insertPolicy = insertPolicy
        self.completer = completer

        self._configValues = [] if configValues is None else configValues
        if displayValues is None:
            self._displayValues = copy.copy(self._configValues)
        else:
            assert not editable, "No separate displayValues may be set if the CTI is editable"
            self._displayValues = displayValues

        assert len(self._configValues) == len(self._displayValues),\
            "If set, configValues must have the same length as displayValues."

        self._defaultConfigValues = copy.copy(self._configValues)

        # Set after self._displayValues are defined. The parent constructor call _enforceDataType
        super(ChoiceCti, self).__init__(nodeName, defaultData)


    def _enforceDataType(self, data):
        """ Converts to int so that this CTI always stores that type.

            The data be set to a negative value, e.g. use -1 to select the last item
            by default. However, it will be converted to a positive by this method.
        """
        idx = int(data)
        if idx < 0:
            idx += len(self._displayValues)
        assert 0 <= idx < len(self._displayValues), \
            "Index should be >= 0 and < {}. Got {}".format(len(self._displayValues), idx)
        return idx


    @property
    def configValue(self):
        """ The currently selected configValue
        """
        return self._configValues[self.data]


    @property
    def iterConfigValues(self):
        """ Returns a generator expression to iterate over al config values
        """
        return (value for value in self._configValues)


    @property
    def iterDisplayValues(self):
        """ Returns a generator expression to iterate over al display values
        """
        return (value for value in self._displayValues)


    def _dataToString(self, data):
        """ Conversion function used to convert the (default)data to the display value.
        """
        choices = self._displayValues
        return str(choices[data])


    def _nodeMarshall(self):
        """ Returns the non-recursive marshalled value of this CTI. Is called by marshall()
        """
        if self.editable:
            return [self.data, self._configValues]
        else:
            return self.data


    def _nodeUnmarshall(self, data):
        """ Initializes itself non-recursively from data. Is called by unmarshall()
        """
        if self.editable:
            curIdx, configValues = data
            self._configValues = configValues
            self._displayValues = configValues
            self.data = curIdx
        else:
            self.data = data


    @property
    def debugInfo(self):
        """ Returns the string with debugging information
        """
        return repr(self._displayValues)


    def createEditor(self, delegate, parent, option):
        """ Creates a ChoiceCtiEditor.
            For the parameters see the AbstractCti constructor documentation.
        """
        return ChoiceCtiEditor(self, delegate, parent=parent)


    def insertValue(self, pos, configValue, displayValue=None):
        """ Will insert the configValue in the configValues and the displayValue in the
            displayValues list.
            If displayValue is None, the configValue is set in the displayValues as well
        """
        self._configValues.insert(pos, configValue)
        self._displayValues.insert(pos, displayValue if displayValue is not None else configValue)


    def removeValue(self, configValue):
        """ Will remove the configValue and the corresponding displayValue from the lists.
        """
        self.removeValueByIndex(self._configValues.index(configValue))


    def removeValueByIndex(self, index):
        """ Will remove the configValue and the corresponding displayValue given the index.
        """
        del self._configValues[index]
        del self._displayValues[index]


class ChoiceCtiEditor(AbstractCtiEditor):
    """ A CtiEditor which contains a QCombobox for editing ChoiceCti objects.
    """
    def __init__(self, cti, delegate, parent=None):
        """ See the AbstractCtiEditor for more info on the parameters
        """
        super(ChoiceCtiEditor, self).__init__(cti, delegate, parent=parent)

        comboBox = QtWidgets.QComboBox()
        comboBox.setEditable(cti.editable)
        comboBox.setInsertPolicy(cti.insertPolicy)
        setWidgetSizePolicy(comboBox, QtWidgets.QSizePolicy.Expanding, None)

        if cti.completer is not NOT_SPECIFIED:
            comboBox.setCompleter(cti.completer if cti.completer else None)

        comboBox.addItems(cti._displayValues)

        # Store the configValue in the combo box, although it's not currently used.
        for idx, configValue in enumerate(cti._configValues):
            comboBox.setItemData(idx, configValue, role=Qt.UserRole)

        comboBox.activated.connect(self.comboBoxActivated)
        comboBox.model().rowsInserted.connect(self.comboBoxRowsInserted)
        self.comboBox = self.addSubEditor(comboBox, isFocusProxy=True)

        # Install an eventFilter on the QListView that pops-up and contains all the items.
        # This allows the user to remove items by pressing the delete key in the list.
        self._comboboxListView = comboBox.view()
        self._comboboxListView.installEventFilter(self)


    def finalize(self):
        """ Is called when the editor is closed. Disconnect signals.
        """
        self._comboboxListView.removeEventFilter(self)
        self.comboBox.model().rowsInserted.disconnect(self.comboBoxRowsInserted)
        self.comboBox.activated.disconnect(self.comboBoxActivated)
        super(ChoiceCtiEditor, self).finalize()


    def setData(self, data):
        """ Provides the main editor widget with a data to manipulate.
        """
        self.comboBox.setCurrentIndex(data)


    def getData(self):
        """ Gets data from the editor widget.
        """
        return self.comboBox.currentIndex()


    @QtSlot(int)
    def comboBoxActivated(self, index):
        """ Is called when the user chooses an item in the combo box. The item's index is passed.
            Note that this signal is sent even when the choice is not changed.
        """
        self.delegate.commitData.emit(self)


    @QtSlot(QtCore.QModelIndex, int, int)
    def comboBoxRowsInserted(self, _parent, start, end):
        """ Called when the user has entered a new value in the combobox.
            Puts the combobox values back into the cti.
        """
        assert start == end, "Bug, please report: more than one row inserted"
        configValue = self.comboBox.itemText(start)
        logger.debug("Inserting {!r} at position {} in {}"
                     .format(configValue, start, self.cti.nodePath))
        self.cti.insertValue(start, configValue)


    def eventFilter(self, watchedObject, event):
        """ Deletes an item from an editable combobox when the delete or backspace key is pressed
            in the list of items, or when ctrl-delete or ctrl-back space is pressed in the
            line-edit.

            When the combobox is not editable the filter does nothing.
        """
        if self.comboBox.isEditable() and event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if key in (Qt.Key_Delete, Qt.Key_Backspace):
                if (watchedObject == self._comboboxListView
                    or (watchedObject == self.comboBox
                        and event.modifiers() == Qt.ControlModifier)):

                    index = self._comboboxListView.currentIndex()
                    if index.isValid():
                        row = index.row()
                        logger.debug("Removing item {} from the combobox: {}"
                                     .format(row, self._comboboxListView.model().data(index)))
                        self.cti.removeValueByIndex(row)
                        self.comboBox.removeItem(row)
                        return True

        # Calling parent event filter, which may filter out other events.
        return super(ChoiceCtiEditor, self).eventFilter(watchedObject, event)

