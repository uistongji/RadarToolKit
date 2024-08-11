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


""" this file contains the UI design and functions in database tab.
"""


import os
import webbrowser
import sqlite3
from argparse import ArgumentParser, RawTextHelpFormatter
from .db import *
from ..bindings import QtCore, QtGui, QtWidgets, QtSignal, QMessageBox
from ..widgets.dbdialog import LoadDataDialog
from display.archives.pdfviewer.pdfviewer import PDFViewer
from display.settings import ICONS_DIR



class databse_tab(QtWidgets.QWidget):

    tableChanged = QtSignal(str) 
    sigShowMessage = QtSignal(str)

    def __init__(self, sync_signal):
        super().__init__()
        self.sync_signal = sync_signal
        self.__initUI()


    def __initUI(self):

        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(254, 254, 254))
        self.setPalette(p)

        btn_URL = QtWidgets.QPushButton(QtGui.QIcon(
            os.path.join(ICONS_DIR, "url.png")), 'Affiliation HomePage')
        btn_URL.setIconSize(QtCore.QSize(16, 16))
        btn_URL.clicked.connect(self.JumpToHomePage)

        btn_NewTable = QtWidgets.QPushButton(QtGui.QIcon(
            os.path.join(ICONS_DIR, "sheet.png")), 'New Table')
        btn_NewTable.setIconSize(QtCore.QSize(16, 16))
        btn_NewTable.clicked.connect(self.NewTable)

        btn_Load = QtWidgets.QPushButton(QtGui.QIcon(
            os.path.join(ICONS_DIR, "load_data.png")), 'Load Data')
        btn_Load.setIconSize(QtCore.QSize(16, 16))
        btn_Load.clicked.connect(self.LoadData)

        btn_OpenPDF = QtWidgets.QPushButton(QtGui.QIcon(
            os.path.join(ICONS_DIR, "pdf.png")), 'Open PDF')
        btn_OpenPDF.setIconSize(QtCore.QSize(16, 16))    
        btn_OpenPDF.clicked.connect(self.OpenPDF)

        hlayout1 = QtWidgets.QHBoxLayout()
        hlayout1.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        switch_lbl = QtWidgets.QLabel("Please select a table:")
        self.table_comboBox = QtWidgets.QComboBox()
       
        try:
            conn = sqlite3.connect('radartoolkit/display/resources/dbs/AntarcticaProject.sqlite') # relative path
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                if tables:
                    table_names = [row[0] for row in tables]
                    if "sqlite_sequence" in table_names:
                        table_names.remove("sqlite_sequence")
                    for i in range(len(table_names)):
                        self.table_comboBox.addItem(table_names[i])
                cursor.close()
                conn.close()  
        except sqlite3.Error as e:
            self.sigShowMessage(e)

        self.table_comboBox.currentIndexChanged.connect(
            self.table_comboBoxCurrentIndexChanged)
        hlayout1.addWidget(switch_lbl)
        hlayout1.addSpacing(20)
        hlayout1.addWidget(self.table_comboBox)

        hlayout2 = QtWidgets.QHBoxLayout()
        hlayout2.addWidget(btn_Load)
        hlayout2.addWidget(btn_OpenPDF)

        hlayout3 = QtWidgets.QHBoxLayout()
        hlayout3.addWidget(btn_URL)
        hlayout3.addWidget(btn_NewTable)

        self.table_name = self.table_comboBox.currentText()
        self.database = DBWidget(self.sync_signal, self.table_name)
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addLayout(hlayout1)
        vlayout.setSpacing(5)
        vlayout.addWidget(self.database)
        vlayout.addSpacing(5)

        vlayout.addLayout(hlayout2)
        vlayout.addLayout(hlayout3)
        self.setLayout(vlayout)


    def JumpToHomePage(self):
        """
        Open the default browser to load the webpage given by the URL.
        """

        # Look up Affiliation_URL in DB
        field_name = "Affiliation_URL"
        currentID = self.database.getcurrentID()
        if currentID and field_name:
            # Fetch URL from the database
            result = self.database.lookupValueByID(
                self.table_comboBox.currentText(), currentID, field_name
            )
            
            if result is not None and len(result) > 0:
                Affiliation_URL = result[0]
                if Affiliation_URL:
                    # Open the URL in the default web browser
                    webbrowser.open(Affiliation_URL)
                else:
                    QMessageBox.warning(
                        None,
                        "Jump To Home Page",
                        "No URL found for the current entry."
                    )
            else:
                QMessageBox.warning(
                    None,
                    "Jump To Home Page",
                    "No URL found for the current entry."
                )
        else:
            QMessageBox.warning(
                None,
                "Jump To Home Page",
                "No valid entry selected."
            )


    def NewTable(self):
        """
        New database table.
        """

        try:
            conn = sqlite3.connect('radartoolkit/display/resources/dbs/AntarcticaProject.sqlite') # relative path
            if conn:
                table_name, ok = QtWidgets.QInputDialog.getText(self, 'Create New Table', 'Enter table name:')
                if ok:
                    cursor = conn.cursor()
                    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (ID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, Project TEXT)")
                    conn.commit()
                    cursor.close()
                    conn.close()
                    self.onrecordUpdated()
                    self.onSheetUpdated()
        except sqlite3.Error as e:
            self.sigShowMessage.emit(str(e))


    def pass_message(self, message):
        self.sigShowMessage.emit(message)


    def LoadData(self):
        """
        Load radar data and transfer the status file
        """

        loaddata = LoadDataDialog()
        if loaddata.exec() == QDialog.Accepted:
            DataType = loaddata.getcurrentValue()
            field_name = DataType
            currentID = self.database.getcurrentID()
            if currentID and field_name:
                result = self.database.lookupValueByID(self.table_comboBox.currentText(), currentID, field_name)
                if result:
                    DataPath = result[0]
                    if DataPath:
                        pass
                    else:
                        self.sigShowMessage.emit("DataPath is empty.")
                else:
                    self.sigShowMessage.emit("No data found for the given ID and field.")
        else:
            self.sigShowMessage.emit("Data loading canceled.")
        

    def OpenPDF(self):
        """
        Retrieve file parameters
        """

        argument_parser = ArgumentParser(description="PDF Viewer",
                                     formatter_class=RawTextHelpFormatter)
        argument_parser.add_argument("file", help="The file to open",
                                    nargs='?', type=str)
        options = argument_parser.parse_args()
        self.pdfw = PDFViewer()
        if options.file:
            self.pdfw.open(QtCore.QUrl.fromLocalFile(options.file))
        self.pdfw.exec()
       

    def onSheetUpdated(self):

        self.sigShowMessage.emit("Database has been updated.")
        try:
            conn = sqlite3.connect('radartoolkit/display/resources/dbs/AntarcticaProject.sqlite') # relative path
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                if tables:
                    table_names = [row[0] for row in tables]
                    if "sqlite_sequence" in table_names:
                        table_names.remove("sqlite_sequence")
                    if "map_data" in table_names:
                        table_names.remove("map_data")
                    combo_items = [self.table_comboBox.itemText(
                        i) for i in range(self.table_comboBox.count())]
                    for table_name in table_names:
                        if table_name not in combo_items:
                            self.table_comboBox.addItem(table_name)
                            self.table_comboBox.setCurrentIndex(
                                self.table_comboBox.count() - 1)  # the latest index
                            self.database.changeTable(table_name)
                cursor.close()
                conn.close()
        except sqlite3.Error as e:
            self.sigShowMessage.emit(e)


    def onrecordUpdated(self):
        print("Record has been updated.")
        table_name = self.table_comboBox.currentText()
        self.database.changeTable(table_name)


    def table_comboBoxCurrentIndexChanged(self):
        table_name = self.table_comboBox.currentText()
        self.database.changeTable(table_name)
        self.tableChanged.emit(table_name)