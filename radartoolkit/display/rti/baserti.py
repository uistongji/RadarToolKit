#!/usr/bin.env python


from ..models.treeitems import AbstractLazyLoadTreeItem
from ..utils.check_class import is_a_sequence, is_a_color_str, check_class
from ..utils import six
from ..utils.defs import DIM_TEMPLATE
from ..utils.dirs import normRealPath
from ..settings import DEBUGGING
from .fileiconfactory import FileIconFactory
import logging, os


logger = logging.getLogger(__name__)


def shapeToSummary(shape, postfix="elements"):
    """ postfix can be sent by "Ascan" or "Bscan"
    """
    return " × ".join([str(elem) for elem in shape]) + " " + postfix


def lengthToSummary(length, postfix="items"):
    """ Constructs a summary from the length of an array
    """
    return str(length) + " " + postfix



class BaseRti(AbstractLazyLoadTreeItem):
    """ 
    TreeItem for use in a RepositoryTreeModel.
    Base node from which to derive the other types of nodes.

    Serves as an interface but can also be instantiated for debugging purposes.

    Parameters
    ----------
    BaseRti.nodeName <- (nodeName=baseName, fileName=fileName, iconColor=iconColor)
    BaseRti.name: name
    """  
    _defaultIconGlyph = None  # Can be overridden by defining a _iconGlyph attribute
    _defaultIconColor = None  # Can be overridden by defining a _iconColor attribute

    def __init__(self, nodeName, iconColor, fileName=''):
        super(BaseRti, self).__init__(nodeName=nodeName)
        assert is_a_color_str(iconColor), \
            "Icon color for {!r} not a hex string: {!r}".format(self, iconColor)
        self._iconColor = iconColor

        self._isOpen = False
        self._exception = None # Any exception that may occur when opening the item

        check_class(fileName, six.string_types, allow_none=True)
        if fileName:
            fileName = os.path.abspath(fileName)
        self._fileName = fileName


    @classmethod
    def createFromFileName(cls, fileName, iconColor):
        """ creates a BaseRti given its file name """
        logger.debug("BaseRti::createFromFileName: fileName={}, color={}".format(fileName, iconColor))
        baseName = os.path.basename(normRealPath(fileName))
        if not baseName:
            logger.warning("Empty file name in path: {}. Using '<root>' as root path.")
            baseName = '<root directory>'
        return cls(nodeName=baseName, fileName=fileName, iconColor=iconColor)
    

    ##############
    # Properties #
    ##############

    @property
    def rootFileName(self):
        """ Always keeps a reference to the root fileName from
            being gargabed if usr clicks any procCombobox to see what happens.
        """ 
        return self._fileName


    @property
    def fileName(self):
        return self._fileName
    

    @property
    def isOpen(self):
        """ returns True if the underlying resources are opened """
        return self._isOpen
    
    
    @property
    def exception(self):
        """ The exception if an error has occurred during reading """
        return self._exception
    
    
    @property
    def iconColor(self):
        """ Returns the color of the icon (.e.g. '#FF0000' for red).
            :rtype: string
        """
        return self._iconColor


    @property
    def iconGlyph(self):
        """ Returns the kind of the icon (e.g. FileIconFactory.FILE, FileIconFactory.ARRAY, etc).
            The base implementation returns the default glyph of the class.
            :rtype: string
        """
        if hasattr(self, "_iconGlyph"):
            return getattr(self, "_iconGlyph")
        else:
            return self._defaultIconGlyph


    @property
    def decoration(self):
        """ The displayed icon.

            Shows open icon when node was visited (children are fetched). This allows users
            for instance to collapse a directory node but still see that it was visited, which
            may be useful if there is a huge list of directories.
        """
        fileIconFactory = FileIconFactory.singleton()

        if self._exception:
            return fileIconFactory.getIcon(fileIconFactory.ERROR, isOpen=False,
                                          color=fileIconFactory.COLOR_ERROR)
        else:
            return fileIconFactory.getIcon(self.iconGlyph, isOpen=not self.canFetchChildren(),
                                          color=self._iconColor)


    @property
    def isSliceable(self):
        """ Returns True if the underlying data can be sliced.
            An inspector should always check this before using an index/slice on an RTI.

            The base implementation returns False. Descendants should override this if they contain
            an array that can be sliced.
        """
        return False
    

    @property
    def nDims(self):
        """ The number of dimensions of the underlying array
            The base implementation returns len(self.arrayShape). Descendants may override this to
            provide a more efficient implementation
        """
        return len(self.arrayShape)


    @property
    def arrayShape(self):
        """ Returns the shape of the underlying array.
            The base function is abstract. Descendants should override this if they contain
            an array that can be sliced (i.e. self.isSliceable is True).
        """
        raise NotImplemented("Override for slicable arrays")
    

    @property
    def chunking(self):
        """ List with chunk sizes if chunked storage is used. Or 'contiguous' for contiguous storage

            By default the empty string is returned, meaning chunking is not applicable for this RTI
        """
        return ""
    

    @property
    def chunksString(self):
        """ String representation of the chunk sizes. For convenience.
        """
        chunking = self.chunking
        if isinstance(chunking, str):
            return chunking
        else:
            return " × ".join(str(elem) for elem in chunking)
        

    @property
    def dimensionality(self):
        """ String that describes if the RTI is an array, scalar, field, etc.
        """
        return ""
    
    
    @property
    def elementTypeName(self):
        """ String representation of the element type.
        """
        return ""
    

    @property
    def typeName(self):
        """ String representation of the type. By default, the elementTypeName + dimensionality.
        """
        return self.elementTypeName + " " + self.dimensionality

    @property
    def attributes(self):
        """ The attribute dictionary.
            The attributes generally contain meta data about the item.
        """
        return {}
    
    @property
    def dimensionNames(self):
        """ Returns a list with the name of each of the RTI's dimensions.
            The default implementation returns ['Dim0', 'Dim1', ...] by default. Descendants can
            override this.
        """
        return [DIM_TEMPLATE.format(dimNr) for dimNr in range(self.nDims)]
    @property
    def dimensionPaths(self):
        """ Returns a list with the full path names of the dimensions.
            The default implementation returns None. Descendants can override this.
        """
        return None

    @property
    def unit(self):
        """ Returns the unit of the RTI. The base implementation returns ''.
        """
        return ""
    
    @property
    def summary(self):
        """ Returns a summary of the contents of the RTI.  E.g. 'array 20 x 30' elements.

            The base implementation returns ''.
        """
        return ""
    
    @property
    def missingDataValue(self):
        """ Returns the value to indicate missing data.

            The base implementation returns None, indicating that there is no missing data
            specified.
        """
        return None
    
    @property
    def relativesInfo(self):
        return {}
    
    def __getitem__(self, index):
        """ Called when using the RTI with an index (e.g. rti[0]).

            The base function is abstract. Descendants should override this if they contain
            an array that can be sliced (i.e. self.isSliceable is True). It should then
            call __getitem__(index) on the underlying array data.

            This may return a numpy array or scalars. Collector.getSlicedArray will convert this into an array
            if case a scalar is expected.
        """
        raise NotImplemented("Override for slicable arrays")
        
    ##############
    #   Methods  #
    ##############

    def finalize(self):
        """ Can be used to cleanup resources. Should be called explicitly.
            Recursively calls the close method on all children and then on itself.
            In turn, close calls _closeRecources; descendants should override the latter.
        """
        for child in self.childItems:
            child.finalize()
        self.close()


    def open(self):
        """ Opens underlying resources and sets isOpen flag.
            It calls _openResources. Descendants should usually override the latter
            function instead of this one.
        """
        self.clearException()
        try:
            if self._isOpen:
                logger.warning("Resources already open. Closing them first before opening.")
                self._closeResources()
                self._isOpen = False
            
            assert not self._isOpen, "Sanity check failed: _isOpen should be false"
            logger.debug("Opening {}".format(self))
            self._openResources()
            self._isOpen = True

            if self.model:
                self.model.sigItemChanged.emit(self)
            else:
                logger.warning("Model not set yet: {}".format(self))

        except Exception as ex:
            if DEBUGGING:
                raise
            logger.exception("Error during tree item open: {}".format(ex))
            self.setException(ex)


    def _openResources(self):
        """ Can be overridden to open the underlying resources.
            The default implementation does nothing.
            Is called by self.open
        """
        pass


    def close(self):
        """ Closes underlying resources and un-sets the isOpen flag.
            Any exception that occurs is caught and put in the exception property.
            This method calls _closeResources, which does the actual resource cleanup. Descendants
            should typically override the latter instead of this one.
        """
        self.clearException()
        try:
            if self._isOpen:
                logger.debug("Closing {}".format(self))
                self._closeResources()
                self._isOpen = False
            else:
                logger.debug("Resources already closed (ignored): {}".format(self))
            
            if self.model:
                self.model.sigItemChanged.emit(self)
            else:
                logger.warning("Model not set yet: {}".format(self))

        except Exception as ex:
            if DEBUGGING:
                raise
            logger.error("Error during tree item close: {}".format(ex))
            self.setException(ex)


    def _closeResources(self):
        """ Can be overridden to open the underlying resources.
            The default implementation does nothing.
            Is called by self.open
        """
        pass


    def _checkFileExists(self):
        """ Verifies that the underlying file exists and sets the _exception attribute if not
            Returns True if the file exists.
            If self._fileName is None, nothing is checked and True is returned.
        """
        if self._fileName and not os.path.exists(self._fileName):
            msg = "File not found: {}".format(self._fileName)
            logger.error(msg)
            self.setException(IOError(msg))
            return False
        else:
            return True
        

    def fetchChildren(self):
        """ Creates child items and returns them.
            Opens the tree item first if it's not yet open.

            Descendants should override _fetchAllChildren, not fetchChildren.
        """
        assert self._iconColor is not None, "Icon color none for: {}".format(self)
        assert self._canFetchChildren, "canFetchChildren must be True"
        try:
            self.clearException()

            if not self.isOpen:
                self.open() 
            
            if not self.isOpen:
                logger.warning("Opening item failed during fetch (aborted)")
                return [] # no need to continue if opening failed.
            
            childItems = []
            try:
                childItems = self._fetchAllChildren()
                assert is_a_sequence(childItems), "ChildItems must be a sequence"
            except Exception as ex:
                # This can happen, for example, when a NCDF/HDF5 file contains data types that
                # are not supported by the Python library that is used to read them.
                if DEBUGGING:
                    raise
                logger.error("Unable fetch tree item children: {}".format(ex))
                self.setException(ex)
            return childItems
        finally:
            self._canFetchChildren = False


    def _fetchAllChildren(self):
        """ The function that actually fetches the children. Default returns no children. """
        return []
    

    def quickLook(self, width: int):
        """ Returns a string representation fof the RTI to use in the Quik Look pane.

            Args:
                Width in characters.
        """
        if not self.isSliceable:
            return ""
        else:
            # We would like to use np.array2string so that we can use commas to separate the array
            # elements, and can set the line length without side effects, but unfortunately
            # np.array2string doesn't work for masked arrays.
            # See: https://github.com/numpy/numpy/issues/11674
            return str(self[...])
        

    def setException(self, ex):
        self._exception = ex


    def clearException(self):
        self._exception = None


    # TEST added on 20231107
    @property
    def isbxdsNode(self):
        return False
    
    
    @property
    def isNode(self):
        return False