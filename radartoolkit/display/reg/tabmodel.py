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


from ..bindings import QtCore, QtGui, Qt, QtWidgets
from ..settings import ICONS_DIR, DEFAULT_COLORS
from ..config.utils import type_name
from ..utils.check_class import check_class

import logging, os
import pyqtgraph as pg


logger = logging.getLogger(__name__)
curFileName = os.path.basename(__file__)



class BaseItem(object):
    """ An object that is stored in the BaseItemStore.

        It always must have a name, which is used as the identifier
        :: Fileds: The fields that this item contains.
        :: Labels: Readable label for each field, will be overriden.
        :: Stretch: True -> The corresponding table column can stretch.
        :: Decoration:  column number containing the decoration with icon or not.
    """

    FIELDS = []
    LABELS = []
    STRETCH = []

    COL_DECORATION = None
    _sequenceCounter =0

    def __init__(self, **kwargs):

        self._data = {}

        for key, value in kwargs.items():
            if key not in self.FIELDS:
                raise ValueError("Key '{}' not in field names: {}".format(key, self.FIELDS))
            self._data[key] = value
        
        for key in self.FIELDS:
            if key not in self._data:
                if key == 'debugCount':
                    self._data['debugCount'] = BaseItem._sequenceCounter
                    BaseItem._sequenceCounter += 1
                else:
                    self._data[key] = ''
        
        assert len(self.FIELDS) > 0
        if len(self.LABELS) != len(self.FIELDS):
            raise AssertionError("Number of labels ({}) is not equal to number of fields ({})"
                                 .format(len(self.LABELS), len(self.FIELDS)))

        if len(self.STRETCH) != len(self.FIELDS):
            raise AssertionError("Number of stretches ({}) is not equal to number of labels ({})"
                                 .format(len(self.STRETCH), len(self.FIELDS)))  


    def __repr__(self):
        return "<{}: {}>".format(type_name(self), self._data)
    

    @property
    def data(self):
        """ Returns the data dictionary.
        """

        return self._data


    @property
    def decoration(self):
        """ A optional icon that is displayed in the COL_DECORATION column.

            The base implementation returns None (no icon). Descendants can override this
        """

        return None


    """ The following functions [load | save] the state to JSON config files.
    """
    def marshall(self):    
        """ Returns a dictionary to save in the persistent settings.
        """

        cfg = {}
        for field in self.FIELDS:
            cfg[field] = str(self._data[field]) 
        return cfg

    
    def unmarshall(self, cfg):
        """ initializes itself from a config dict form the persistent settings """

        self._fields = {}
        for field in self.FIELDS:
            if field in cfg:
                self._data[field] = cfg[field]
            else:
                logger.warning("Field '{}' not in config: {}".format(field, cfg))



class BaseItemStore(object):
    """ Class that stores a collection of BaseItems or descendants. Base class for the registries.

        In principle this class could be merged with the BaseItemModel but I chose to separate them
        because most of the time the data is used read-only, from the store. Only when the user
        edits the registry from the GUI is a table model needed. This way registries don't descent
        from QAbstractTableModel and inherit a huge number of methods.

        The BaseItemStore can only store items of one type (ITEM_CLASS). Descendants will
        store their own type. For instance the InspectorRegistry will store InspectorstoreItem
    """

    ITEM_CLASS = BaseItem

    def __init__(self):
        self._items = []
    

    def __str__(self):
        return "Item Store"
    

    @property
    def fieldNames(self):
        """ Name of the fields. So think twice before changing them."""

        return self.ITEM_CLASS.FIELDS


    @property
    def fieldLabels(self):
        """ Short, human readable, label fields for use in GUI. """

        return self.ITEM_CLASS.LABELS


    @property
    def canStretchPerColumn(self):
        """ List of booleans, for each column indicating if it can strech.
            True -> the corresponding table column can stretch. False -> resize to contents.
        """

        return self.ITEM_CLASS.STRETCH


    @property
    def items(self):
        """ The registered class items. """

        return self._items


    def clear(self):
        """ Empties the registry
        """

        self._items = []


    def marshall(self):
        return [item.marshall() for item in self.items]
    

    def unmarshall(self, cfg):
        self.clear()
        if not cfg:
            logger.info("Empty config, using registry defaults for: {}".format(self))
            for storeItem in self.getDefaultItems():
                self._items.append(storeItem)
        else:
            for dct in cfg:
                logger.debug("Creating {} from: {}".format(self.ITEM_CLASS, dct))
                storeItem = self.ITEM_CLASS()
                storeItem.unmarshall(dct)
                self._items.append(storeItem)
        

    def getDefaultItems(self):
        """ Returns a list with the default items.
            This is used initialize the application plugins when there are no saved settings,
            for instance the first time the application is started.
            The base implementation returns an empty list but other registries should override it.
        """

        return []



class BaseTableModel(QtCore.QAbstractTableModel):
    sigItemChanged = QtCore.Signal(BaseItem)

    def __init__(self, store, parent=None):
        """ Constructor.

            :param store: Underlying data store, must descent from BaseItemStore
            :param parent: Parent widget
        """

        super(BaseTableModel, self).__init__(parent)
        self._store = store
        self._fieldNames = self._store.fieldNames
        self._fieldLabels = self.store.fieldLabels


    @property
    def store(self):
        """ The underlying BaseItemStore

            Note that if you modify this directly (i.e. not via the setData method), the model is
            not aware of the modifications. Therefore the user is responsible for nofifying the
            this table model after modifications.
        """

        return self._store   
    

    def rowCount(self, parent=None):
        """ Returns the number of items in the registry.
        """

        return len(self._store.items)


    def columnCount(self, parent=None):
        """ Returns the number of columns of the registry.
        """

        return len(self._fieldNames) # return len(self._fieldNames)


    def itemFromIndex(self, index, altItem=None):
        """ Gets the item given the model index
            Returns altItem (default: None) if the index is not alid
        """

        if not index.isValid():
            return altItem
        else:
            return self._store.items[index.row()]


    def indexFromItem(self, storeItem, col=0):
        """ Gets the index (with column=0) for the row that contains the storeItem
            If col is negative, it is counted from the end
        """

        if col < 0:
            col = len(self._fieldNames) - col
        try:
            row = self._store.items.index(storeItem)
        except ValueError:
            return QtCore.QModelIndex()
        else:
            return self.index(row, col)


    def flags(self, index):
        """ Returns the item flags for the given index.
        """

        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


    def headerData(self, section, orientation, role):
        """ Returns the header for a section (row or column depending on orientation).
            Reimplemented from QAbstractTableModel to make the headers start at 0.
        """

        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._fieldLabels[section] 
            else:
                return str(section)
        else:
            return None


    def data(self, index, role=QtCore.Qt.DisplayRole):
        """ Returns the data stored under the given role for the item referred to by the index.
        """

        if not index.isValid():
            return None

        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole, QtCore.Qt.ToolTipRole, QtCore.Qt.DecorationRole):
            return None

        row = index.row()
        col = index.column()
        item = self._store.items[row]
        attrName = self._fieldNames[col]

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole, QtCore.Qt.ToolTipRole):
            return str(item.data[attrName])

        elif role == QtCore.Qt.DecorationRole:
            if col == item.COL_DECORATION:
                return item.decoration
        else:
            raise ValueError("Invalid role: {}".format(role))


    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """ Sets the role data for the item at index to value.
        """

        if not index.isValid():
            return False

        if role != QtCore.Qt.EditRole:
            return False

        row = index.row()
        col = index.column()
        storeItem = self._store.items[row]
        fieldName = self._fieldNames[col]
        storeItem.data[fieldName] = value

        self.emitDataChanged(storeItem)
        return True


    def emitDataChanged(self, storeItem):
        """ Emits the dataChanged and sigItemChanged signals for the storeItem
        """

        leftIndex = self.indexFromItem(storeItem, col=0)
        rightIndex = self.indexFromItem(storeItem, col=-1)

        logger.debug("Data changed: {} ... {}".format(self.data(leftIndex), self.data(rightIndex)))
        self.dataChanged.emit(leftIndex, rightIndex)
        self.sigItemChanged.emit(storeItem)


    def createItem(self):
        """ Creates an emtpy item of type ITEM_CLASS
        """

        return self.store.ITEM_CLASS()


    def insertItem(self, item, row):
        """ Insert an item in the store at a certain row.
        """

        logger.info("Inserting {!r} at row {}".format(item, row, self))
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        try:
            self.store.items.insert(row, item)
        finally:
            self.endInsertRows()


    def popItemAtRow(self, row):
        """ Removes a store item from the store.
            Returns the item
        """

        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        try:
            item = self.store.items[row]
            del self.store.items[row]
            return item
        finally:
            self.endRemoveRows()


    def moveItem(self, fromRow, toRow):
        """ Moves the item for position
        """

        item = self.popItemAtRow(fromRow)

        # This always works, regardless if fromPos is before or after toPos
        self.insertItem(item, toRow)



class TableInfoModel(BaseTableModel):
    """ Table Information Model that holds a BaseInfoItems store. 
    """

    DISPLAY = ['nodeid', 'desc']
    STRETCH = [False, False]

    def __init__(self, items, parent=None):
        store = InfoItemStore()
        store.unmarshall(items)

        super(TableInfoModel, self).__init__(store, parent)


    def columnCount(self, parent=None):
        """ Returns the number of columns of the registry.
        """

        return len(self.DISPLAY)

    def headerData(self, section, orientation, role):
        """ Returns the header for a section (row or column depending on orientation).
            Reimplemented from QAbstractTableModel to make the headers start at 0.
        """

        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.nameToDisplay(self.DISPLAY[section])
            else:
                return str(section)
        else:
            return None
        

    def nameToDisplay(self, txt):
        # transfer the text into the display value
        displays = {'nodeid': 'Interaction Node', 'desc': 'Description'}
        return displays[txt]
    

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """ Returns the data stored under the given role for the item referred to by the index.
        """

        if not index.isValid():
            return None
        
        if role not in (QtCore.Qt.DisplayRole,
                        QtCore.Qt.EditRole, 
                        QtCore.Qt.ToolTipRole, 
                        QtCore.Qt.DecorationRole):
            return None
        
        row = index.row()
        col = index.column()
        item = self._store.items[row]
        attrName = self.DISPLAY[col]

        if role in (Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole):
            if attrName == 'nodeid':
                return str("{}".format(item._interactionNode))
            return str(item.data[attrName])
        elif role == Qt.DecorationRole:
            if col == item.COL_DECORATION:
                return item.decoration
        else:
            raise ValueError("Invalid role: {}".format(role))
        
    

class BaseInfoItem(object):
    """ Base item with `nodeid`, `datetime`, `field`, `desc`, 
                        `detailed information`, `decoration`.
        
        ::nodeid:     The ID of a node stored in the list, which is used as the identifier.
        ::timeStamp:  The time of the interaction activated either by the user or necessrarily by the app.
        ::field:      The field which it belongs to.
        ::desc:       One line of description.
        ::details:    Detailed information.
        ::decoration: Icon for this item to be displayed.
        ::styles:     Styled options.
    """

    FIELDS = ['nodeid', 'timeStamp', 'field', 'desc', 'details', 'decoration', 'styles']
    LABELS = ['Node ID', 'Time Stamp', 'Field', 'Description', 'Details', 'Decoration', 'Styles']
    STRETCH = []

    COL_DECORATION = 0 # Display Icon in the main column
    STATUS_COLORS = {'question': '#FFAA33', 
                     'success':   '#DDFF77',
                     'failure':  '#FF3333'}

    def __init__(self, dct={}):
        
        self._data = {}
        for key, value in dct.items():
            if key not in self.FIELDS:
                raise ValueError("Key '{}' not in field names: {}".format(key, self.FIELDS))
            self._data[key] = value
        
        for key in self.FIELDS:
            if key not in self._data:
                if key == 'nodeid':
                    raise ValueError("Key '{}' not included but its required.".format('nodeid'))
                elif key == 'decoration':
                    self._data[key] = None
                elif key == 'styles':
                    self._data[key] = {}
                else:
                    self._data[key] = ''
        if self._data['decoration'] is None:
            self._data['decoration'] = self.registerIcon(self._data['field'])
        
        if len(self.FIELDS) != len(self.data):
            raise AssertionError("Number of labels ({}) is not equal to number of fields ({})"
                                 .format(len(self.FIELDS), len(self.data)))
        

    def __repr__(self) -> str:
        return f"<{curFileName}:{type(self).__name__}"
    

    @property
    def data(self):
        return self._data
    

    @property
    def decoration(self):
        return self.data['decoration']
    

    @property
    def status(self):
        return self.data['field']
    

    ##############
    #  Messages  #
    ##############

    @property
    def _interactionNode(self):
        return "N-{} ({})".format(self.data['nodeid'], self.data['timeStamp'])
    

    @property
    def _headerText(self):
        return "Interaction Node - {}".\
            format(self.data['nodeid'])
    

    @property
    def _statusTexts(self):
        return ("<span style='color:{};font-weight:bold;'>{}</span><br>".\
            format(self.STATUS_COLORS[self.status]," ### -------- Results -------- ### ") + 
               "<span style='color:{};'>* status: {}</span><br>".\
            format(self.STATUS_COLORS[self.status], self.status.upper()) + 
               "<span style='color':{};'>* request time: {}</span><br>".\
            format(self.STATUS_COLORS[self.status], self.data['timeStamp'])
               )
    

    @property
    def _detailedTexts(self):
        return ("<span style='font-weight:bold;'>{}</span><br>".\
            format(" ### -------- Details -------- ### ") + 
               "To be finished ..."
               )
    

    ##############
    #   Methods  #
    ##############
    
    def registerIcon(self, result='question'):
        """ Registers icon for the item with no set decoration
            or after the retrived result status.
        """

        if result is None or result not in ["question", "success", "failure"]:
            result = 'question'
        if result == 'question':
           icon = QtGui.QIcon(
                os.path.join(os.path.join(ICONS_DIR, "question.png"))) 
        elif result == 'success':
            icon = QtGui.QIcon(
                os.path.join(os.path.join(ICONS_DIR, "success.png"))) 
        elif result == 'failure':
            icon = QtGui.QIcon(
                    os.path.join(os.path.join(ICONS_DIR, "failure.png"))) 
        return icon



class InfoItemStore(BaseItemStore):
    """ Class that stores a collection of BaseInfoItems or descendants.

        The BaseInfoItemStore can only store items of one type (ITEM_CLASS). Descendants will
        store their own type. 
        :: It's another type of item store differing from the inspector/rti/config items.
    """

    ITEM_CLASS = BaseInfoItem

    # --- override the functions inherited from the ancestor --- #
    def marshall(self):
        pass

    def unmarshall(self, items=None):
        """ initializes from the `items` """
        self.clear()
        if items is not None:
            for storeItem in items:
                check_class(storeItem, BaseInfoItem)
                self._items.append(storeItem)