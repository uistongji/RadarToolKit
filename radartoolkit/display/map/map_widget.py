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
# AUTHOR: Jiaying Zhou (supervisor: Tong Hao), Tongji University


""" this file contains the UI design and functions of map tab in rtktoolbox
"""


from display.settings import ICONS_DIR
from display.widgets.icedialog import setupEnv
from ..bindings import QtCore, QtGui, QtWidgets, QProgressDialog
from ..archives.db import *



class MapWholeWidget(QtWidgets.QWidget):

    def __init__(self, ref=None, parent=None):
        super().__init__(parent)
        self.ref = ref
        self.__initUI()


    def __initUI(self):
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(254, 254, 254))
        self.setPalette(p)

        lbl = QtWidgets.QLabel("Current Table:  Map Data")
        self.map_db = MapWidget('map_data')

        self.btn_update = QtWidgets.QPushButton(QtGui.QIcon(
            os.path.join(ICONS_DIR, "update.png")), "Update")
        self.btn_update.setIconSize(QtCore.QSize(16, 16))
        self.btn_update.clicked.connect(self.update)

        self.btn_drawall = QtWidgets.QPushButton(QtGui.QIcon(
            os.path.join(ICONS_DIR, "draw-all.png")), "Draw All")
        self.btn_drawall.setIconSize(QtCore.QSize(16, 16))
        self.btn_drawall.clicked.connect(self.drawall)

        btn_clear = QtWidgets.QPushButton(QtGui.QIcon(
            os.path.join(ICONS_DIR, "clear-all.png")), "Clear All")
        btn_clear.setIconSize(QtCore.QSize(16, 16))
        btn_clear.clicked.connect(self.clear)
        
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.btn_update)
        hlayout.addWidget(self.btn_drawall)
        hlayout.addWidget(btn_clear)
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        vlayout.addWidget(lbl)
        vlayout.setSpacing(5)
        vlayout.addWidget(self.map_db)
        vlayout.addLayout(hlayout)
        self.setLayout(vlayout)


    def update(self):
        ids, paths, projects = self.map_db.getSelectedRecordDetails()
        if not paths:
            return

        if len(paths) > 10:
            message_box = QtWidgets.QMessageBox(self)
            message_box.setIcon(QtWidgets.QMessageBox.Warning)
            message_box.setWindowTitle("Selection Limit")
            message_box.setText("To ensure the application remains responsive, only the first 10 selected records will be drawn.")
            message_box.setStandardButtons(QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Ok)
            message_box.setDefaultButton(QtWidgets.QMessageBox.Ok)

            result = message_box.exec_()
            if result == QtWidgets.QMessageBox.Cancel:
                self.btn_update.setEnabled(True)
                self.btn_drawall.setEnabled(True)
                return
            else:
                ids = ids[:10]
                paths = paths[:10]
                projects = projects[:10]

        self.btn_update.setEnabled(False)
        self.btn_drawall.setEnabled(False)
        progress_dialog = QProgressDialog("Updating...", "Cancel", 0, len(paths))
        progress_dialog.setWindowTitle("Progress")
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.show()
        QtCore.QTimer.singleShot(50, lambda: self.excute_draw(ids, paths, projects, progress_dialog))


    def excute_draw(self, ids, paths, projects, progress_dialog):
        ice_path = os.getenv('ICE')
        if ice_path is None:
            message_box = QMessageBox(self)
            message_box.setIcon(QMessageBox.Warning)
            message_box.setWindowTitle("Environment Variable Missing")
            message_box.setText("The environment variable 'ICE' is not set. Please set it to the appropriate directory.")
            message_box.setStandardButtons(QMessageBox.Ok)
            message_box.exec()
            setICE = setupEnv()
            setICE.exec()
            self.btn_update.setEnabled(True)
            self.btn_drawall.setEnabled(True)
            return

        absolute_paths = [os.path.join(ice_path, 'shpdata', path) if not os.path.isabs(path) else path for path in paths]
        
        try:
            self.ref.draw(ids, absolute_paths, projects, progress_dialog)
        finally:
            self.btn_update.setEnabled(True)
            self.btn_drawall.setEnabled(True)
            progress_dialog.close()


    def drawall(self):
        self.btn_update.setEnabled(False)
        self.btn_drawall.setEnabled(False)
        progress_dialog = QProgressDialog("Updating...", "Cancel", 0, 1)
        progress_dialog.setWindowTitle("Progress")
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.show()
        QtCore.QTimer.singleShot(50, lambda: self.excute_drawall(progress_dialog))
        
    
    def excute_drawall(self, progress_dialog):
        try:
            self.clear()
            ice_path = os.getenv('ICE')
            if ice_path is None:
                message_box = QMessageBox(self)
                message_box.setIcon(QMessageBox.Warning)
                message_box.setWindowTitle("Environment Variable Missing")
                message_box.setText("The environment variable 'ICE' is not set. Please set it to the appropriate directory.")
                message_box.setStandardButtons(QMessageBox.Ok)
                message_box.exec()
                setICE = setupEnv()
                setICE.exec()
                self.btn_update.setEnabled(True)
                self.btn_drawall.setEnabled(True)
                return
            allreords_path = os.path.join(ice_path, 'shpdata', 'ALL/merged_lines.shp')
            self.ref.draw([-1], [allreords_path], ['All'], progress_dialog)
            
        finally:
            self.btn_update.setEnabled(True)
            self.btn_drawall.setEnabled(True)
            progress_dialog.close()


    def clear(self):
        self.ref.clearLines()


    def onrecordUpdated(self):
        pass