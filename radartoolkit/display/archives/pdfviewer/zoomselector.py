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


""" This file contains code modified from the official Qt example "PDF Viewer" 
    found in the Qt for Python documentation.
    Original example: https://doc.qt.io/qtforpython-6/examples/example_pdfwidgets_pdfviewer.html
    Modifications made:
    - delete the pages tab.
    - change the ui design to fit QDialog form.
    - change the icons.
    The original code is provided by The Qt Company Ltd under the terms of the LicenseRef-Qt-Commercial OR BSD-3-Clause.
    For more information, see the original Qt documentation at https://doc.qt.io/.
    Copyright (C) 2022 The Qt Company Ltd.
"""


from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import Signal, Slot



class ZoomSelector(QComboBox):

    zoom_mode_changed = Signal(QPdfView.ZoomMode)
    zoom_factor_changed = Signal(float)

    def __init__(self, parent):
        super().__init__(parent)
        self.setEditable(True)

        self.addItem("Fit Width")
        self.addItem("Fit Page")
        self.addItem("12%")
        self.addItem("25%")
        self.addItem("33%")
        self.addItem("50%")
        self.addItem("66%")
        self.addItem("75%")
        self.addItem("100%")
        self.addItem("125%")
        self.addItem("150%")
        self.addItem("200%")
        self.addItem("400%")

        self.currentTextChanged.connect(self.on_current_text_changed)
        self.lineEdit().editingFinished.connect(self._editing_finished)


    @Slot(float)
    def set_zoom_factor(self, zoomFactor):
        percent = int(zoomFactor * 100)
        self.setCurrentText(f"{percent}%")


    @Slot()
    def reset(self):
        self.setCurrentIndex(8)  # 100%


    @Slot(str)
    def on_current_text_changed(self, text):
        if text == "Fit Width":
            self.zoom_mode_changed.emit(QPdfView.ZoomMode.FitToWidth)
        elif text == "Fit Page":
            self.zoom_mode_changed.emit(QPdfView.ZoomMode.FitInView)
        elif text.endswith("%"):
            factor = 1.0
            zoom_level = int(text[:-1])
            factor = zoom_level / 100.0
            self.zoom_mode_changed.emit(QPdfView.ZoomMode.Custom)
            self.zoom_factor_changed.emit(factor)


    @Slot()
    def _editing_finished(self):
        self.on_current_text_changed(self.lineEdit().text())
