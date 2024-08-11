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
# AUTHOR: Chen Lv, Jiaying Zhou (supervisor: Tong Hao), Tongji University


""" RadarToolKit (ISR) Mainwindow Instance.
"""


import logging
import base64
import os
from functools import partial

from .bindings import QtWidgets, QtCore, QtGui, QtSignal, QtSlot, Qt, QApplication
from display.rti.filehub import FileHub
from display.rti.fileiconfactory import FileIconFactory
from display.evaluator.evaluator import Evaluator

from display.reg.basereg import nameToIdentifier
from display.collector.collector import Collector
from display.map.mapview import MapView
from display.widgets.rtkstatusbar import RTKStatusBar
from display.widgets.rtkmenubar import RTKMenuBar
from display.widgets.rtktoolbox import RTKToolBox
from display.widgets.icedialog import setupEnv
from display.utils.check_class import check_is_a_sequence
from info import PROJECT_NAME, VERSION, EXIT_CODE_RESTART
from display.archives.db import createConnection, SyncSignal, DatabaseManage
from display.evaluator.abstract import UpdateReason


logger = logging.getLogger(__name__)



class MainWindow(QtWidgets.QMainWindow):

    """ 
    sigInspectorChanged: inpector changed, PgImagePlot2d / PgLinePlot1d
    sigShowMessage: raise toast changes.
    """

    sigInspectorChanged = QtSignal(object)
    sigShowMessage = QtSignal(str) # message to the user in the statusBar
    sigdbSync = SyncSignal()
    
    def __init__(self, RTKApplication, identifier):
        """ constructor """
        super(MainWindow, self).__init__()

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(255, 255, 255))
        self.setPalette(p)
        
        # --- setup all the important widgets ---
        self._RTKApplication = RTKApplication  # application instance keeper
        self._setupActions()                   # setup useful actions

        # setup the collector together with its configs
        # collector that builds the bridge between the fileHub and the evaluator.
        self._collector = Collector()

        # file hub: to load, view and organize the files in memory
        self._fileHub = FileHub(self.RTKApplication.fileTreeModel,
                                self.collector,
                                app=self.RTKApplication
                                )

        # Antarctic map viewer
        self._mapViewer = MapView()

        # data evaluator: to view and results compare with simple processing methods
        self._evaluator = Evaluator(fileHub=self.fileHub, 
                                    collector=self.collector,
                                    identifier=identifier,
                                    actions=self.evaluatorActionGroup,
                                    registy=self.RTKApplication.evaluatorRegistry
                                    )

        # Qstatusbar setting up that displays every piece of important information
        self.rtkStatusBar = RTKStatusBar(self, msg="{} IS ONLINE! READY!".format(PROJECT_NAME))
        self.setStatusBar(self.rtkStatusBar)
        
        # setup QWidget attributes
        self.setAttribute(Qt.WA_DeleteOnClose) # see closeEvent()
        self.setUnifiedTitleAndToolBarOnMac(True) # unified title and toolbar look on MacOS
    
        # initialize the mainWindow
        self._setUpWrapperWidgets() # setup centeral widget & menus bar
        self._setUpCentralWidget()


        window_width = QApplication.primaryScreen().size().width() *  2 // 3
        window_height = QApplication.primaryScreen().size().height() * 2 // 3
        self.resize(window_width, window_height)

        # move window to the center of the screen
        window_geometry = self.frameGeometry()
        center_point = QApplication.primaryScreen().availableGeometry().center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())
        
        # # ------  status bar message display  -------
        self.sigShowMessage.connect(self.showMessage) # messages from the rtkwin
        self._collector.sigShowMessage.connect(self.showMessage) # messages from the collector
        self.evaluator.sigShowMessage.connect(self.showMessage) # messages from the evaluator 
        self.fileHub.fileTreeView.sigShowMessage.connect(self.showMessage) # messages from the fileViewer 
        self.rtkToolBox.sigShowMessages.connect(self.showMessage)
        # # --- connect self._mapViewer with self.rtkToolBox.antarcmap ---
        self._mapViewer.recordSelected.connect(self.selectRecordInDatabase)
        self.rtkToolBox.sigTableChanged.connect(self.changeTable)

        # # ---- toolbox & wrapperWidget (tabWidget) ----
        self.rtkToolBox.currentChanged.connect(self.wrapperWidget.setCurrentIndex)
        self.wrapperWidget.currentChanged.connect(self.rtkToolBox.setCurrentIndex)

        self.updateWindowTitle()
        # # ----------- EOF ------------


    def __repr__(self) -> str:
        return f"<{type(self).__name__}"


    ##############
    # Properties #
    ##############

    @property
    def RTKApplication(self):
        return self._RTKApplication


    @property
    def fileHub(self):
        return self._fileHub
    

    @property
    def fileTreeModel(self):
        return self._RTKApplication.fileTreeModel
    

    @property
    def evaluator(self):
        return self._evaluator


    @property
    def collector(self):
        return self._collector


    @property
    def eyeOnIce(self):
        return self._eyeOnIce
    

    @property
    def evaPicks(self):
        return self._evaPicks
    

    @property
    def evaPicksCtiPane(self):
        return self._evaPicksCtiPane
    
    
    @property
    def mapViewer(self):
        return self._mapViewer
    
    
    @property
    def Urls(self):
        return self._Urls
    

    @property
    def dbmanage(self):
        return self._dbmanage
    

    ##############
    #   Viewers  #
    ##############

    def _setUpWrapperWidgets(self):
        
        self.wrapperWidget = QtWidgets.QTabWidget()
        self.wrapperWidget.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(255, 255, 255))
        self.wrapperWidget.setPalette(p)

        # setup toolbox
        self.rtkToolBox = RTKToolBox(self, syncSignal=self.sigdbSync)
        self._dbmanage = DatabaseManage(self.sigdbSync, 'Antarctica_Project')
        self.wrapperWidget.addTab(self.mapViewer, "Antarctic Map Viewer")
        self.wrapperWidget.addTab(self.evaluator, "Data Evaluator")
        self.wrapperWidget.addTab(self.dbmanage, "DataBase Management")


    def _setUpCentralWidget(self):
        # setup centeral widget
        self.centralWidget = CentralWidget(self)
        self.setCentralWidget(self.centralWidget)

        self.rtkMenuBar = RTKMenuBar(self) 


    def _setupMenuBar(self):
        """ Sets up the main menu 
            Re-modified the MenusTools class and combined it here.
        """

        # --- File Menu --- # -> assume RTKMenuBar already initialized fileMenu variable
        fileMenu = self.rtkMenuBar._menus['File']
        
        action = fileMenu.addAction("Browse Direcoty ...",
                    lambda: self.openFiles(fileMode=QtWidgets.QFileDialog.Directory))
        action.setShortcut(QtGui.QKeySequence("Ctrl+D"))

        action = fileMenu.addAction("Browse File ...",
                    lambda: self.openFiles(fileMode=QtWidgets.QFileDialog.ExistingFile))
        action.setShortcut(QtGui.QKeySequence("Ctrl+F"))

        self.openRecentMenu = self.rtkMenuBar._menus['Open Recent']
        self.openAsMenu = self.rtkMenuBar._menus['Open File As ...']

        # --- View Menu --- # -> assume RTKMenuBar already initialized viewMenu variable
        viewMenu = self.rtkMenuBar._menus['View']
        for action in self.evaluatorActionGroup.actions():
            viewMenu.addAction(action)
        
        viewMenu.addSeparator()

        action = viewMenu.addAction("Plugins Help",
                lambda: self.execPluginsDialog())
        action.setShortcut(QtGui.QKeySequence("Crtl+P"))
        

    def _setupActions(self):
        """
        Sets up the frequently usable actions to keep reference in a global manner.
        """
        self._createEvaluatorActionsGroup(self)
        createConnection(self)
        

    def _createEvaluatorActionsGroup(self, parent):
        """ 
        Creates an actions group with all the installed 'set evaluator' actions. 
        """
        actionGroup = QtGui.QActionGroup(parent)
        actionGroup.setExclusive(True)
        logger.debug(f"{self.__repr__()}:_createEvaluatorActionsGroup> called, "
                     f"with items: {self.RTKApplication.evaluatorRegistry.items}")
        
        for item in self.RTKApplication.evaluatorRegistry.items:
            setAndDrawFn = partial(self._updateEvaluatorById, item.identifier)
            action = QtGui.QAction(item.name, self, triggered=setAndDrawFn, checkable=True)
            action.setData(item.identifier)
            if item.shortCut:
                try:
                    keySeq = QtGui.QKeySequence(item.shortCut.strip())
                except Exception as ex:
                    logger.debug(f"{self.__repr__()}:_createEvaluatorActionsGroup> unable to create shortcut: {ex}.")
                else:
                    action.setShortcut(QtGui.QKeySequence(keySeq))
            actionGroup.addAction(action)
        self.evaluatorActionGroup = actionGroup
    

    ##############
    #   Methods  #
    ##############

    def finalize(self):
        """ called before destruction (when closing), used to clean up resources. """
        logger.debug("Closing: {}".format(self))

        # ------ disconnect status bar message display ------
        self.sigShowMessage.disconnect(self.showMessage) # messages from the rtkwin
        self._collector.sigShowMessage.disconnect(self.showMessage) # messages from the collector
        self._evaluator.sigShowMessage.disconnect(self.showMessage) # messages from the inspector 
        self._fileHub.fileTreeView.sigShowMessage.disconnect(self.showMessage) # messages from the fileViewer
        self.rtkToolBox.sigShowMessages.disconnect(self.showMessage)

        self._mapViewer.recordSelected.disconnect(self.selectRecordInDatabase)
        self.rtkToolBox.sigTableChanged.disconnect(self.changeTable)

        # ---- toolbox & wrapperWidget (tabWidget) ----
        self.rtkToolBox.currentChanged.connect(self.wrapperWidget.setCurrentIndex)
        self.wrapperWidget.currentChanged.connect(self.rtkToolBox.setCurrentIndex)


    def _repopulateOpenRecentMenu(self, *args, **kwargs):
        """ clears the currently window menu of the '# Recent Menu' and fills it with the actions """
        logger.debug(f"{self.__repr__()}:_repopulateOpenRecentMenu> called.")
        fileIconFactory = FileIconFactory.singleton()

        for action in self.openRecentMenu.actions():
            self.openRecentMenu.removeAction(action)
        
        # count duplicate basename and this will be added with their full path
        baseNameCount = {}
        for _timeStamp, fileName, _rtiRegName in self.RTKApplication.getRecentFiles():
            _, baseName = os.path.split(fileName)
            if baseName in baseNameCount:
                baseNameCount[baseName] += 1
            else:
                baseNameCount[baseName] = 1
        
        # list returned has already been sorted as added-timing
        for _timeStamp, fileName, rtiRegItemName in self.RTKApplication.getRecentFiles():

            regItemId = nameToIdentifier(rtiRegItemName)
            rtiRegItem = self.RTKApplication.fileRegistry.getItemById(regItemId)

            if rtiRegItem is None and rtiRegItemName == 'Directory':
                rtiRegItem = self.RTKApplication.fileRegistry.DIRECTORY_REG_ITEM
            
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
            
            self.openRecentMenu.addAction(action)
        

    def _repopulateOpenAsMenu(self, *args, **kwargs):
        """ clears the currently window menu of the '# Open File As Menu' and fills it with the registered file plugins """
        logger.debug(f"{self.__repr__()}:_repopulateOpenAsMenu> called.")
        for action in self.openAsMenu.actions():
            self.openAsMenu.removeAction(action)

        fileRegistry = self.RTKApplication.fileRegistry
        for rtiRegItem in fileRegistry.items:
            if not rtiRegItem.triedImport:
                rtiRegItem.tryImportClass()

            def createTrigger():
                "Function to create a closure with the regItem"
                _rtiRegItem = rtiRegItem # keep reference in closure
                return lambda: self.openFiles(rtiRegItem=_rtiRegItem,
                                              fileMode = QtWidgets.QFileDialog.ExistingFile,
                                              caption="Open {}".format(_rtiRegItem.name))
            action = QtGui.QAction("{} ...".format(rtiRegItem.name), self,
                        enabled=bool(rtiRegItem.successfullyImported),
                        triggered=createTrigger(), icon=rtiRegItem.decoration)
            self.openAsMenu.addAction(action)


    def _repopulateWindowMenu(self, actionGroup):
        """ clears the window menu and fills it with the actions of the actionGroup """
        pass


    def updateWindowTitle(self):
        """ Updates the window title with the App version & user. 
        """
        title = f"{PROJECT_NAME} (-v {VERSION}) | TONGJI UNIVERSITY"
        self.setWindowTitle(title)


    ##############
    #    Slot    #
    ##############

    @QtSlot()
    def openFiles(self, fileNames=None, rtiRegItem=None, caption=None, fileMode=None):
        """ 
        Lets the user select on or more files and opens it.

        :param fileNames: If None an open-file dialog allows the user to select files,
            otherwise the files are opened directly.
        :param rtiRegItem: Open the files as this type of registered RTI. None=autodetect.
        :param caption: Optional caption for the file dialog.
        :param fileMode: is passed to the file dialog.
        :rtype fileMode: QtWidgets.QFileDialog.FileMode constant
        """
        check_is_a_sequence(fileNames, allow_none=True)
        if fileNames is None:
            dialog = QtWidgets.QFileDialog(self, caption=caption)
            if rtiRegItem is None:
                nameFilter = 'All files (*);;' # Default show all files.
                nameFilter += self.RTKApplication.fileRegistry.getFileDialogFilter()
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
                fileNames = []
            
            # only add files that were added via the dialog box 
            # -- not via the command line
            self._RTKApplication.addToRecentFiles(fileNames, rtiRegItemName)
        
        fileRootIndex = None
        
        logger.debug("")
        for fileName in fileNames:
            fileRootIndex = self.RTKApplication.fileTreeModel.loadFile(fileName, rtiRegItem=rtiRegItem)
        
        if len(fileNames) == 1: # only expand and open the file if the usr selected one.
            logger.debug("")
            self.fileViewer.fileTreeView.setExpanded(fileRootIndex, True)
        
        # select the last opened file
        if fileRootIndex is not None:
            self.fileViewer.fileTreeView.setCurrentIndex(fileRootIndex)


    @QtSlot(str)
    def _updateEvaluatorById(self, identifier):
        """
        Updates the Evaluator interface item by identifier (ID).
        """
        self._evaluator._updateEvaluator(identifier=identifier)


    @QtSlot(str, str, str)
    def showMessage(self, msg="", item='', level="INFO"):
        logger.debug("RTKWin.showMessage() called")
        self.rtkStatusBar.showMessage(item, msg, level)     
        

    @QtSlot()
    def _quit(self):
        self.RTKApplication.quit


    @QtSlot()
    def activateAndRaise(self):
        """ Activates and raises the window ::
            Sets the top-level widget containing this widget to be the active window.
        """
        self.activateWindow()
        self.raise_()


    @QtSlot(int)
    def selectRecordInDatabase(self, record_id):
        self.rtkToolBox.antarc_map.map_db.select_record_by_id(record_id)  
        self.sigShowMessage.emit({"INFO":f"Currently selected no.{record_id} transect."})


    @QtSlot()
    def printView(self):
        """ prints the current selected view as .pdf """
        pass


    @QtSlot()
    def saveFile(self):
        """ save files as *.* """
        pass


    @QtSlot()
    def activateProcParams(self):
        """ activate and exec_ the processing parameters dialog for usr to change. """
        pass


    @QtSlot()
    def activateSearchDialog(self):
        """ shows a search widget """
        pass


    @QtSlot()
    def activateVisitDialog(self):
        """ shows a search widget """
        pass


    @QtSlot()
    def activateShortCutsDialog(self):
        """ shows a search widget """
        pass


    @QtSlot()
    def activateRTKDialog(self):
        """ shows a search widget """
        pass


    @QtSlot()
    def activeiceDialog(self):
        setICE = setupEnv()
        setICE.exec()

    
    @QtSlot(str)
    def changeTable(self, table_name):
        try:
            self._dbmanage.changeTable(table_name)
            self.rtkToolBox.db_tab.database.changeTable(table_name)
        except Exception as e:
            logger.exception("Exception occurred while changing the table")


    ################
    # (Un)marshall #
    ################

    def marshall(self):
        """ returns a dictionary to save in the persistent settings. """

        self._storeInspectorState(self.inspectorRegItem, self.inspector)
        cfg = dict(
            configWidget=self.configWidget.marshall(),
            curInspector=self.inspectorRegItem.idntifier if self.inspectorRegItem else '',
            inspectors=self._inspectorStates,
        )
        return cfg
    
    
    def unmarshall(self, cfg, evaluator):
        """ initializes itself from a config dict from the persistent settings. """

        self.rtkMenuBar.unmarshall(cfg.get('menuBar', {}))
        self._Urls = cfg.get('Urls', {})

        # setup rtkMenuBar & rtkToolBar
        self._setupMenuBar() # depraction: self._setupToolBar()

        # unmarshall on the evaluator instance
        self.evaluator.unmarshall(cfg, evaluator=evaluator)

        layoutCfg = cfg.get('layout', {})
        if 'winGeom' in layoutCfg:
            self.restoreGeometry(base64.b64decode(layoutCfg['winGeom']))
        if 'winState' in layoutCfg:
            self.restoreState(base64.b64decode(layoutCfg['winState']))

        # should not be placed here!
        if self.evaluator.evaluatorRegItem: # can be None at start
            evaluatorId = self.evaluator.evaluatorRegItem.identifier
            self.evaluator.getEvaluatorActionById(evaluatorId).setChecked(True)
        else:
            logger.info(f"{self.__repr__()}:addNewMainWindow> adding a new main window with NO inspector.")




class CentralWidget(QtWidgets.QWidget):
    """ Will be split into 2 panes, 
        left for animated navigation bar, right for detailed functions and display.

        updates: moved toolBox and etc., some necessary to the mainWindow for better communications.
    """
    def __init__(self, parent=None):
        super(CentralWidget, self).__init__(parent)

        self._rtkWin = parent

        # split rtkMainWindow horizontally into 2 panes.
        # setup background color
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(255, 255, 255))
        self.setPalette(p)

        self._initLeftPane()
        self._initRightPane()

        self.spliter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.spliter.addWidget(self.leftPane)
        self.spliter.addWidget(self.rightPane)

        self.spliter.setSizes([300, 800])

        hbox = QtWidgets.QHBoxLayout(self)
        hbox.addWidget(self.spliter)
        self.setLayout(hbox)


    def _initLeftPane(self):
        """ initialize the left pane, which basically is the animated navigation bar. """
        self.leftPane = QtWidgets.QWidget()
        self.leftPaneLayout = QtWidgets.QVBoxLayout()

        self.verticalSpacer = QtWidgets.QSpacerItem(50, 10, 
            QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        
        self.leftPaneLayout.addWidget(self.rtkWin.rtkToolBox)
        self.leftPane.setLayout(self.leftPaneLayout)
        self.leftPane.setMinimumSize(400, 400) 


    def _initRightPane(self):

        self.rightPane = QtWidgets.QWidget()
        self.rightPaneLayout = QtWidgets.QVBoxLayout(self.rightPane)
        self.rightPaneLayout.addWidget(self.rtkWin.wrapperWidget)


    @property
    def rtkWin(self):
        return self._rtkWin


