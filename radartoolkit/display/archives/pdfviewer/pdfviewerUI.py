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


from PySide6.QtCore import (QCoreApplication, QMetaObject, QSize, Qt)
from PySide6.QtGui import (QAction, QIcon)
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (QToolBar, QSizePolicy, QSplitter, QTabWidget, 
                               QTreeView, QVBoxLayout,QWidget)



class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(1000,600)
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"PDF Viewer", None))
        
        self.actionOpen = QAction(Dialog)
        self.actionOpen.setObjectName(u"actionOpen")
        icon = QIcon()
        iconThemeName = u"document-open"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u"radartoolkit/display/resources/svgs/open-file.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.actionOpen.setIcon(icon)

        self.actionZoom_In = QAction(Dialog)
        self.actionZoom_In.setObjectName(u"actionZoom_In")
        icon1 = QIcon()
        iconThemeName = u"zoom-in"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u"radartoolkit/display/resources/svgs/zoom-in.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.actionZoom_In.setIcon(icon1)

        self.actionZoom_Out = QAction(Dialog)
        self.actionZoom_Out.setObjectName(u"actionZoom_Out")
        icon2 = QIcon()
        iconThemeName = u"zoom-out"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u"radartoolkit/display/resources/svgs/zoom-out.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.actionZoom_Out.setIcon(icon2)

        self.actionPrevious_Page = QAction(Dialog)
        self.actionPrevious_Page.setObjectName(u"actionPrevious_Page")
        icon3 = QIcon()
        iconThemeName = u"go-previous-page"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u"radartoolkit/display/resources/svgs/go-previous-page.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.actionPrevious_Page.setIcon(icon3)

        self.actionNext_Page = QAction(Dialog)
        self.actionNext_Page.setObjectName(u"actionNext_Page")
        icon4 = QIcon()
        iconThemeName = u"go-next-page"
        if QIcon.hasThemeIcon(iconThemeName):
            icon4 = QIcon.fromTheme(iconThemeName)
        else:
            icon4.addFile(u"radartoolkit/display/resources/svgs/go-next-page.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.actionNext_Page.setIcon(icon4)

        self.actionContinuous = QAction(Dialog)
        self.actionContinuous.setObjectName(u"actionContinuous")
        self.actionContinuous.setCheckable(True)
        icon5 = QIcon()
        iconThemeName = u"multipage-mode"
        if QIcon.hasThemeIcon(iconThemeName):
            icon5 = QIcon.fromTheme(iconThemeName)
        else:
            icon5.addFile(u"radartoolkit/display/resources/svgs/continuous.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.actionContinuous.setIcon(icon5)

        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.widget = QWidget(Dialog)
        self.widget.setObjectName(u"widget")
        self.verticalLayout_2 = QVBoxLayout(self.widget)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(self.widget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.tabWidget = QTabWidget(self.splitter)
        self.tabWidget.setObjectName(u"tabWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setTabPosition(QTabWidget.West)
        self.tabWidget.setDocumentMode(False)
        self.bookmarkTab = QWidget()
        self.bookmarkTab.setObjectName(u"bookmarkTab")
        self.verticalLayout_3 = QVBoxLayout(self.bookmarkTab)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(2, 2, 2, 2)
        self.bookmarkView = QTreeView(self.bookmarkTab)
        self.bookmarkView.setObjectName(u"bookmarkView")
        sizePolicy.setHeightForWidth(self.bookmarkView.sizePolicy().hasHeightForWidth())
        self.bookmarkView.setSizePolicy(sizePolicy)
        self.bookmarkView.setHeaderHidden(True)

        self.verticalLayout_3.addWidget(self.bookmarkView)
        self.tabWidget.addTab(self.bookmarkTab, "")
        
        self.splitter.addWidget(self.tabWidget)
        self.pdfView = QPdfView(self.splitter)
        self.pdfView.setObjectName(u"pdfView")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(10)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.pdfView.sizePolicy().hasHeightForWidth())
        self.pdfView.setSizePolicy(sizePolicy1)
        self.splitter.addWidget(self.pdfView)

        self.verticalLayout_2.addWidget(self.splitter)
       
        self.toolbar = QToolBar()
        self.toolbar.addAction(self.actionOpen)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionZoom_Out)
        self.toolbar.addAction(self.actionZoom_In)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionPrevious_Page)
        self.toolbar.addAction(self.actionNext_Page)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionContinuous)

        self.verticalLayout.addWidget(self.toolbar)

        self.verticalLayout.addWidget(self.widget)
        
        self.retranslateUi(Dialog)

        self.tabWidget.setCurrentIndex(0)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        self.actionOpen.setText(QCoreApplication.translate("Dialog", u"Open...", None))
#if QT_CONFIG(shortcut)
        self.actionOpen.setShortcut(QCoreApplication.translate("Dialog", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.actionZoom_In.setText(QCoreApplication.translate("Dialog", u"Zoom In", None))
#if QT_CONFIG(shortcut)
        self.actionZoom_In.setShortcut(QCoreApplication.translate("Dialog", u"Ctrl++", None))
#endif // QT_CONFIG(shortcut)
        self.actionZoom_Out.setText(QCoreApplication.translate("Dialog", u"Zoom Out", None))
#if QT_CONFIG(shortcut)
        self.actionZoom_Out.setShortcut(QCoreApplication.translate("Dialog", u"Ctrl+-", None))
#endif // QT_CONFIG(shortcut)
        self.actionPrevious_Page.setText(QCoreApplication.translate("Dialog", u"Previous Page", None))
#if QT_CONFIG(shortcut)
        self.actionPrevious_Page.setShortcut(QCoreApplication.translate("Dialog", u"PgUp", None))
#endif // QT_CONFIG(shortcut)
        self.actionNext_Page.setText(QCoreApplication.translate("Dialog", u"Next Page", None))
#if QT_CONFIG(shortcut)
        self.actionNext_Page.setShortcut(QCoreApplication.translate("Dialog", u"PgDown", None))
#endif // QT_CONFIG(shortcut)
        self.actionContinuous.setText(QCoreApplication.translate("Dialog", u"Continuous", None))
#if QT_CONFIG(tooltip)
        self.actionPrevious_Page.setToolTip(QCoreApplication.translate("Dialog", u"back to previous page", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.actionNext_Page.setToolTip(QCoreApplication.translate("Dialog", u"forward to next page", None))
#endif // QT_CONFIG(tooltip)
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.bookmarkTab), QCoreApplication.translate("Dialog", u"Bookmarks", None))
    # retranslateUi