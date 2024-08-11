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
    Data Evaluator Module.
"""


import logging
from functools import partial

from display.bindings import QtWidgets, QtCore, QtSignal, QtSlot, QtGui
from display.config.configtreeview import ConfigWidget
from display.config.configtreemodel import ConfigTreeModel
from display.evaluator.abstract import UpdateReason, AbstractInspector
from ..widgets.misc import setWidgetSizePolicy
from display.utils.check_class import check_class
from .selectionpane import SelectionPane


logger = logging.getLogger(__name__)



class Evaluator(QtWidgets.QWidget):

    DEFAULT_ACTIONS = {"Parameters": 0, "Configurations": 1}

    sigEvaluatorChanged = QtSignal(object)
    sigShowMessage = QtSignal(str)


    def __init__(self, 
                 fileHub, 
                 collector,
                 identifier="imageplot2d", 
                 registy=None,
                 actions=None, 
                 parent=None):
        super(Evaluator, self).__init__(parent=parent)

        self._identifier = identifier
        self._fileHub = fileHub
        self._registry = registy
        self._collector = collector
        self._actionsGroup = actions
        self.activeEvaluator = None

        # initialize the `Evualtor` selection pane
        self.selectionPane = SelectionPane(self.actionsGroup)

        # evaluator 
        self.evaluator = None
        self.evaluatorRegItem = None # the registered inspector item, class: `evaluatorRegItem` 
        self.evaluatorStates = {}

        # evaluatorID = nameToIdentifier(identifier)
        # self._updateEvaluator(evaluatorID)

        # configurations viewer: automatically unmarshall according to the identifier
        self.configTreeModel = ConfigTreeModel()
        self.configViewer = ConfigWidget(self.configTreeModel)       
         

        # setup the interface
        self._setupPlotsMenuActions(self)
        self._initView()

        # --- signal-slot connection ---
        # self.sigShowMessage.disconnect(self.showMessage)
        self.collector.sigContentsChanged.connect(self.onContentsChanged)
        self.collector.sigShowMessage.connect(self.showMessage)

        self.configTreeModel.sigItemChanged.connect(self.onContentsChanged)
        self.sigEvaluatorChanged.connect(self.selectionPane.updateFromEvalutaor)


    @property
    def fileHub(self):
        return self._fileHub
    

    @property
    def registry(self):
        return self._registry
    

    @property
    def collector(self):
        return self._collector
    

    @property
    def actionsGroup(self):
        return self._actionsGroup
    

    @property
    def paramsViewer(self):
        return self.collector.paramsViewer
    

    ###################
    #     Methods     #      
    ###################

    def finalize(self):
        """
        Called before destruction when it's closing to clean up the resouces.
        """

        self.collector.sigContentsChanged.disconnect(self.onContentsChanged)
        self.collector.sigShowMessage.disconnect(self.showMessage)

        self.configTreeModel.sigItemChanged.disconnect(self.onContentsChanged)
        self.sigEvaluatorChanged.disconnect(self.selectionPane.updateFromEvalutaor)


    def _setupPlotsMenuActions(self, parent):
        """
        Sets up Actions.
        """
        plotsMenuActionsGroup = QtGui.QActionGroup(parent)
        plotsMenuActionsGroup.setExclusive(True)

        for item in self.DEFAULT_ACTIONS.keys():
            func = partial(self._flipRightPane, item)
            action = QtGui.QAction(item, self, triggered=func, checkable=True)
            action.setData(item)
            plotsMenuActionsGroup.addAction(action)

        self.plotsMenuActionsGroup = plotsMenuActionsGroup
        

    def _initView(self):
        """
        Initialize the interface.
        """        
        # add a group to organize the buttons for the evaluator further actions.
        self.buttonGroup = QtWidgets.QButtonGroup(self)
        self.buttonGroup.setExclusive(True)
        self.buttonGroup.buttonClicked.connect(self.onBtnClicked)

        # setup the evaluator view-related buttons
        self.plot1Btn = QtWidgets.QRadioButton("Plot 1")
        self.plot1Btn.setEnabled(self.activeEvaluator is not None)
        self.plot2Btn = QtWidgets.QRadioButton("Plot 2")
        self.plot2Btn.setEnabled(self.activeEvaluator is not None)

        setWidgetSizePolicy(self.plot1Btn, hor=QtWidgets.QSizePolicy.Minimum) 
        setWidgetSizePolicy(self.plot2Btn, hor=QtWidgets.QSizePolicy.Minimum) 

        self.buttonGroup.addButton(self.plot1Btn, 1)
        self.buttonGroup.addButton(self.plot2Btn, 2)

        # Q-stacked widget for 2 plots pane
        self.stackedViewers = QtWidgets.QStackedWidget()
        self.stackedViewers.addWidget(self.paramsViewer)
        self.stackedViewers.addWidget(self.configViewer)

        # setup the config widgets
        self.plotsMenuBtn = QtWidgets.QPushButton('< None >')
        self.plotsMenuBtn.setMinimumWidth(30)
        self.plotsMenuBtn.setEnabled(False)

        plotsMenu = QtWidgets.QMenu("Choose Evaluator", parent=self.plotsMenuBtn)
        for action in self.plotsMenuActionsGroup.actions():
            plotsMenu.addAction(action)
        self.plotsMenuBtn.setMenu(plotsMenu)

        self.plotsMenuBtn.setText("Parameters")
        self.plotsMenuActionsGroup.actions()[self.DEFAULT_ACTIONS["Parameters"]].setChecked(True)


        # --- layout decoration and organization ---
        self.topPane = QtWidgets.QFrame()
        self.vLayout = QtWidgets.QVBoxLayout(self.topPane)
        self.vLayout.setContentsMargins(0, 0, 0, 0)
        self.vLayout.setSpacing(0)

        # top horizontal layout
        hLayout = QtWidgets.QHBoxLayout()
        hLayout.setContentsMargins(5, 0, 2, 0)

        hLayout.addWidget(self.selectionPane)
        hLayout.addWidget(self.plot1Btn)
        hLayout.addWidget(self.plot2Btn)
        hLayout.addWidget(self.plotsMenuBtn)
        
        self.vLayout.addLayout(hLayout)
        # self.vLayout.addWidget(self.evaluator) # segmentation fault: None


        self.horSplitter = QtWidgets.QSplitter()
        self.horSplitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horSplitter.addWidget(self.topPane)
        self.horSplitter.addWidget(self.stackedViewers)

        self.verPaneLayout = QtWidgets.QVBoxLayout(self)
        self.verPaneLayout.setContentsMargins(0, 0, 0, 0)
        self.verPaneLayout.setSpacing(0)

        self.verPaneLayout.addWidget(self.horSplitter)
        self.verPaneLayout.addWidget(self.collector)


    def _getEvaluatorActions(self):
        if hasattr(self, "evaluatorActionGroup"):
            return self.evaluatorActionGroup
        else:
            return None
    

    def _updateEvaluator(self, identifier):
        """ 
        Sets the `Evaluator` and draw the contents.
        """
        self._setupEvaluatorById(identifier)

        regItem = self.evaluatorRegItem
        if regItem and not regItem.successfullyImported:
            msg = "Unable to import {} inspector. \n{}" \
                .format(regItem.identifier, regItem.exception)
            QtWidgets.QMessageBox.warning(self, "Warning", msg)
            logger.warning(msg)

        self._drawEvaluatorContents(reason=UpdateReason.INSPECTOR_CHANGED)


    def _setupEvaluatorById(self, identifier):
        """ 
        Sets the central inspector widget given a inspector ID.

        If identifier is None, the inspector will be unset. Otherwise it will lookup the
        inspector class in the registry. It will raise a KeyError if the ID is not found there.

        It will do an import of the inspector code if it's loaded for the first time. If the
        the inspector class cannot be imported a warning is logged and the inspector is unset.

        NOTE: does not draw the new inspector, this is the responsibility of the caller.
        Also, the corresponding action is not triggered.

        Emits the sigInspectorChanged(self.inspectorRegItem)
        """
        logger.debug(f"{self.__repr__()}:_setupEvaluator> called, setting evaluator: {identifier}")

        # use the identifier to find a registered evaluator and 
        # set the self.insepctorRegItem as what it is and creates an object from it.
        oldEvaluatorRegItem = self.evaluatorRegItem
        oldEvaluator = self.evaluator
        evaluator, errMsg = None, None

        if not identifier:
            errMsg = "No evaluator selected and detected. Please select one from the menu."
            self._evaluatorRegItem = None
        else:
            evaluatorRegistry = self.registry
            evaluatorRegItem = evaluatorRegistry.getItemById(identifier)
            self.evaluatorRegItem = evaluatorRegItem

            if self.evaluatorRegItem is None:
                logger.warning(f"{self.__repr__()}:_setupEvaluatorById> No {identifier} evaluator found. "
                               f"Please select one from menu.")
                
            else:
                try:
                    """ creates a current inspector instance from the inspectorRegItem """
                    evaluator = evaluatorRegItem.create(self.collector, tryImport=True)
                except ImportError as ex:
                    logger.warning(f"{self.__repr__()}:_setupEvaluatorById> "
                                   f"Unable to create {evaluatorRegItem.identifier} inspector because {ex}")
                    self.getEvaluatorActionById(identifier).setEnabled(False)

        # --- setup the inspector --- #
        check_class(evaluator, AbstractInspector, allow_none=True)

        self.setUpdatesEnabled(False)
        # try:
            # delete the old inspector
        self._storeEvaluatorState(oldEvaluatorRegItem, oldEvaluator)

        # disconnect the signal
        if isinstance(oldEvaluator, AbstractInspector):
            oldEvaluator.finalize()
            self.vLayout.removeWidget(oldEvaluator)
            oldEvaluator.deleteLater()

        # setup the new inspector
        oldBlockState = self.collector.blockSignals(True)

        self.evaluator = evaluator

        # add and apply the config values to the inspector
        key = self.evaluatorRegItem.identifier
        cfg = self.evaluatorStates.get(key, {})
        self.evaluator.config.unmarshall(cfg)
        self.configTreeModel.setInvisibleRootItem(self.evaluator.config)
        self.collector._clearAndSetAll(self.evaluator.axesNames())

        # local message receiver connection
        self.evaluator.sigShowMessage.connect(self.showMessage)
        self.vLayout.addWidget(self.evaluator)

        self.collector.blockSignals(oldBlockState)
        self.setUpdatesEnabled(True)
        logger.debug(f"{self.__repr__()}:setEvaluatorById> emitting signal: "
                        f"sigEvaluatorChanged ({self.evaluatorRegItem})")
        self.sigEvaluatorChanged.emit(self.evaluatorRegItem)


    def getEvaluatorActionById(self, identifier):
        """ 
        Sets the inspector and draw the contents.
        Triggers the conrresponding action.
        """
        for action in self.actionsGroup.actions():
            if action.data() == identifier:
                return action
        raise KeyError("No action found with ID: {!r}".format(identifier))
    

    def _storeEvaluatorState(self, evaluatorRegItem, evaluator):
        """ 
        Store the settings values for the current evaluator in a local dictionary.
        This dictionary is later used to store value for persistence.

        This function must be called after the inspector was drawn because that may update
        some derived config values (e.g. ranges)
        """
        if evaluatorRegItem and evaluator:
            key = evaluatorRegItem.identifier
            self.evaluatorStates[key] = evaluator.config.marshall()
            logger.debug(f"{self.__repr__()}::_storeEvaluatorState>: the settings values {key}-{type(evaluator)} are stored successfully.")
            
        else:
            logger.debug(f"{self.__repr__()}::_storeEvaluatorState>: no evaluator.")


    def _drawEvaluatorContents(self, reason, origin=None): 
        """ 
        Draws all the contents of this window's inspector. 
        """
        logger.debug(f"{self.__repr__()}:_drawEvaluatorContents> "
                     f"called to draw the evaluator contents ({reason}).")

        # this is the moment when it's about to draw the contents
        self.evaluator.updateContents(reason=reason, initiator=origin) 
        logger.debug(f"{self.__repr__()}:_drawEvaluatorContents> finished drawing.")


    def unmarshall(self, cfg, evaluator=None):

        self.configViewer.unmarshall(cfg.get('configWidget', {}))
        self.evaluatorStates = cfg.get('inspectors', {})
        
        evaluator = cfg.get('curInspector') if evaluator is None else evaluator
        if evaluator:
            self._setupEvaluatorById(evaluator)
            self._drawEvaluatorContents(reason=UpdateReason.NEW_MAIN_WINDOW)

        layoutCfg = cfg.get('layout', {})
        self.configViewer.configTreeView.unmarshall(layoutCfg.get('configTreeHeaders', ''))


    ###################
    #      Slot      #      
    ###################

    @QtSlot(str)
    def showMessage(self, msg):
        self.sigShowMessage.emit(msg)


    @QtSlot(str, object)
    def onContentsChanged(self, reason, origin=None):
        """ 
        Slot that receives information when the contents 
        from the collector or the config.
        When received then re-draw the evaluator's contents.

        # updates from the config:
        self.drawInspectorContents(
            reason=UpdateReason.CONFIG_CHANGED, origin=configTreeItem(AbstractCti/configTreeItem))

        # updates from the collector:
        self.drawInspectorContents(reason=reason)
        """
        logger.debug(f"{self.__repr__()}:onContentsChanged> called, drawing contents in the evaluator ...")
        self._drawEvaluatorContents(reason=reason, origin=origin)
        

    @QtSlot()
    def _flipRightPane(self, paneName):
        """
        Flips the right pane.
        """
        self.stackedViewers.setCurrentIndex(self.DEFAULT_ACTIONS[paneName])
        self.plotsMenuBtn.setText(paneName)


    @QtSlot()
    def onBtnClicked(self):
        pass
        
