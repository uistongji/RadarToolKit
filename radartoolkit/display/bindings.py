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
    Harmonize PySide6 API bindings.
    Basically this script is to provide a linker to the main RTK software.
"""


import os
import sys

import logging
logger = logging.getLogger(__name__)


API_PYSIDE6 = "PySide6"
REQUEST_PYSIDE6 = os.environ.get('QT_API')

# determine whether any QT_APIs environment variables exist
# if not the PySide6, then discard.
if REQUEST_PYSIDE6 != API_PYSIDE6:
    REQUEST_PYSIDE6 = None

# see if module is already imported
if REQUEST_PYSIDE6 is None:
    if 'PySide6' in sys.modules:
        REQUEST_PYSIDE6 = API_PYSIDE6


""" Try to import and do the imports if everything goes well.
"""
# try to import
if REQUEST_PYSIDE6 is None:
    try:

        import PySide6
        REQUEST_PYSIDE6 = API_PYSIDE6
    except ModuleNotFoundError:
        print(f"Required module not found: {API_PYSIDE6}. Link to the RTK main software unsuccessfully.")


# do the imports
if REQUEST_PYSIDE6 == API_PYSIDE6:

    from PySide6 import QtCore, QtGui, QtWidgets, QtSvg, QtXml, __version__ as PYSIDE_VERSION
    from PySide6.QtCore import (Qt, QLineF, QPointF, QRect, QObject, QRectF, QSize, QSizeF, Signal,
                                Signal as QtSignal, Slot as QtSlot, QThread, QThreadPool, QObject,
                                QSortFilterProxyModel, QModelIndex, QPersistentModelIndex, QRegularExpression,
                                QItemSelectionModel, QUrl, QFile, QAbstractTableModel)
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                                QPushButton, QFileDialog, QTableView, QWidget,
                                QApplication, QAbstractItemView, QGridLayout,
                                QMessageBox, QStyledItemDelegate, QComboBox,
                                QSpacerItem, QSizePolicy, QTableWidget,
                                QTableWidgetItem, QCheckBox, QHeaderView,
                                QGroupBox, QRadioButton, QFormLayout, QMenuBar,
                                QProgressDialog)
    from PySide6.QtSvgWidgets import QSvgWidget
    from PySide6.QtGui import (QBrush, QPen, QPainter, QColor, QFont, QAction, QIcon,
                            QPainterPath, QPixmap)
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEnginePage
    from PySide6.QtSql import QSqlTableModel, QSqlQuery, QSqlDatabase, QSqlError

    from PySide6 import QtXml as _unused_QtXml  # Removing unused import
    from PySide6.QtWidgets import QApplication as _unused_QApplication  # Removing unused import
    from PySide6.QtGui import QAction as _unused_QAction  # Removing unused import
    from PySide6.QtCore import __version__ as QT_VERSION  # Keeping QT_VERSION
    
else:
    raise RuntimeError(
        "Unable to import the required Qt bindings: {}".format(API_PYSIDE6))


