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
    RadarToolKit (ISR) FileHub.
"""

import logging
import os

from ..bindings import QtGui, QtCore, QtWidgets, QtSignal, QtSlot, Qt
from ..widgets.basepanel import BasePanel
from ..models.rtktreeview import RTKTreeView
from ..config.ctis.groupcti import MainGroupCti
from ..rti.rtis import MappingRti, createExpansiveRtis, getExpansiveTasksName
from .panes import PropertiesPane, RelativesPane, DerivativesPane
from ..utils.constants import COL_NODE_NAME_WIDTH, COL_SUMMARY_WIDTH
from ..utils.check_class import check_is_a_sequence, check_class
from .fileiconfactory import FileIconFactory
from ..reg.basereg import nameToIdentifier
from .filetreemodel import FileTreeModel
from ..settings import (COL_KIND_WIDTH, DOCK_MARGIN)
from cookies.processing.procs import PIK1Thread


logger = logging.getLogger(__name__)

SEPARATORS_LIST = [3, 6]
LEFT_DOCK_WIDTH = 440  # needs room for scroll bars


class FileHub(BasePanel):
    """ 
    * added 'breakout' & 'pik1' buttons here. (yes)
    * moved detailsTabs from `class:MainWindow` to `class:FileWidget` (no)
    """

    def __init__(self, fileTreeModel, collector, parent=None, app=None):
        """ Constructor. """
        super(FileHub, self).__init__(parent=parent)

        self.fileTreeView = FileTreeView(fileTreeModel, collector, app=app)
        self._initView()

        # --- signal-slot connection ---
        self.detailTabs.currentChanged.connect(self.tabChanged)
        self.fileTreeView.sigFileItemChanged.connect(self.FileItemChanged)


    def __repr__(self) -> str:
        return f"<{type(self).__name__}"
    
    
    def _initView(self):

        self.detailTabs = QtWidgets.QTabWidget()
        self.detailTabs.setFixedHeight(160) 
        self.detailPanes = []

        self.propPane = self.addDetailsPane(PropertiesPane(self.fileTreeView))
        self.relatPane = self.addDetailsPane(RelativesPane(self.fileTreeView))
        self.derivPane = self.addDetailsPane(DerivativesPane(self.fileTreeView))
        self.detailTabs.setCurrentIndex(1)

        self.verSplitter = QtWidgets.QSplitter()
        self.verSplitter.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.verSplitter.addWidget(self.fileTreeView)
        self.verSplitter.addWidget(self.detailTabs)
        self.verSplitter.setSizes([1, 0])
        
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setSpacing(10)
        self.mainLayout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)
        self.mainLayout.addWidget(self.verSplitter)


    def FileItemChanged(self, rti):
        """ Updates the detailTabs.
        """
        logger.debug("FileWidget.FileItemChanged: {}".format(rti))
        curPanel = self.detailTabs.currentWidget()
        # curPanel = self.detailTabs.widget(0)
        if curPanel:
            curPanel.itemChanged(rti)
        else:
            logger.debug("No panel selected.")


    def tabChanged(self, _tabIndex):
        """ Updates the tab from the currently selected file item in the tree. 
        """
        currentFileItem, _currentIndex = self.fileTreeView.getCurrentItem()
        self.FileItemChanged(currentFileItem)


    def addDetailsPane(self, detailPane):
        """ Add panes to display detailed information.
        """
        self.detailTabs.addTab(detailPane, detailPane.classLabel())
        self.detailPanes.append(detailPane)
        return detailPane
    




class FileTreeView(RTKTreeView):
    """ Tree Widget for browsing the data repository, 
        currently it only supports selecting one item.  
    """
    # sigFileItemChanged parameter is BaseRti or None when no RTI is returned
    sigFileItemChanged = QtSignal(object)
    sigContentsUpdated = QtSignal(object) # Can be emitted when contents changed (e.g., long-time processing flow ...)
    sigShowMessage = QtSignal(str)


    def __init__(self, fileTreeModel, collector, parent=None, app=None):
        super(FileTreeView, self).__init__(fileTreeModel, parent)

        self._collector = collector
        self._app = app
        self._threads = []
        self._config = self._createConfig()

        treeHeader = self.header()
        treeHeader.resizeSection(FileTreeModel.COL_NODE_NAME, COL_NODE_NAME_WIDTH)
        treeHeader.resizeSection(FileTreeModel.COL_KIND, COL_KIND_WIDTH)
        treeHeader.resizeSection(FileTreeModel.COL_SUMMARY, COL_SUMMARY_WIDTH)
        treeHeader.setStretchLastSection(True)

        """ headerNames: [Name, Kind, Summary]
            checked: for choosing which one to be displayed as treeheader
        """
        headerNames = self.model().horizontalHeaders
        enabled = dict((name, True) for name in headerNames)
        enabled[headerNames[FileTreeModel.COL_NODE_NAME]] = False
        checked = dict((name, False) for name in headerNames)
        checked[headerNames[FileTreeModel.COL_NODE_NAME]] = True
        checked[headerNames[FileTreeModel.COL_KIND]] = True
        checked[headerNames[FileTreeModel.COL_SUMMARY]] = True
        self.addHeaderContextMenu(checked=checked, enabled=enabled, checkable={})

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.setUniformRowHeights(True)
        self.constructActions()

        # connect signals
        selectionModel = self.selectionModel() # need to store reference to prevent crash in PySide
        selectionModel.currentChanged.connect(self.currentItemChanged)

        # close files on collapse. Note that, self.collapsed does NOT seem to be connected to self.collapse by default,
        # so there is not conflict here. Also there is no need to connect to expand, this is automatic with the
        # fetchMore mechanism
        self.collapsed.connect(self.closeItem)

        self.model().sigItemChanged.connect(self.fileTreeItemChanged)
        self.model().sigAllChildrenRemovedAtIndex.connect(self.collapse)

        # --- signal-slot connnections ---
        self.collector.sigProcessingChanged.connect(self.insertItemByCollector)
        self.collector.sigProdDictChanged.connect(self.pickTargetRtiByCollector)


    def sizeHint(self):
        """ The recommended size for the FileWidget """
        return QtCore.QSize(LEFT_DOCK_WIDTH, 400) # 450
    

    ##############
    # Properties #
    ##############

    @property
    def eye(self):
        return self._eye
    
    
    @property
    def collector(self):
        return self._collector
    
    
    @property
    def app(self):
        return self._app
    

    @property
    def config(self):
        """ The root config tree item for the FileWidget """
        return self._config
    

    @property
    def registry(self):
        return self.app.fileRegistry
    

    ##############
    #   Methods  #
    ##############

    def finalize(self):
        """ disconnects signals and frees resources """
        self.model().sigItemChanged.disconnect(self.fileTreeItemChanged)

        selectionModel = self.selectionModel()
        selectionModel.currentChanged.disconnect(self.currentItemChanged)


    def constructActions(self):
        """ 
        Constructs actions group for fileHub. 
        """

        self.currentItemActionGroup = QtGui.QActionGroup(self)
        self.currentItemActionGroup.setExclusive(False)

        # open current selected item
        self.openItemAction = QtGui.QAction("Open Item", self.currentItemActionGroup,
                                            triggered=self.openCurrentItem)
        self.addAction(self.openItemAction)

        # close current selected item: all the children will be unfetched and closed!
        self.closeItemAction = QtGui.QAction("Close Item", self.currentItemActionGroup,
                                             toolTip="close the current selected item, all the children will be closed.",
                                             triggered=self.closeCurrentItem)
        self.addAction(self.closeItemAction)

        # collapse current selected item without closing any item. can be open anytime!
        self.collapseItemAction = QtGui.QAction("Collapse Item", self.currentItemActionGroup,
                                                toolTip="close the current selected item, all the children will NOT be closed.",
                                                triggered=self.collapseCurrentItem)
        self.addAction(self.collapseItemAction)
        
        # remove current selected item from the file tree 
        self.removeItemAction = QtGui.QAction("Remove Item", self.currentItemActionGroup,
                                              shortcut=QtGui.QKeySequence.Delete,
                                              triggered=self.removeCurrentItem)
        self.addAction(self.removeItemAction)

        # copy file path to the clipboard
        self.copyPathAction = QtGui.QAction("Copy File Path to Clipboard", self.currentItemActionGroup,
                                            triggered=self.copyPath2Clipboard)
        self.addAction(self.copyPathAction)
        

    def contextMenuEvent(self, event):
        """ Creates and executes the context menu for the tree view.
        """
        menu = QtWidgets.QMenu(self)
        for action in self.currentItemActionGroup.actions():
            menu.addAction(action)
        menu.addSeparator()

        # --- load as sub-menu ---
        loadAsMenu = QtWidgets.QMenu(parent=menu)
        loadAsMenu.setTitle("Load File As ...")
        loadAsMenu.aboutToShow.connect(lambda: self._populateLoadAsMenu(loadAsMenu))
        menu.addMenu(loadAsMenu)

        # ------ add a Separator ------
        # browse directory: this will automatically detect the rti type.
        self.browseDirectoryAction = QtGui.QAction("Browse Directory ...", self,
                                                   triggered=self.browseDirectory)
        menu.addAction(self.browseDirectoryAction)

        saveAsMenu = QtWidgets.QMenu(parent=menu)
        saveAsMenu.setTitle("Save File As ...")
        saveAsMenu.aboutToShow.connect(lambda: self._populateSaveAsMenu(saveAsMenu))
        menu.addMenu(saveAsMenu)

        menu.addSeparator()
        RecentMenu = QtWidgets.QMenu(parent=menu)
        RecentMenu.setTitle("Recent Files ...")
        RecentMenu.aboutToShow.connect(lambda: self._populateOpenRecentMenu(RecentMenu))
        menu.addMenu(RecentMenu)

        menu.exec_(event.globalPos())


    def _populateLoadAsMenu(self, loadAsMenu):
        """ Repopulates the submenu for the Open Item choice (which is used to reload files). 
        """
        loadAsMenu.clear() # make sure the actions added before have been clean

        for rtiRegItem in self.registry.items:
            if not rtiRegItem.triedImport:
                rtiRegItem.tryImportClass()
            
            def createTrigger():
                """ function to create a closure with the rtiRegItem """
                _rtiRegItem = rtiRegItem
                return lambda: self.openFiles(rtiRegItem=_rtiRegItem,
                                             fileMode=QtWidgets.QFileDialog.ExistingFile,
                                             caption="Open {}".format(_rtiRegItem.name))
            
            action = QtGui.QAction(" {} ".format(rtiRegItem.name), self,
                                   enabled=bool(rtiRegItem.successfullyImported),
                                   triggered=createTrigger(),
                                   icon=rtiRegItem.decoration)
            loadAsMenu.addAction(action)
    
    
    def _populateSaveAsMenu(self, saveAsMenu):
        """ 
        Repopulates the submenu for the Save Item choice (which is used to reload files). 
        """
        saveAsMenu.clear() # make sure the actions added before have been clear

        for rtiRegItem in self.registry.getDefaultSaveItems():
            if not rtiRegItem.triedImport:
                rtiRegItem.tryImportClass()
            
            def createTrigger():
                """ function to create a closure with the rtiRegItem """
                _rtiRegItem = rtiRegItem
                return lambda: self.saveFiles(rtiRegItem=_rtiRegItem,
                                              fileMode=QtWidgets.QFileDialog.ExistingFiles,
                                              caption="Save {}".format(_rtiRegItem.name))
            
            action = QtGui.QAction(" {} ".format(rtiRegItem.name), self,
                                   enabled=bool(rtiRegItem.successfullyImported),
                                   triggered=createTrigger(),
                                   icon=rtiRegItem.decoration)
            saveAsMenu.addAction(action)
    

    def _populateOpenRecentMenu(self, RecentMenu):
        """ 
        Repopulates the submenu for the recent items that are obtained from the configurations.
        """
        RecentMenu.clear() # make sure the actions added before have been clear

        fileIconFactory = FileIconFactory.singleton()
        fileRegistry = self.app.fileRegistry
        recentFiles = self.app.getRecentFiles()
        
        # count duplicate basename and this will be added with their full path
        baseNameCount = {}
        for _timeStamp, fileName, _rtiRegName in recentFiles:
            _, baseName = os.path.split(fileName)
            if baseName in baseNameCount:
                baseNameCount[baseName] += 1
            else:
                baseNameCount[baseName] = 1
        
        # list returned has already been sorted as added-timing
        for _timeStamp, fileName, rtiRegItemName in recentFiles:

            regItemId = nameToIdentifier(rtiRegItemName)
            rtiRegItem = fileRegistry.getItemById(regItemId)

            if rtiRegItem is None and rtiRegItemName == 'Directory':
                rtiRegItem = fileRegistry.DIRECTORY_REG_ITEM
            
            if rtiRegItem and not rtiRegItem.triedImport:
                rtiRegItem.tryImportClass()
            
            def createTrigger():
                """ func to create a closure with the regItem """
                _fileNames = [fileName]  # keep reference in closure
                _rtiRegItem = rtiRegItem # keep reference in closure
                return lambda: self.openFiles(_fileNames, rtiRegItem=_rtiRegItem)
            
            _dirName, baseName = os.path.split(fileName)
            fileLabel = fileName if baseNameCount[baseName] > 1 else baseName

            action = QtGui.QAction(fileLabel, self, enabled=True, triggered=createTrigger())
            action.setToolTip(fileName)
            if rtiRegItem is not None:
                action.setIcon(rtiRegItem.decoration)
            else:
                action.setIcon(fileIconFactory.getIcon(fileIconFactory.TRANSPARENT, False))
            RecentMenu.addAction(action)
    

    @QtSlot()
    def openFiles(self, fileNames=None, rtiRegItem=None, 
                  caption=None, fileMode=QtWidgets.QFileDialog.ExistingFile):
        """ Lets the user select on or more files and opens it.

            :param fileName: If None, an open-file dialog allows the user to select file (single one),
                otherwise the files are opened directly.
            :param rtiRegItem: Open the files as this type of registered RTI. None=autodetect.
            :param caption: Optional caption for the file dialog.
            :param fileMode: is passed to the file dialog.
            :rtype fileMode: QtWidgets.QFileDialog.FileMode constant
        """
        check_is_a_sequence(fileNames, allow_none=True)

        if fileNames is None:
            logger.debug("<FileWidget::openFiles>: {} not exists. Opening dialog to request.".format(fileNames))
            dialog = QtWidgets.QFileDialog(self, caption=caption)
            if rtiRegItem is None:
                nameFilter = 'All files (*);;'
                nameFilter += self.registry.getFileDialogFilter()
                if fileMode == QtWidgets.QFileDialog.Directory:
                    rtiRegItemName = 'Directory'
                else:
                    rtiRegItemName = ''
            else:
                nameFilter = rtiRegItem.getFileDialogFilter()
                nameFilter += ';;All files (*)'
                rtiRegItemName = rtiRegItem.name
            dialog.setNameFilter(nameFilter)

            if fileMode:
                dialog.setFileMode(fileMode)

            if dialog.exec_() == QtWidgets.QFileDialog.Accepted:
                fileNames = dialog.selectedFiles()
            else:
                logger.debug("<FileWidget::openFiles>: user cancelled. OpenFile aborted.")
                return


        fileRootIndex = None
        model = self.model()
        for fileName in fileNames:
            fileRootIndex = model.loadFile(fileName, rtiRegItem=rtiRegItem)
            fileRootItem  = model.getItem(fileRootIndex)

            logger.debug(f"{self.__repr__()}:openFiles> called. \
                        Now it's loading the fileRootItem.name: {type(fileRootItem).__name__}")
            
            # check whether the rtiRegItem requires the expansive computational loads.
            expansiveTasksName = getExpansiveTasksName()
            name = type(fileRootItem).__name__
            if name in expansiveTasksName:
                # _subIndex = model.insertItem(MappingRti({}, nodeName=expansiveTasksName[name]), parentIndex=fileRootIndex)
                _subIndex = fileRootIndex
                self._startThreadsforTasks(fileRootItem, fileName, _subIndex=_subIndex, kind="Raw")
            else:
                pass
            self.app.addToRecentFiles(fileName, rtiRegItemName) # added to the recent loaded files.

        if len(fileNames) == 1:
            logger.debug(f"{self.__repr__()}:openFiles> called. Noew opening files: {fileNames[0]}")
            self.setExpanded(fileRootIndex, True)
        
        if fileRootIndex is not None:
            self.setCurrentIndex(fileRootIndex)


    def saveFiles(self, fileNames=None, rtiRegItem=None, 
                  caption=None, fileMode=QtWidgets.QFileDialog.ExistingFile):
        pass


    def _startThreadsforTasks(self, item, fileName, _subIndex=QtCore.QModelIndex(), kind="Raw"):
        """
        Initialize threads for bxds or pik1 type loading/processing.
        """
        if fileName is None or not os.path.exists(fileName):
            return
        
        outdir,_ = os.path.split(fileName)
        thread = PIK1Thread(kind, callable, 
                            fileName, outdir=outdir, parentIndex=_subIndex)
        self._threads.append(thread)

        thread.finished_progress.connect(self.addThreadResultsToTree)
        thread.work_done.connect(self.removeThread)
        thread.quit()
        thread.wait()
        thread.start()


    def closeCurrentItemOrNot(self):
        curIndex = self.getRowCurrentIndex()
        item = self.model().getItem(curIndex)

        if len(item.childItems) == 0:
            self.closeCurrentItem()
        else:
            pass


    @QtSlot(str, object, object)
    def insertItemByCollector(self, methodValue, item, model):
        """ 
        - parentIteRoot: Rti.procDict[]
        - model: getting parentIndex
        """
        self.sigShowMessage.emit("FileWidget::insertItemByCollector received signal from collector processing method value: {methodValue}.")
        _subIndex = item.parentIndex
        fileRootItem  = model.getItem(_subIndex)
        print(f"fileRootItem: {fileRootItem}")
        print(f"fileRootItem.fileName: {fileRootItem.fileName}")
        self._startThreadsforTasks(fileRootItem, fileRootItem.fileName, 
                                   _subIndex=_subIndex, kind=methodValue)


    @QtSlot(str, str)
    def pickTargetRtiByCollector(self, parentNodeName, methodValue):
        """ 
        param::model: self.rti.model
        -> pick the target rti.
        """
        rowCount = self.model().rowCount()
        for row in range(rowCount):
            idx = self.model().index(row, 0)
            item = self.model().getItem(idx)
            if item.nodeName == parentNodeName:
                _rowCount = self.model().rowCount(idx)
                for _row in range(_rowCount):
                    _idx = self.model().index(_row, 0, idx)
                    _item = self.model().getItem(_idx)
                    if _item.nodeName == methodValue.lower():
                        # self.closeCurrentItemorNot()
                        self.closeCurrentItem()
                        self.setCurrentIndex(self.model().index(0, 0, _idx))
                        self.openCurrentItem()


    @QtSlot(dict, str, object)
    def addThreadResultsToTree(self, results, kind, index):
        
        rti = createExpansiveRtis(kind=kind)
        model = self.model()

        check_class(results, dict)
        for nodeName, fileName in results.items():
            newIndex = model.insertItem(
                    rti(nodeName=nodeName, fileName=fileName, parentIndex=index), parentIndex=index)
        
        if newIndex is not None:
            self.closeCurrentItemOrNot()
            self.setCurrentIndex(newIndex)
            self.openCurrentItem()


    @QtSlot(object)
    def removeThread(self, _thread):
        """
        Removes thread calling.
        """
        sender = self.sender() if _thread is None else _thread
        if sender in self._threads:
            try:
                print("thread.state: {}".format(sender.isFinished()))
                self._threads.remove(sender)
                print("thread.len: {}".format(len(self._threads)))
            except Exception as e:
                print(e)
        

    @QtSlot()
    def browseDirectory(self):
        self.openFiles(fileMode=QtWidgets.QFileDialog.Directory)


    @QtSlot()
    def openCurrentItem(self):
        """ Opens the current item in the file viewer. 
        """
        # Expanding the node will indirectly call FileTreeModel.fetchMore which will call
        # BaseRti.fetchChildren, which will call BaseRti.open and thus open the current RTI.
        # BaseRti.open will emit the self.model.sigItemChanged signal, which is connected to
        # FileTreeView.FileTreeItemChanged.
        logger.debug("<FileWidget::openCurrentItem> called")
        _currentItem, currentIndex = self.getCurrentItem()
        if not currentIndex.isValid():
            return
        self.expand(currentIndex)


    @QtSlot()
    def closeCurrentItem(self):
        """ 
        Closes the current item. And all its children will be unfetched and closed. 
        """
        logger.debug("<FileWidget::closeCurrentItem> called")
        self.closeItem(self.getRowCurrentIndex())


    @QtSlot(QtCore.QModelIndex)
    def closeItem(self, index):
        """ 
        Closes the item at the index and collapses the node. 
        """
        logger.debug("<FileWidget::closeItem> called")
        if not index.isValid():
            logger.debug("<FileWidget::closeItem> invalid index. returning")
            return 
        
        # First we remove all the children, this will close them as well.
        # It will emit sigAllChildrenRemovedAtIndex, which is connected to the collapse method of
        # all trees. It will thus collapse the current item in all trees. This is necessary,
        # otherwise the children will be fetched immediately.
        self.model().removeAllChildrenAtIndex(index)

        # Close the item. BaseRti.close will emit the self.model.sigItemChanged signal,
        # which is connected to FileTreeView.fileTreeItemChanged.
        item = self.model().getItem(index)
        logger.debug("Item: {}".format(item))
        item.close()


    def expand(self, index):
        """ 
        Expands current item. updates the context menu action. 
        """
        super(FileTreeView, self).expand(index)
        self.closeItemAction.setEnabled(self.isExpanded(index)) 


    @QtSlot()
    def collapseCurrentItem(self):
        """ 
        Collapses the current item. all the children will be unfetched and closed. 
        """
        currentIndex = self.getRowCurrentIndex()
        oldBlockState = self.blockSignals(True) # prevent automatically closing of the item
        try:
            self.collapse(currentIndex)
        finally:
            self.blockSignals(oldBlockState)


    def collapse(self, index):
        """ Collapses the current item. updates the context menu action. 
        """
        super(RTKTreeView, self).collapse(index)
        self.collapseItemAction.setEnabled(self.isExpanded(index))


    @QtSlot()
    def removeCurrentItem(self):
        """ Removes the current selected item from the file tree. 
        """
        currentIndex = self.getRowCurrentIndex()
        currentItem, _  = self.getCurrentItem() 
        if not currentIndex.isValid():
            return
        self.model().deleteItemAtIndex(currentIndex) # this will close the item's resource before removing it.
        self.sigShowMessage.emit(f"{self.__repr__()}:removeCurrentItem> removed currently selected item {currentItem.nodeName}")
     

    @QtSlot()
    def copyPath2Clipboard(self):
        """ 
        Copies the file path of the currently selected item to the clipboard.
        If not exists, ask whether to save the currently selected file and then copy!
        """ 
        currentItem, currentIndex = self.getCurrentItem()
        if not currentIndex.isValid():
            return
        QtWidgets.QApplication.clipboard().setText(currentItem.nodePath)
        self.sigShowMessage.emit(f"{self.__repr__()}:_drawEvaluatorContents> copied path to the clipboard: {currentItem.nodePath}")


    def fileTreeItemChanged(self, rti):
        """ Called when a file tree item has changed (* !the item itself!, not a new selection!)
            
            If the item is the currently selected item, 
            the collector & inspector are both sequently updated.
        """
        logger.debug("<FileWidget::fileTreeItemChanged>: called")
        currentItem, _currentIndex = self.getCurrentItem()
        if rti == currentItem:
            self.currentFileTreeItemChanged()
        else:
            logger.debug("<FileWidget::fileTreeItemChanged>:" 
                         "ignoring changed item as is not the current item: {}".format(rti))


    # received signal with (current, previous). 
    # The previous model item index is replaced by the current index as the selection's current item.
    @QtSlot(QtCore.QModelIndex)
    @QtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def currentItemChanged(self, current, previous=None):
        """ Enables/disables actions when a new item is the current item in the tree view.

            Is not called currentChanged as this would override an existing method. We want to
            connect this to the currentChanged signal at the end of the constructor, which would
            then not be possible.
        """
        self.currentFileTreeItemChanged()


    def currentFileTreeItemChanged(self):
        """ 
        Called to update the GUI when a file tree item has changed or a new one was selected.
        """
        # when the model is empty, the current selected item may be None and the index may be invalid
        currentItem, currentIndex = self.getCurrentItem()

        hasCurrent = currentIndex.isValid()
        assert hasCurrent == (currentItem is not None), \
            "If current index is valid, the currentIndex may not be None."
        
        # set the item in the collector, then the evaluator
        # only the item that can be sliceable should be sent to.
        if hasCurrent:
            if not currentItem.isSliceable:
                self.sigShowMessage.emit("<{}>: current selected item is not sliceable: {}, returning ..."
                                         .format(self.__repr__(), currentItem))
            else:
                self.sigShowMessage.emit("<{}>: adding rti to collector: {}"
                                         .format(self.__repr__(), currentItem.nodePath))
                self.collector.setRti(currentItem)

        # update context menus in the file tree
        self.currentItemActionGroup.setEnabled(hasCurrent)
        self.collapseItemAction.setEnabled(self.isExpanded(currentIndex))
        self.openItemAction.setEnabled(currentItem is not None
                                       and currentItem.hasChildren()
                                       and not currentItem.isOpen)
        self.closeItemAction.setEnabled(currentItem is not None
                                        and currentItem.hasChildren()
                                        and currentItem.isOpen)

        # emit sigFileItemChanged signal so that, for example, details panes can update.
        self.sigFileItemChanged.emit(currentItem)


    def _createConfig(self):
        """ creates a config tree item hierarchy containing the default children """
        rootItem = MainGroupCti('Data Repository')
        return rootItem