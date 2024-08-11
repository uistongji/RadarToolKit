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


import sys

from PySide6.QtPdf import QPdfBookmarkModel, QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (QDialog, QFileDialog, QMessageBox, QSpinBox)
from PySide6.QtCore import (QModelIndex, QPoint, QStandardPaths, QUrl, Slot)

from .zoomselector import ZoomSelector
from .pdfviewerUI import Ui_Dialog



class PDFViewer(QDialog):

    ZOOM_MULTIPLIER = 1.25  # Define a zoom multiplier for zooming in and out

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.m_zoomSelector = ZoomSelector(self)
        self.m_pageSelector = QSpinBox(self)
        self.m_document = QPdfDocument(self)
        self.m_fileDialog = None

        self.ui.setupUi(self)

        self.setWindowTitle("PDF Viewer") 

        self.m_zoomSelector.setMaximumWidth(150)
        self.ui.toolbar.insertWidget(self.ui.actionZoom_In,self.m_zoomSelector)
        self.m_zoomSelector.zoom_mode_changed.connect(self.ui.pdfView.setZoomMode)
        self.m_zoomSelector.zoom_factor_changed.connect(self.ui.pdfView.setZoomFactor)
        self.m_zoomSelector.reset()

        self.ui.toolbar.insertWidget(self.ui.actionNext_Page, self.m_pageSelector)
        self.m_pageSelector.valueChanged.connect(self.page_selected)
        nav = self.ui.pdfView.pageNavigator()
        nav.currentPageChanged.connect(self.m_pageSelector.setValue)

        self.ui.actionPrevious_Page.setEnabled(False) # default state
        self.ui.actionNext_Page.setEnabled(False)

        bookmark_model = QPdfBookmarkModel(self)
        bookmark_model.setDocument(self.m_document)

        self.ui.bookmarkView.setModel(bookmark_model)
        self.ui.bookmarkView.activated.connect(self.bookmark_selected)

        self.ui.pdfView.setDocument(self.m_document)

        self.ui.pdfView.zoomFactorChanged.connect(self.m_zoomSelector.set_zoom_factor)


    @Slot(QUrl)
    def open(self, doc_location):
        if doc_location.isLocalFile():
            self.m_document.load(doc_location.toLocalFile())
            document_title = self.m_document.metaData(QPdfDocument.MetaDataField.Title)
            self.setWindowTitle(document_title if document_title else "PDF Viewer")
            self.page_selected(0)
            self.m_pageSelector.setMaximum(self.m_document.pageCount() - 1)
            self.update_navigation_buttons()
            self.m_zoomSelector.setCurrentIndex(0) # Fit Width
            self.ui.bookmarkView.expandAll()
        else:
            message = f"{doc_location} is not a valid local file"
            print(message, file=sys.stderr)
            QMessageBox.critical(self, "Failed to open", message)
    

    @Slot(QModelIndex)
    def bookmark_selected(self, index):
        if not index.isValid():
            return
        page = index.data(int(QPdfBookmarkModel.Role.Page))
        zoom_level = index.data(int(QPdfBookmarkModel.Role.Level))
        self.ui.pdfView.pageNavigator().jump(page, QPoint(), zoom_level)


    @Slot(int)
    def page_selected(self, page):
        nav = self.ui.pdfView.pageNavigator()
        nav.jump(page, QPoint(), nav.currentZoom())
        self.update_navigation_buttons()
    

    @Slot()
    def update_navigation_buttons(self):
        current_page = self.ui.pdfView.pageNavigator().currentPage()
        total_pages = self.m_document.pageCount()

        self.ui.actionPrevious_Page.setEnabled(current_page > 0)
        self.ui.actionNext_Page.setEnabled(current_page < total_pages - 1)


    @Slot()
    def on_actionOpen_triggered(self):
        if not self.m_fileDialog:
            directory = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
            self.m_fileDialog = QFileDialog(self, "Choose a PDF", directory)
            self.m_fileDialog.setAcceptMode(QFileDialog.AcceptOpen)
            self.m_fileDialog.setMimeTypeFilters(["application/pdf"])
        if self.m_fileDialog.exec() == QDialog.Accepted:
            to_open = self.m_fileDialog.selectedUrls()[0]
            if to_open.isValid():
                self.open(to_open)


    @Slot()
    def on_actionZoom_In_triggered(self):
        factor = self.ui.pdfView.zoomFactor() * self.ZOOM_MULTIPLIER
        self.ui.pdfView.setZoomFactor(factor)


    @Slot()
    def on_actionZoom_Out_triggered(self):
        factor = self.ui.pdfView.zoomFactor() / self.ZOOM_MULTIPLIER
        self.ui.pdfView.setZoomFactor(factor)


    @Slot()
    def on_actionPrevious_Page_triggered(self):
        nav = self.ui.pdfView.pageNavigator()
        nav.jump(nav.currentPage() - 1, QPoint(), nav.currentZoom())


    @Slot()
    def on_actionNext_Page_triggered(self):
        nav = self.ui.pdfView.pageNavigator()
        nav.jump(nav.currentPage() + 1, QPoint(), nav.currentZoom())


    @Slot()
    def on_actionContinuous_triggered(self):
        cont_checked = self.ui.actionContinuous.isChecked()
        mode = QPdfView.PageMode.MultiPage if cont_checked else QPdfView.PageMode.SinglePage
        self.ui.pdfView.setPageMode(mode)