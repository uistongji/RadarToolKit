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


import os

from display.bindings import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QtCore, QtGui, QFileDialog
from display.settings import ICONS_DIR



class setupEnv(QDialog):
    
    def __init__(self):
        super().__init__()
        self.__initUI()


    def __initUI(self):
        self.setWindowTitle("Environment Setting")
        layout = QVBoxLayout()

        line_lay1 = QHBoxLayout()
        self.lbl_ice = QLabel("ICE:")
        self.button_ice = QPushButton(QtGui.QIcon(os.path.join(ICONS_DIR, "select.png")), "Select")
        self.button_ice.setIconSize(QtCore.QSize(16, 16))
        self.button_ice.clicked.connect(self.path_update)
        line_lay1.addWidget(self.lbl_ice)
        line_lay1.addWidget(self.button_ice)

        line_lay2 = QHBoxLayout()
        lbl_qyear = QLabel("QYEAR:")
        self.input_qyear = QLineEdit()
        self.input_qyear.setFixedWidth(180)
        line_lay2.addWidget(lbl_qyear)
        line_lay2.addWidget(self.input_qyear)

        line_lay2.addStretch(1)
        lbl_qplat = QLabel("QPLAT:")
        self.input_qplat = QLineEdit()
        self.input_qplat.setFixedWidth(180)
        line_lay2.addWidget(lbl_qplat)
        line_lay2.addWidget(self.input_qplat)

        line_lay3 = QHBoxLayout()
        lbl_qbase = QLabel("QBASE:")
        self.input_qbase = QLineEdit()
        self.input_qbase.setFixedWidth(180)
        line_lay3.addWidget(lbl_qbase)
        line_lay3.addWidget(self.input_qbase)

        line_lay3.addStretch(1)
        lbl_proj = QLabel("QPROJ:")
        self.input_qproj = QLineEdit()
        self.input_qproj.setFixedWidth(180)
        line_lay3.addWidget(lbl_proj)
        line_lay3.addWidget(self.input_qproj)

        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)  # Connect directly to reject
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)  # Connect to accept method
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(line_lay1)
        layout.addLayout(line_lay2)
        layout.addLayout(line_lay3)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.adjustSize()  # Adjust dialog size to fit all widgets


    def path_update(self):
        file_dialog = QFileDialog()
        selected_directory = file_dialog.getExistingDirectory(self, "Choose ICE", os.path.join(os.path.expanduser("~"), 'Desktop'))

        if selected_directory:
            self.icepath = selected_directory
            self.lbl_ice.setText(f"ICE: {self.icepath}")


    def accept(self):
        env_dict = self.get_env()
        os.environ["ICE"] = env_dict["ICE"]
        os.environ["QYEAR"] = env_dict["QYEAR"]
        os.environ["QPLAT"] = env_dict["QPLAT"]
        os.environ["QBASE"] = env_dict["QBASE"]
        os.environ["QPROJ"] = env_dict["QPROJ"]

        super().accept()  # Ensure that the dialog is closed


    def get_env(self):
        dict_env = {
            "ICE": self.icepath,
            "QYEAR": self.input_qyear.text(),
            "QPLAT": self.input_qplat.text(),
            "QBASE": self.input_qbase.text(),
            "QPROJ": self.input_qproj.text()
        }
        return dict_env
