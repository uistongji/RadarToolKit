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


import logging
import os

from ..bindings import QtWidgets, QtCore, QtGui, QtSlot, Qt
from ..utils.constants import MONO_FONT, FONT_SIZE
from ..utils.check_class import check_class
from ..settings import DOCK_MARGIN, ICONS_DIR
from ..reg.tabmodel import TableInfoModel
from ..reg.tabview import TableInfoViewer
from ..config.configtreeview import ConfigTreeView
from ..config.configtreemodel import ConfigTreeModel
from ..widgets.basepanel import BasePanel


logger = logging.getLogger(__name__)


class CollectorSpinBox(QtWidgets.QSpinBox):
    """ A spinBox for use in the collector, for displaying.
    """

    def __init__(self, *args, **kwargs):

        super(CollectorSpinBox, self).__init__(*args, **kwargs)
        self._cachedSizeHint = None


    def sizeHint(self):
        """ 
        Reimplemented from the C++ Qt source of QAbstractSpinBox.sizeHint, but without
        truncating to a maximum of 18 characters.
        """
        # The cache is invalid after the prefix, postfix and other properties
        # have been set. I disabled it because sizeHint isn't called that often.
        #if self._cachedSizeHint is not None:
        #    return self._cachedSizeHint

        orgSizeHint = super(CollectorSpinBox, self).sizeHint()
        self.ensurePolished()
        h = orgSizeHint.height()
        result = QtCore.QSize(90, h)
        return result
        


class InfoDialog(QtWidgets.QDialog):
    """ Dialog window shows the collector related information
    """
    def __init__(self, config=None, parent=None, _histories=[]):
        super(InfoDialog, self).__init__(parent=parent)

        self._config = config
        self._histories = _histories

        self.resize(QtCore.QSize(800, 600))

        # setup the window title
        self.setWindowTitle("More Of Collector")
        # self.setWindowTitle(f"{PROJECT_NAME} (-v {VERSION}) | More Of Collector")
        layout = QtWidgets.QHBoxLayout(self)

        # setup the detailed information widget
        font = QtGui.QFont()
        font.setFamily(MONO_FONT)
        font.setFixedPitch(True)
        font.setPointSize(FONT_SIZE)

        self.editor = QtWidgets.QTextEdit()
        self.editor.setReadOnly(True)
        #self.editor.setFocusPolicy(Qt.NoFocus) # Allow focus so that user can copy text from it.
        #self.editor.setFont(font)
        self.editor.setWordWrapMode(QtGui.QTextOption.WordWrap)
        self.editor.clear()

        # setup the main view
        self._tableModel = TableInfoModel(self._histories)
        self.tableView = TableInfoViewer(self._tableModel)
        # self.tableView = QtWidgets.QTableWidget() # to diplay the information, requires parsing
        
        self.colConfigWidget = ParamsWidget()
        self.colConfigWidget._configTreeModel.setInvisibleRootItem(self._config)

        self.saveBtn = QtWidgets.QPushButton("Save")
        self.saveBtn.clicked.connect(self.accept)

        self.cancelBtn = QtWidgets.QPushButton("Cancel")
        self.cancelBtn.clicked.connect(self.reject)

        # We use a button layout instead of a QButtonBox because there always will be a default
        # button (e.g. the Save button) that will light up, even if another widget has the focus.
        # From https://doc.qt.io/archives/qt-4.8/qdialogbuttonbox.html#details
        #   However, if there is no default button set and to preserve which button is the default
        #   button across platforms when using the QPushButton::autoDefault property, the first
        #   push button with the accept role is made the default button when the QDialogButtonBox
        #   is shown,

        self.btnsLayout = QtWidgets.QHBoxLayout()
        self.btnsLayout.addWidget(self.cancelBtn)
        self.btnsLayout.addWidget(self.saveBtn)

        # layout of the right pane
        vrlayout = QtWidgets.QVBoxLayout()
        vrlayout.addWidget(self.colConfigWidget)
        vrlayout.addLayout(self.btnsLayout)

        # layout of the left pane
        vllayout = QtWidgets.QVBoxLayout() 
        vllayout.addWidget(self.tableView)
        vllayout.addWidget(self.editor)

        layout.addLayout(vllayout)
        layout.addLayout(vrlayout)

        # --- connect signal-slot --- #
        self.tableView.selectionModel().currentChanged.connect(self.currentItemChanged)
        self.tableView.model().sigItemChanged.connect(self._updateEditor)

        self.tableView.setFocus(QtCore.Qt.NoFocusReason)


    def __repr__(self) -> str:
        return f"<{type(self).__name__}"
    

    def accept(self):
        """ Saves changes of the parameters, e.g., processing, roi, ...
        """
        logger.debug(f"{self.__repr__()}:accept> called. Updating from the changes.")
        pass


    def getCurrentRegItem(self):
        """ Returns the item that is currently selected in the table.
            Can return None if there is no data in the table
        """
        return self.tableView.getCurrentItem()
    

    @QtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def currentItemChanged(self, currentIndex=None, _previousIndex=None):
        """ Updates the description text widget when the user clicks on a selector in the table.
            The _currentIndex and _previousIndex parameters are ignored.
        """
        regItem = self.getCurrentRegItem()
        self._updateEditor(regItem)

    
    # @QtSlot()
    def _updateEditor(self, infoItem=None):
        """ Updates the editor with contents of the currently selected information
        """
        self.editor.clear()

        if infoItem is None:
            return
        else:
            header = "<h3>{}</h3>".format(infoItem._headerText)
            self.editor.setHtml("{}{}<br>{}".\
                format(header, infoItem._statusTexts, infoItem._detailedTexts))



class ParamsWidget(BasePanel):
    """ 
    Shows the processing parameters widget, esepcially for the basic config & processing.
    """

    def __init__(self, parent=None):
        super(ParamsWidget, self).__init__(parent=parent)

        self._configTreeModel = ConfigTreeModel()
        self.colConfigView = ConfigTreeView(self._configTreeModel, parent=self)
        
        # setup reset2Default (r2d) button
        self.r2dBtn = QtWidgets.QPushButton(
            QtGui.QIcon(os.path.join(ICONS_DIR, "reset.png")), "Reset To Defaults")
        self.r2dBtn.setEnabled(False)

        # setup view
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN, DOCK_MARGIN)

        layout.addWidget(self.colConfigView)
        layout.addWidget(self.r2dBtn)

        # --- connect signal-slot --- #
        self.r2dBtn.clicked.connect(self.colConfigView.resetAllSettings)


    def __repr__(self) -> str:
        return f"<{type(self).__name__}"
    

    @property
    def model(self):
        return self._configTreeModel
    


class Spinder(QtWidgets.QWidget):
    """ Spinder (SpinBox + Slider) widget, which is next to each other. 
        The layout will be created automatically. 
        The layout can be accessed as self.layout.
    """ 

    def __init__(self, 
                 spinBox = None, 
                 slider = None,
                 layoutSpacing = None,
                 layoutContentsMargins = (0, 0, 0, 0),
                 parent = None):
        """ constructor.
            The settings (min, maxm enabled, etc) from the spinBox will be used 
            for the Slider as well. That is, the spinBox is the master.
        """
        super(Spinder, self).__init__(parent=parent)

        check_class(spinBox, QtWidgets.QSpinBox, allow_none=True)
        check_class(slider, QtWidgets.QSlider, allow_none=True)

        self.menuButton = QtWidgets.QPushButton('<select>')
        self.menuButton.setMaximumWidth(80)
        self.menuButton.setEnabled(False)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(*layoutContentsMargins)
        if layoutSpacing is not None:
            self.layout.setSpacing(layoutSpacing)
        
        if spinBox is None:
            self.spinBox = QtWidgets.QSpinBox()
        else:
            self.spinBox = spinBox
        self.spinBox.setMinimum(0)
        self.spinBox.setSingleStep(1)
        # self.spinBox.setSpecialValueText("<span style='text-align: center'>Not avaliable</span>")
        self.spinBox.setSpecialValueText("Not availabel")

        if slider is None:
            self.slider = QtWidgets.QSlider(Qt.Horizontal)
        else:
            self.slider = slider(Qt.Horizontal)
        self.slider.setEnabled(self.spinBox.isEnabled())

        hLayout = QtWidgets.QHBoxLayout()
        hLayout.addWidget(self.menuButton, stretch=0)
        hLayout.addWidget(self.slider, stretch=1)
        self.layout.addLayout(hLayout)
        self.layout.addWidget(self.spinBox)

        self.spinBox.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(self.spinBox.setValue)

    @QtSlot(dict)
    def _updateValues(self, values):

        print("values: {}".format(values))
        label = values['label']
        self.menuButton.setText(label)
        # updates spinBox value
        self.spinBox.setMinimum(values['min'] if 'min' in values else 0)
        self.spinBox.setMaximum(values['max'] if 'max' in values else 1)
        self.spinBox.setValue((values['max']+values['min'])//2)
        self.spinBox.setProperty("nodeName", label)
        self.spinBox.setEnabled(values['enabled'] if 'enabled' in values else False)
        self.spinBox.setPrefix("{} Slice Center = ".format(label) if self.spinBox.isEnabled() else 'Not avaliable')

        self.slider.setMinimum(self.spinBox.minimum())
        self.slider.setMaximum(self.spinBox.maximum())
        self.slider.setValue(self.spinBox.value())
        self.slider.setEnabled(self.spinBox.isEnabled())

        

class SpinBox(QtWidgets.QSpinBox):
    """ 
    A spinBox for use in the collector.
    Overrides the sizeHint so that is not truncated when large dimension names are selected.
    """

    def __init__(self, *args, **kwargs):
        super(SpinBox, self).__init__(*args, **kwargs)
        self._cachedSizeHint = None


    def sizeHint(self):
        """ Reimplemented from the C++ Qt source of QAbstractSpinBox.sizeHint, but without
            truncating to a maximum of 18 characters.
        """
        orgSizeHint = super(SpinBox, self).sizeHint()
        self.ensurePolished()
        h = orgSizeHint.height()
        result = QtCore.QSize(90, h)
        return result



class SpinSlider(QtWidgets.QWidget):
    """ 
    A SpinBox and Slider widgets next to each other.
    The layout will be created. It can be accessed as self.layout

    --> SpinBox and Slider widgets both for displaying.
    """

    def __init__(self, 
                 spinBox,
                 slider = None,
                 layoutSpacing = None,
                 layoutContentsMargins = (0, 0, 0, 0),
                 parent = None):
        
        super(SpinSlider, self).__init__(parent=parent)

        check_class(spinBox, QtWidgets.QSpinBox, allow_none=True)
        check_class(slider, QtWidgets.QSlider, allow_none=True)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(*layoutContentsMargins)

        if layoutSpacing is not None:
            self.layout.setSpacing(layoutSpacing)
        
        if spinBox is None:
            self.spinBox = QtWidgets.QSpinBox()
        else:
            self.spinBox = spinBox

        if slider is None:
            self.slider = QtWidgets.QSlider(Qt.Horizontal)
        else:
            self.slider = slider
        
        # settings for the qt-widgets
        self.slider.setMinimum(self.spinBox.minimum())
        self.slider.setMaximum(self.spinBox.maximum())
        self.slider.setValue(self.spinBox.value())
        self.slider.setEnabled(self.spinBox.isEnabled())

        self.layout.addWidget(self.spinBox, stretch=0)
        self.layout.addWidget(self.slider, stretch=1)

        self.spinBox.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(self.spinBox.setValue)