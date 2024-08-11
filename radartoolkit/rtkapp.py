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


""" RadarToolKit (ISR) Application Instance.
"""


from __future__ import print_function

import copy
import json
import logging
import os.path
import sys
from datetime import datetime


from info import (EXIT_CODE_SUCCESS, PROJECT_NAME, VERSION, KEY_VERSION,\
                  KEY_VERSION, KEY_PROGRAM)

from display.rtkwin import MainWindow, UpdateReason
from display.bindings import QtCore, QtWidgets, QtSlot, QtGui
from display.evaluator.registry import EvaluatorRegistry, DEFAULT_EVALUATOR
from display.utils.misc import initQApplication, handleException
from display.color.colors import CmLibSingleton, DEF_FAV_COLOR_MAPS
from display.rti.registry import globalFileRegistry
from display.rti.filetreemodel import FileTreeModel
from display.utils.dirs import rtkConfigDirectory, normRealPath, checkFileExists
from display.utils.moduleinfo import versionStrToTuple
from display.settings import CONFIG_FILE, DEFAULT_FUNCS


logger = logging.getLogger(__name__)

curFileName = os.path.basename(__file__)


def _updateConfig(cfg):
    """ 
    Updates the config/settings dict file for the new lauched interface afrer an update. 
    """
    curFuncName = sys._getframe().f_code.co_name

    msg = "<{}::{}>".format(curFileName, curFuncName)
    logger.debug("{}: called, updates the config dict.".format(msg))
    
    if not cfg: # the config dict may be empty, e.g. when the first time the application starts
        logger.debug("{}: empty config file, returning.".format(msg))
        return cfg
    cfg = copy.deepcopy(cfg)

    cfgVersion = versionStrToTuple(cfg.get(KEY_VERSION, '1.0.0'))[0:3]
    appVersion = versionStrToTuple(VERSION)[0:3]

    if cfgVersion >= appVersion:
        logger.info("{}: config file version {} >= app version {}, will use config as-is."
                    .format(msg, cfgVersion, appVersion))
        return cfg
    else:
        logger.info("{}: config file version {} < app version {}, updading the config file to a new version."
                    .format(msg, cfgVersion, appVersion))
        assert appVersion > cfgVersion, "Sanity check"

    return cfg


_Q_APP = None # keep reference to the QApplication instance. Global variable.
def qApplicationSingleton() -> QtWidgets.QApplication:
    """ returns the QApplication instance. creates if not exists."""
    global _Q_APP

    qApp = QtWidgets.QApplication.instance()
    if qApp is None:
        logger.debug("<{}::{}>: QApplication instance not exists, creating."
                     .format(curFileName, sys._getframe().f_code.co_name))
        _Q_APP = qApp = QtWidgets.QApplication([])
    return qApp



class RTKApplication(QtCore.QObject):
    """ The application singleton which holds the global variables and states. 
    """

    def __init__(self, settingsFile=None, inspectorFullName=None, registeredFiles={}, setExceptHook=True):
        """ Constructor

            :param settingsFile:      Config file from which the persistent settings are loaded.
            :param inspectorFullName: Name of the inspector which will be loaded later on.
            :param fileRegistry:      Directly initializes operations from the beginning on.
            :param setExceptHook:     Sets the global sys.except hook so that Qt shows a dialog box
                                      when an exception is raised.
        """
        super(RTKApplication, self).__init__()

        if not settingsFile:
            key, val = RTKApplication.defaultSettingsFile()
            logger.debug(f"{self.__repr__()}:__init__> no conifg file specified. "
                         f"Using {val}({key})")
        self._settingsFile = val
    
        if setExceptHook:
            logger.debug(f"{self.__repr__()}:__init__> setting "
                         "sys.excepthook({setExceptHook}) for rtk exception handling.")
            sys.excepthook = handleException
        QtCore.qInstallMessageHandler(self.handleQtLogMessages)

        self._fileTreeModel = FileTreeModel()
        self._fileRegistry = globalFileRegistry()
        self._evaluatorRegistry = EvaluatorRegistry()

        self._mainWindows = []
        self._settingsSaved = False # boolean to prevent saving settings twice
        self._recentFiles = []      # list of recently opened files ([timeStamp, fileName, rtiItemType] per file)
        self._maxRecentFiles = 20   # maximum number of the recent files

        self.qApplication.aboutToQuit.connect(self.aboutToQuitHandler)

        # activate-actions for the all main/sub windows
        self.windowActionGroup = QtGui.QActionGroup(self)
        self.windowActionGroup.setExclusive(True)

        # can be called as many times as requred
        self._registeredFiles = registeredFiles
        self.loadRegisteredFiles()

        # call setup when the event loop starts
        QtCore.QTimer.singleShot(0, self.onEventLoopStarted)


    def onEventLoopStarted(self):
        """ called as soon as the event loop has started """
        logger.debug(f"{self.__repr__()}:__onEventLoopStarted> called.")
        actions = self.windowActionGroup.actions()
        if actions:
            actions[0].trigger()


    def __repr__(self) -> str:
        return f"<{curFileName}:{type(self).__name__}"
        

    #################
    # Class Methods #
    #################

    @classmethod
    def defaultSettingsFile(cls) -> dict:
        """ returns the default settings config file """
        if not checkFileExists(CONFIG_FILE):
            # check the baseConfigDirectory
            DEFAULT_SETTING_PATH = os.path.join(rtkConfigDirectory(), "rtk.json")
            if not checkFileExists(DEFAULT_SETTING_PATH):
                return 'USR-DEFINED', normRealPath(cls.usrProvidedSettingsFile())
            return 'DEFAULT', normRealPath(DEFAULT_SETTING_PATH)
        return 'CURRENT', normRealPath(CONFIG_FILE)
    

    @classmethod
    def usrProvidedSettingsFile(cls) -> str:
        """ Asks the user to provide the settings file since no file given.
            In this case, the provided file will be copied to the DEFAULT & CURRENT folder for further usage.
        """
        _app = qApplicationSingleton() # make sure the QApplication exists.
        answer = QtWidgets.QMessageBox.question(
            None, "Attach new settings file",
            "The settings file for launching {} cannot be found."
            "\n\n"
            "Please attach a new settings file.".format(PROJECT_NAME))
        if answer == QtWidgets.QMessageBox.Yes:
            pass
        else:
            exit(1)


    @classmethod
    def handleQtLogMessages(cls, qMsgType, context, msg) -> None:
        """ Forwards Qt log message to the Python log system.
            
            This ensures that they end up in application log files instead of just being printed to
            stderr at application exit.

            This function must be installed with QtCore.qInstallMessageHandler.
            See https://doc.qt.io/qt-5/qtglobal.html#qInstallMessageHandler
        """
        if qMsgType == QtCore.QtMsgType.QtDebugMsg:
            logger.debug(msg)
        elif qMsgType == QtCore.QtMsgType.QtInfoMsg:
            logger.info(msg)
        elif qMsgType == QtCore.QtMsgType.QtWarningMsg:
            logger.warning(msg)
        elif qMsgType == QtCore.QtMsgType.QtCriticalMsg:
            logger.error(msg)
        elif qMsgType == QtCore.QtMsgType.QtFatalMsg:
            logger.error(msg)
        else:
            logger.critical("Qt message of unknown type {}: {}".format(qMsgType, msg))


    ##############
    # Properties #
    ##############

    @property
    def qApplication(self) -> QtWidgets.QApplication:
        """ equivalent to QtWidgets.QApplication.instance() or directly call qApp (global variable) 
            :: For testing purposes, get rid of the application by simply calling qApp.shutdown()
        """
        global _Q_APP

        qApp = QtWidgets.QApplication.instance()
        if qApp is None:
            logger.debug(f"{self.__repr__()}:qApplication> qApp not exists, creating.")
            _Q_APP = qApp = initQApplication()
        return qApp
    
    
    @property
    def fileRegistry(self):
        return self._fileRegistry
    

    @property
    def evaluatorRegistry(self):
        return self._evaluatorRegistry
    

    @property
    def fileTreeModel(self):
        return self._fileTreeModel
    

    @property
    def registeredFiles(self):
        return self._registeredFiles
    

    @property
    def maxRecentFiles(self):
        return self._maxRecentFiles
    

    @property
    def mainWindows(self):
        return self._mainWindows
    
    
    @property
    def nWindow(self):
        """ returns the number of the mainWindow """
        return len(self._mainWindows)
    

    @property
    def settingsSaved(self):
        """ returns the boolean logic to prevent saving settings twice """
        return self._settingsSaved
    
    
    @property
    def settingsFile(self):
        return self._settingsFile
    

    ##############
    #   Methods  #
    ##############

    def marshall(self):
        """ returns a dictionary to save in the persistent settings """
        logger.debug(f"{self.__repr__()}:marshall> called, save any persistent settins in the dict.")
        
        cfg = {}
        cfg[KEY_PROGRAM] = PROJECT_NAME
        cfg[KEY_VERSION] = VERSION

        # save colormap-related favorites 
        cmLib = CmLibSingleton.instance() # colormap favorites
        cfg['cmFavorites'] = [colorMap.key for colorMap in cmLib.color_maps
                              if colorMap.meta_data.favorite]
        
        # save recent files settings 
        cfg['recentFiles'] = self._recentFiles

        # save plugins
        cfg['plugins'] = {}
        cfg['plugins']['inspectors'] = self.evaluatorRegistry.marshall()
        cfg['plugins']['file-supported'] = self.fileRegistry.marshall()

        # save windows in the config dictionary
        cfg['windows'] = {}
        for winNr, mainWindow in enumerate(self.mainWindows):
            key = "win-{:d}".format(winNr)
            cfg['windows'][key] = mainWindow.marshall()
        
        return cfg
    
    
    def unmarshall(self, cfg, evaluator):
        """ 
        Initializes itself from a config diction from the persistent settings.

        :param inspectorFullName: a window with the specified inspector is created.
        If an inspector window with this inspector is created from the config file, this parameter will be ignored.
        """

        cmLib = CmLibSingleton.instance()
        if not cmLib.color_maps:
            logger.warning(f"{self.__repr__()}:unmarshall> called, "
                        f"no color maps loaded yet. Favorites will be empty.")
        
        favKeys = cfg.get('cmFavorites', DEF_FAV_COLOR_MAPS)
        for colorMap in cmLib.color_maps:
            colorMap.meta_data.favorite = colorMap.key in favKeys

        self._recentFiles = cfg.get('recentFiles', [])

        pluginCfg = cfg.get('plugins', {})
        self.evaluatorRegistry.unmarshall(pluginCfg.get('evaluators', {}))
        self.fileRegistry.unmarshall(pluginCfg.get('file-formats', {}))

        if evaluator is not None:
            logger.debug(f"{self.__repr__()}:unmarshall> no evaluator detected, using the default ({DEFAULT_EVALUATOR})")
            evaluator = DEFAULT_EVALUATOR

        logger.debug(f"{self.__repr__()}:unmarshall> initializing new window with evluator: {evaluator}")
        
        for winId, winCfg in cfg.get('windows', {}).items():
            assert winId.startswith('win-'), "Win ID doesn't start with 'win-': {}".format(winId)
            self.addNewMainWindow(cfg=winCfg, evaluator=evaluator)
            break

        
    def saveSettings(self):
        """ saves the persistent settings to file (*.json) """
        try:
            if not self._settingsFile:
                logger.info(f"{self.__repr__()}:saveSettings> no settings file specified. " 
                            f"Not saving persistent state.")
            else:
                logger.info(f"{self.__repr__()}:saveSettings> saving settings to: {self._settingsFile}.")
                settings = self.marshall()
                try:
                    jsonStr = json.dumps(settings, sort_keys=True, indent=4)
                except Exception as ex:
                    logger.error(f"{self.__repr__()}:saveSettings> failed to serialize settings to JSON: {ex}.")
                    logger.error(f"{self.__repr__()}:saveSettings> no settings file specified. Not saving persistent state.")
                    raise
                else:
                    with open(self._settingsFile, 'w') as fd:
                        fd.write(jsonStr)
        except Exception as ex:
            logger.error(f"{self.__repr__()}:saveSettings> failed: {ex}.")
        finally:
            self._settingsSaved = True


    def loadSettings(self, evaluator):
        """ 
        Loads the settings from file and populates the application object from it.

        Will update the config (and make a backup of the config file) if the version number
        has changed.

        :param evaluator: If not None, a window with this evaluator is created.
            If an evaluator window with this evaluator is created from the config file, this
            parameter is ignored.
        """
        if not checkFileExists(self._settingsFile):
            logger.warning(f"{self.__repr__()}:loadSettings> settings file not exists: {self._settingsFile}.")
        try:
            with open(self._settingsFile, 'r') as fd:
                jsonStr = fd.read()

            if jsonStr:
                cfg = json.loads(jsonStr)
            else:
                cfg = {}
        except Exception as ex:
            logger.error(f"{self.__repr__()}:loadSettings> error ({ex}) occured while loading settings file.")
            raise # in case of a syntax error it's probably best to exit.
        
        cfg = _updateConfig(cfg)
        self.unmarshall(cfg, evaluator)


    def raiseSaveSettings(self):
        """ writes the persistent settings if it's the only windows and the settings havenot been set yet """
        if not self._settingsSaved and len(self.mainWindows) <= 1:
            self.saveSettings()


    def loadRegisteredFiles(self):
        """ 
        Loads files into the repository as file tree items of class rtiClass.
        Auto-detects using the extensions when rtiClass is None

        :param filePatterns: list of file names or unix like file expansions (globs),
            For example filePatterns = ['my_file.nc, 'your_file.nc']
            For example filePatterns = ['*.h5']
        """
        if not isinstance(self.registeredFiles, dict):
            return
        else:
            if self.registeredFiles.keys() not in DEFAULT_FUNCS:
                return
            else:
                # load registered starts here ...
                for fileName in self.registeredFiles.values():
                    self.fileTreeModel.loadFile(fileName, rtiRegItem=None)


    def getRecentFiles(self):
        """ adds the files to the list of recently opened files """
        return self._recentFiles
    
    
    def addToRecentFiles(self, fileNames, rtiRegItemName):
        """ adds the files to the list of the recently added files """
        # use the timestamp for sorting so we can store it as a string. Easy to (un)marshall.
        timeStamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # list of recently opened files: (fileName, timeStamp, rtiRegItemName) per file
        recentItems = [(item[1], item[2]) for item in self._recentFiles]

        for fileName in fileNames:
            try:
                existingIndex = recentItems.index((fileName, rtiRegItemName))
            except ValueError:
                self._recentFiles.append([timeStamp, fileName, rtiRegItemName])
            else:
                # Only update timestamp if item is already in de list.
                self._recentFiles[existingIndex][0] = timeStamp

        self._recentFiles.sort(reverse=True)
        self._recentFiles = self._recentFiles[0:self._maxRecentFiles]
    

    ##############
    #    Slot    #
    ##############

    @QtSlot()
    def addNewMainWindow(self, cfg, evaluator=None):
        """ Creates and shows a new MainWindow.

            If inspectorFullName is set, it will set the identifier from that name.
            If the inspector identifier is not found in the registry, a KeyError is raised.
        """
        logger.debug(f"{self.__repr__()}:addNewMainWindow> called.")
        
        mainWindow = MainWindow(self, identifier=evaluator)
        self._mainWindows.append(mainWindow)

        if cfg is not None:
            mainWindow.unmarshall(cfg, evaluator)
        mainWindow.show()

        if sys.platform.startswith('darwin'):
            mainWindow.raise_()
            pass
        return mainWindow
    
    
    def removeMainWindow(self, mainWindow):
        """ Removes the mainWindow from the list of windows. Saves the settings
        """
        logger.debug(f"{self.__repr__()}:removeMainWindow> called, "
                     f"removing the mainWindow({hex(id(mainWindow))}).")

        self.windowActionGroup.removeAction(mainWindow.activateWindowAction)
        self.repopulateAllWindowMenus()
        self.mainWindows.remove(mainWindow)

    def exit(self, exitCode):
        """ saves settings and exits the program with a certain exit code """
        self.saveSettings()
        self.qApplication.closeAllWindows()
        self.qApplication.exit(exitCode)
    
    def quit(self):
        """ exit with code 0 (sucess) """
        self.exit(EXIT_CODE_SUCCESS)

    def aboutToQuitHandler(self):
        """ called by Qt when the application is quitting """
        logger.debug(f"{self.__repr__()}:aboutToQuitHandler> called by Qt, rtk is about to quit.")
    
    def execute(self):
        logger.debug(f"{self.__repr__()}:aboutToQuitHandler> called, starting rtk ...")
        exitCode = self.qApplication.exec_()
        logger.debug(f"{self.__repr__()}:aboutToQuitHandler> called, rtk finished with exit code: {exitCode}")
        return exitCode





            
                    
                




