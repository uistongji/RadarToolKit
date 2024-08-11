#!/usr/bin.env python

from ..bindings import QtCore, QtGui
from ..reg.tabmodel import BaseItem, BaseItemStore, BaseTableModel
from ..utils.importutils import ImportClass
from ..config.utils import type_name

import enum, logging, traceback
import inspect, os, sys

logger = logging.getLogger(__name__)

QCOLOR_REGULAR = QtGui.QColor('black')
QCOLOR_NOT_IMPORTED = QtGui.QColor('grey')
QCOLOR_ERROR = QtGui.QColor('red')


@enum.unique
class RegType(enum.Enum):
    String = 0
    ColorStr = 1
    ShortCut = 2


def nameToIdentifier(fullName):
    return string_to_identifier(fullName, white_space_becomes='')


def string_to_identifier(s, white_space_becomes='_'):
    """ Takes a string and makes it suitable for use as an identifier

        Translates to lower case
        Replaces white space by the white_space_becomes character (default=underscore).
        Removes and punctuation.
    """
    import re
    s = s.lower()
    s = re.sub(r"\s+", white_space_becomes, s)  # replace whitespace with underscores
    s = re.sub(r"-", "_", s)  # replace hyphens with underscores
    s = re.sub(r"[^A-Za-z0-9_]", "", s)  # remove everything that's not a character, a digit or a _
    return s


class BaseRegItem(BaseItem):
    """ Represents a class that is registered in the registry.

        Each registry item (RegItem) can import its class. If the import fails, the exception info
        is put into the exception property. The underlying class is not imported by default;
        use tryImportClass or getClass() for this.

        Some of the underlying class's attributes, such as the docstring, are made available as
        properties of the RegItem as well. If the class is not yet imported, they return None.
    """
    FIELDS = ['name', 'absClassName', 'pythonPath']
    TYPES = [RegType.String, RegType.String, RegType.String]
    LABELS = ['Name', 'Class', 'Python path']
    STRETCH = [False, False, True]

    def __init__(self, name='', absClassName='', pythonPath=''):
        """ Constructor.

            :param name: fullName comprising of library and name, separated by a slash.
                Can contain spaces. E.g.: 'library name/My Widget'
                Must be unique when spaces are removed and converted to lower case.
            :param absClassName: absolute name of the underlying class. Must include the full
                path of packages and module. E.g.: 'rtk.plugins.rti.ncdf.NcdfFileInspector'
            :param pythonPath: directory that will be added to the sys.path before importing.
                Can be multiple directories separated by a colon (:)
        """
        super(BaseRegItem, self).__init__()

        self._data = {'name': name, 'absClassName': absClassName, 'pythonPath': pythonPath}

        self._cls = None
        self._triedImport = False
        self._exception = None

    def __repr__(self) -> str:
        return "<{} (0x{:x}): {!r}>".format(type_name(self), id(self), self.name)

    @property
    def identifier(self):
        """ The name with wihte space removed.
        """
        return nameToIdentifier(self._data['name'])

    @property
    def name(self):
        """ Name of the registered plug in.
        """
        return self._data['name']

    @property
    def absClassName(self):
        """ Absolute name of the underlying class.

        Must include the full path of packages and module.
        E.g.: 'rtk/../plugins.rti.ncdf.NcdfFileInspector'
        """
        return self._data['absClassName']

    @property
    def pythonPath(self):
        """ Directory that will be added to the sys.path before importing.
            Can be multiple directories separated by a colon (:)
        """
        return self._data['pythonPath']

    @property
    def library(self):
        """ The fullName minus the last part (the name).
            Used to group libraries together, for instance in menus.
        """
        return os.path.dirname(self.absClassName)

    def splitName(self):
        """ Returns (self.library, self.name) tuple but is more efficient than calling both
            properties separately.
        """
        return os.path.split(self.absClassName)

    @property
    def cls(self):
        """ Returns the underlying class.
            Returns None if the class was not imported or import failed.
        """
        return self._cls

    @property
    def docString(self):
        """ A cleaned up version of the doc string of the registered class.
            Can serve as backup in case descriptionHtml is empty.
        """
        return inspect.cleandoc('' if self.cls is None else self.cls.__doc__)

    @property
    def triedImport(self):
        """ Returns True if the class has been imported (either successfully or not)
        """
        return self._triedImport

    @triedImport.setter
    def triedImport(self, value):
        """ Set to true if the class has been imported (either successfully or not)
        """
        self._triedImport = value

    @property
    def successfullyImported(self):
        """ Returns True if the import was a success, False if an exception was raised.
            Returns None if the class was not yet imported.
        """
        if self.triedImport:
            return self.exception is None
        else:
            return None

    @property
    def exception(self):
        """ The exception that occurred during the class import.
            Returns None if the import was successful.
        """
        return self._exception

    def tryImportClass(self):

        self._triedImport = True
        self._exception = None
        self._cls = None

        try:
            for pyPath in self.pythonPath.split(';'):
                if pyPath and pyPath not in sys.path:
                    logger.debug("Appending {!r} to the PythonPath".format(pyPath))
                    sys.path.append(pyPath)

            self._cls = self.importClass(self.absClassName)
        except Exception as ex:
            ex.traceBackString = traceback.format_exc()
            self._exception = ex
            logger.warning("Unable to import {!r}: {}".format(self.absClassName, ex))
            logger.debug("Traceback: {}".format(ex.traceBackString))

    def getClass(self, tryImport=True):
        """ Gets the underlying class. Tries to import if tryImport is True (the default).
            Returns None if the import has failed (the exception property will contain the reason)
        """
        if not self.triedImport and tryImport:
            self.tryImportClass()
        return self._cls

    def importClass(self, fullClassPath):

        cls = ImportClass(fullClassPath)
        return cls


class BaseRegistry(BaseItemStore):
    """ Class that maintains the collection of registered classes (plugins).

        It can load or store its classes in the persistent settings. It can also create a default
        set of plugins that can be used initially, the first time the program is executed.

        The BaseRegistry can only store items of one type (ClassRegItem). Descendants will
        store their own type. For instance the InspectorRegistry will store InspectorRegItem
        items. This makes serialization easier.
    """

    ITEM_CLASS = BaseRegItem

    @property
    def registryName(self):

        raise NotImplementedError

    def getItemById(self, identifier):
        """ Gets a registered item given the identifier. Returns None if not found.
        """

        for item in self._items:
            if item.identifier == identifier:
                return item

        return None

    def getDefaultItems(self):
        """ Returns a list with the default plugins in the registry.
            This is used initialize the application plugins when there are no saved settings,
            for instance the first time the application is started.
            The base implementation returns an empty list but other registries should override it.
        """
        raise NotImplementedError

    def createTableModel(self, parent=None):
        """ Creates a BaseRegistryModel that has self as an item store.

            Descendants can override so they can create specialized types of registry models
        """
        return BaseRegistryModel(store=self, parent=parent)


class BaseRegistryModel(BaseTableModel):
    """ Table model that holds a BaseRegistry store
    """
    def __init__(self, store, parent=None):
        """ Constructor.

            :param store: Underlying data store, must descent from BaseRegistry
            :param parent: Parent widget
        """
        super(BaseRegistryModel, self).__init__(store, parent)

        self.regularBrush = QtGui.QBrush(QCOLOR_REGULAR)
        self.notImportedBrush = QtGui.QBrush(QCOLOR_NOT_IMPORTED)
        self.errorBrush = QtGui.QBrush(QCOLOR_ERROR)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """ Returns the data stored under the given role for the item referred to by the index.
        """
        if not index.isValid():
            return None

        if role == QtCore.Qt.ForegroundRole:
            item = self._store.items[index.row()]

            if item.succussfullyImported is None:
                return self.notImportedBrush
            elif item.successfullyImported:
                return self.regularBrush
            else:
                return self.errorBrush
        else:
            return super(BaseRegistryModel, self).data(index, role=role)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """ Sets the role data for the item at index to value.
        """
        result = super(BaseRegistryModel, self).setData(index, value, role=role)

        if not index.isValid():
            return False

        if role != QtCore.Qt.EditRole:
            return False

        regItem = self._store.items[index.row()]
        regItem.tryImportClass()

        self.emitDataChanged(regItem)
        return result

    def tryImportRegItem(self, regItem):
        """ Tries to import a registry item (plugin)
        """
        logger.debug("Importing {}...".format(regItem.name))
        regItem.tryImportClass()
        self.emitDataChanged(regItem)


def import_symbol(full_symbol_name):
    """ Imports a symbol (e.g. class, variable, etc) from a dot separated name.
        Can be used to create a class whose type is only known at run-time.

        The full_symbol_name must contain packages and module,
        e.g.: 'rtk/../plugins.rti.ncdf.NcdfFileRti'
        --> symbol_name = NcdfFileRti.
        --> module_name = 'rtk/../plugins.rti.ncdf'

        If the module doesn't exist an ImportError is raised.
        If the class doesn't exist an AttributeError is raised.
    """
    parts = full_symbol_name.rsplit('.', 1)
    if len(parts) == 2:
        module_name, symbol_name = parts
        module_name = str(module_name)  # convert from possible unicode
        symbol_name = str(symbol_name)
        module = __import__(module_name, fromlist=[symbol_name])
        cls = getattr(module, symbol_name)
        return cls
    elif len(parts) == 1:
        # No module part, only a class name. If you want to create a class
        # by using name without module, you should use globals()[symbol_name]
        # We cannot do this here because globals is of the module that defines
        # this function, not of the modules where this function is called.
        raise ImportError("full_symbol_name should contain a module")
    else:
        assert False, "Bug: parts should have 1 or elements: {}".format(parts)


@enum.unique
class RegType(enum.Enum):
    String = 0
    ColorStr = 1
    ShortCut = 2
