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
# AUTHOR: Jiaying Zhou, Chen Lv (supervisor: Tong Hao), Tongji University


import os
import re
import sqlite3
from typing import Any
from pathlib import Path
from .icedialog import setupEnv
from ..bindings import (QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QComboBox,
                        QVBoxLayout, QDialog, QFileDialog, QTableWidgetItem,QFormLayout,
                        QTableWidget, QCheckBox, QHeaderView, QWidget, QGroupBox,
                        QRadioButton, QApplication, Qt, Signal, QtGui, QtCore)



class paramsInputDialog(QDialog):

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.__initUI(path)


    def __initUI(self, path):
        self.setWindowTitle("Parameters Input")
        layout = QVBoxLayout()
        input_tip = QLabel(f"Please input parameters of {path}:")
        line_lay1 = QHBoxLayout()
        lbl_project = QLabel("Project:")
        self.input_project = QLineEdit()
        self.input_project.setFixedWidth(180)
        line_lay1.addWidget(lbl_project)
        line_lay1.addWidget(self.input_project)

        line_lay2 = QHBoxLayout()
        lbl_radar = QLabel("Radar:")
        self.input_radar = QLineEdit()
        self.input_radar.setFixedWidth(180)
        line_lay2.addWidget(lbl_radar)
        line_lay2.addWidget(self.input_radar)

        line_lay3 = QHBoxLayout()
        lbl_flight = QLabel("Flight:")
        self.input_flight = QLineEdit()
        self.input_flight.setFixedWidth(180)
        line_lay3.addWidget(lbl_flight)
        line_lay3.addWidget(self.input_flight)

        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addWidget(input_tip)
        layout.addLayout(line_lay1)
        layout.addLayout(line_lay2)
        layout.addLayout(line_lay3)
        layout.addLayout(button_layout)
        self.setLayout(layout)


    def accept(self):
        if not all([self.input_project.text(), self.input_radar.text(), self.input_flight.text()]):
            QMessageBox.warning(self, "Warning", "Please input all parameters.")
            return
        super().accept()

 
    def get_parameters(self):
        parameters = [self.input_project.text(), self.input_radar.text(), self.input_flight.text(), self.path]
        return parameters



class OpenFileDialog(QFileDialog):

    def __init__(self, option):
        super().__init__()
        self.setWindowTitle("Select Data File Folder")
        self.setDirectory(os.path.expanduser("-"))
        self.folder_path = self.getExistingDirectory(
            self, "Select a Directory", "", QFileDialog.ShowDirsOnly)


    def getpath(self):
        if self.folder_path:
            return self.folder_path
        else:
            return 



class AddColDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.__initUi()


    def __initUi(self):
        self.setWindowTitle('Add Column')

        self.__colNameLineEdit = QLineEdit()
        self.__colNameLineEdit.textChanged.connect(self.__checkAccept)

        self.combo_box = QComboBox()
        self.combo_box.addItems(["INTEGER", "TEXT"])

        lay = QFormLayout()
        lay.addRow('Name', self.__colNameLineEdit)
        lay.addRow('DataType', self.combo_box)
        top_widget = QWidget()
        top_widget.setLayout(lay)

        self.__okBtn = QPushButton('OK')
        self.__okBtn.clicked.connect(self.accept)
        self.__okBtn.setEnabled(False)

        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.close)

        lay = QHBoxLayout()
        lay.addWidget(self.__okBtn)
        lay.addWidget(close_btn)
        lay.setContentsMargins(0, 0, 0, 0)

        bottom_widget = QWidget()
        bottom_widget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(top_widget)
        lay.addWidget(bottom_widget)

        self.setLayout(lay)

        self.setFixedSize(self.sizeHint().width(), self.sizeHint().height())


    def __checkAccept(self, text):
        p = bool(re.match('^[a-zA-Z0-9]+$', text))
        self.__okBtn.setEnabled(p)


    def getColumnName(self):
        return self.__colNameLineEdit.text()


    def getDataType(self):
        return self.combo_box.currentText()



class DelColDialog(QDialog):

    def __init__(self, table_name):
        super().__init__()
        self.__initVal()
        self.__initUi(table_name)


    def __initVal(self):
        self.__chkBoxes = []


    def __initUi(self, table_name):
        self.setWindowTitle('Del Column')
        v_lay = QVBoxLayout()
        try:
            conn = sqlite3.connect('radartoolkit/display/resources/dbs/AntarcticaProject.sqlite') # relative path
            if conn:
                cursor = conn.cursor()
                mysel = cursor.execute(f"select * from {table_name}")
                column_names = list(map(lambda x: x[0], mysel.description))
                for columnName in column_names:
                    chk_box = QCheckBox(columnName)
                    self.__chkBoxes.append(chk_box)
                    v_lay.addWidget(chk_box)
                cursor.close()
                conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", e)

        group_box = QGroupBox()
        group_box.setLayout(v_lay)

        self.__okBtn = QPushButton('OK')
        self.__okBtn.clicked.connect(self.accept)

        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.close)

        h_lay = QHBoxLayout()
        h_lay.addWidget(self.__okBtn)
        h_lay.addWidget(close_btn)
        h_lay.setContentsMargins(0, 0, 0, 0)

        bottom_widget = QWidget()
        bottom_widget.setLayout(h_lay)

        whole_lay = QVBoxLayout()
        whole_lay.addWidget(group_box)
        whole_lay.addWidget(bottom_widget)

        self.setLayout(whole_lay)

        self.setFixedSize(self.sizeHint().width(), self.sizeHint().height())


    def getColumnNames(self):
        return [checkbox.text() for checkbox in self.__chkBoxes if checkbox.isChecked()]



class LoadDataDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.__initUi()


    def __initUi(self):
        self.setWindowTitle("Data select")
        self.setFixedSize(250, 150)
        layout = QVBoxLayout()
        tip = QLabel("Please select which type of data：")
        layout.addWidget(tip)
        self.combo_box = QComboBox()
        self.combo_box.addItems(["BreakOutData", "pik1Data"])
        layout.addWidget(self.combo_box)
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)


    def getcurrentValue(self):
        return self.combo_box.currentText()



class qctype_dialog(QDialog):

    def __init__(self):
        super().__init__()
        self.__initUi()


    def __initUi(self):
        self.setWindowTitle("Select QC Report")
        self.setFixedSize(300, 150)
        layout = QVBoxLayout()
        tip = QLabel("Please select which type of QC report：")
        layout.addWidget(tip)
        self.combo_box = QComboBox()
        self.combo_box.addItems(["GLNKQC", "GRADQC", "GGPSQC", "GQC"])
        layout.addWidget(self.combo_box)
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)


    def getcurrentValue(self):
        return self.combo_box.currentText()



class TableNameDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.__initUi()


    def __initUi(self):
        self.setWindowTitle("Table Name Input")

        layout = QVBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Input table name...")

        ok_button = QPushButton("OK", self)
        cancel_button = QPushButton("Cancel", self)
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout = QHBoxLayout()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addWidget(self.input_box)
        layout.addLayout(button_layout)

        self.setLayout(layout)


    def getTableName(self):
        return self.input_box.text()