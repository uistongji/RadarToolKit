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


""" this file contains all the database methods.
"""


import os
import sys
import sqlite3
import xlsxwriter
import pandas as pd
from typing import Union
import subprocess

from ..bindings import (QtSignal, QSqlTableModel, QSvgWidget,QTableView, QRegularExpression,
                        QWidget, QHBoxLayout, QApplication, QLabel, QAbstractItemView, QObject,
                        QGridLayout, QLineEdit, QStyledItemDelegate, QPushButton, QComboBox,
                        QSpacerItem, QSizePolicy, QVBoxLayout, QDialog, QFileDialog, QTableWidget,
                        QTableWidgetItem, QStyledItemDelegate, Qt, QSortFilterProxyModel,
                        QModelIndex, QPersistentModelIndex, QItemSelectionModel, QtGui, QtWidgets,
                        QSqlDatabase, QSqlQuery, QMessageBox)

from ..widgets.dbdialog import AddColDialog, DelColDialog, TableNameDialog



class SyncSignal(QObject):
    syncRequested = QtSignal()



class InstantSearchBar(QWidget):
    searched = QtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__initUi()


    def __initUi(self):
        
        self.__label = QLabel()

        self.__searchLineEdit = QLineEdit()
        self.__searchIcon = QSvgWidget()
        ps = QApplication.font().pointSize()
        self.__searchIcon.setFixedSize(ps, ps)

        self.__searchBar = QWidget()
        self.__searchBar.setObjectName('searchBar')

        lay = QHBoxLayout()
        lay.addWidget(self.__searchIcon)
        lay.addWidget(self.__searchLineEdit)
        self.__searchBar.setLayout(lay)
        lay.setContentsMargins(ps // 2, 0, 0, 0)
        lay.setSpacing(0)

        self.__searchLineEdit.setFocus()
        self.__searchLineEdit.textChanged.connect(self.__searched)

        self.setAutoFillBackground(True)

        lay = QHBoxLayout()
        lay.addWidget(self.__searchBar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

        self._topWidget = QWidget()
        self._topWidget.setLayout(lay)

        lay = QGridLayout()
        lay.addWidget(self._topWidget)

        searchWidget = QWidget()
        searchWidget.setLayout(lay)
        lay.setContentsMargins(0, 0, 0, 0)

        lay = QGridLayout()
        lay.addWidget(searchWidget)
        lay.setContentsMargins(0, 0, 0, 0)

        self.__setStyle()

        self.setLayout(lay)


    def setLabel(self, visibility: bool = True, text=None):
        if text:
            self.__label.setText(text)
        self.__label.setVisible(visibility)


    def __setStyle(self):
        self.__searchIcon.load('radartoolkit/display/resources/svgs/search.svg')

        with open('radartoolkit/display/resources/css/lineedit.css', 'r') as f:
            self.__searchLineEdit.setStyleSheet(f.read())
        with open('radartoolkit/display/resources/css/search_bar.css', 'r') as f:
            self.__searchBar.setStyleSheet(f.read())
        with open('radartoolkit/display/resources/css/widget.css', 'r') as f:
            self.setStyleSheet(f.read())


    def __searched(self, text):
        self.searched.emit(text)


    def setSearchIcon(self, icon_filename: str):
        self.__searchIcon.load(icon_filename)


    def setPlaceHolder(self, text: str):
        self.__searchLineEdit.setPlaceholderText(text)


    def getSearchBar(self):
        return self.__searchLineEdit


    def getSearchLabel(self):
        return self.__searchIcon


    def showEvent(self, e):
        self.__searchLineEdit.setFocus()



class FilterProxyModel(QSortFilterProxyModel):

    def __init__(self):
        super().__init__()
        self.__searchedText = ''


    @property
    def searchedText(self):
        return self.__searchedText


    @searchedText.setter
    def searchedText(self, value):
        self.__searchedText = value
        self.invalidateFilter()



class AlignDelegate(QStyledItemDelegate):

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter


    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        return editor



class SqlTableModel(QSqlTableModel):

    added = QtSignal(int, str)
    updated = QtSignal(int, str)
    deleted = QtSignal(list)
    addedCol = QtSignal()
    deletedCol = QtSignal()

    def flags(self, index: Union[QModelIndex, QPersistentModelIndex]) -> Qt.ItemFlags:
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return super().flags(index)



class DatabaseManage(QWidget):

    sheetUpdated = QtSignal()
    recordUpdated = QtSignal()
    sigShowMessage = QtSignal(str)

    def __init__(self, sync_signal, tablename):
        super().__init__()
        self.sync_signal = sync_signal
        self.__tableName = tablename
        self.__initUi()


    def __initUi(self):
       
        self.setWindowTitle("DataBase Management")
        self.lbl = QLabel(f"Current Table: {self.__tableName}")
       
        self.__model = SqlTableModel(self)        
        self.__model.setTable(self.__tableName)
        self.__model.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.__model.beforeUpdate.connect(self.__updated)
        self.__model.select()

        self.__proxyModel = FilterProxyModel()

        self.__proxyModel.setSourceModel(self.__model)

        self.__tableView = QTableView()
        self.__tableView.setModel(self.__proxyModel)

        delegate = AlignDelegate()
        for i in range(self.__model.columnCount()):
            self.__tableView.setItemDelegateForColumn(i, delegate)

        self.__tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.__tableView.setSortingEnabled(True)
        self.__tableView.sortByColumn(0, Qt.AscendingOrder)

        self.__tableView.setCurrentIndex(self.__tableView.model().index(0, 0))

        addBtn = QPushButton('Add Record')
        addBtn.clicked.connect(self.__add)
        self.__delBtn = QPushButton('Delete Record')
        self.__delBtn.clicked.connect(self.__delete)

        addColBtn = QPushButton('Add Column')
        addColBtn.clicked.connect(self.__addCol)
        self.__delColBtn = QPushButton('Delete Column')
        self.__delColBtn.clicked.connect(self.__deleteCol)

        self.__importBtn = QPushButton('Import As Excel')
        self.__importBtn.clicked.connect(self.__import)

        self.__exportBtn = QPushButton('Export As Excel')
        self.__exportBtn.clicked.connect(self.__export)

        self.__searchBar = InstantSearchBar()
        self.__searchBar.setPlaceHolder('Search...')
        self.__searchBar.searched.connect(self.__showResult)

        self.__comboBox = QComboBox()
        record = self.__model.record()
        field_names = [record.fieldName(i) for i in range(record.count())]
        items = ['All'] + field_names
        for i in range(len(items)):
            self.__comboBox.addItem(items[i])
        self.__comboBox.currentIndexChanged.connect(self.__currentIndexChanged)

        self.__tableInfoWidget = QTableWidget()
        self.__setTableInfo(schema_name='AntarcticaProject.sqlite',
                            table_name=self.__tableName)
        self.__tableInfoWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        
        lay = QHBoxLayout()
        lay.addWidget(self.lbl)
        lay.addSpacing(20)
        lay.addWidget(self.__comboBox)
        lay.addSpacing(20)
        lay.addWidget(self.__searchBar)
        
        searchWidget = QWidget()
        searchWidget.setLayout(lay)

        lay_btn = QHBoxLayout()
        lay_btn.addWidget(addBtn)
        lay_btn.addWidget(self.__delBtn)
        lay_btn.addWidget(addColBtn)
        lay_btn.addWidget(self.__delColBtn)
        lay_btn.addWidget(self.__importBtn)
        lay_btn.addWidget(self.__exportBtn)
        lay_btn.setContentsMargins(0, 0, 0, 0)
        btnWidget = QWidget()
        btnWidget.setLayout(lay_btn)

        self.lay = QVBoxLayout()
        self.lay.addWidget(searchWidget)
        self.lay.addWidget(btnWidget)

        self.lay.addWidget(self.__tableView)

        layH = QHBoxLayout()
        layH.addWidget(QLabel('Table Info'))
       
        self.btn_showhide = QPushButton('Show')
        self.__tableInfoWidget.hide()  # default value
        self.btn_showhide.setFixedSize(100, 30)
        self.btn_showhide.clicked.connect(self.__showhideTableInfo)

        layH.addWidget(self.btn_showhide)
        self.lay.addLayout(layH)
        self.lay.addWidget(self.__tableInfoWidget)  # Table Info
        self.lay.setStretchFactor(self.__tableView, 2)
        self.lay.setStretchFactor(self.__tableInfoWidget, 1)
        self.setLayout(self.lay)
        self.__showResult('')

        self.__delBtnToggle()


    def __setTableInfo(self, schema_name: str, table_name: str):

        try:
            conn = sqlite3.connect('radartoolkit/display/resources/dbs/AntarcticaProject.sqlite') # relative path
            if conn:
                cursor = conn.cursor()
                result = cursor.execute(f'PRAGMA table_info([{self.__tableName}])')
                result_info = result.fetchall()
                df = pd.DataFrame(result_info, columns=[
                    'cid', 'name', 'type', 'not_null', 'default_value', 'primary_key'])
                columnNames = df.keys().values
                values = df.values
                self.__tableInfoWidget.setEditTriggers(
                    QAbstractItemView.NoEditTriggers)
                self.__tableInfoWidget.setColumnCount(len(columnNames))
                self.__tableInfoWidget.setRowCount(len(values))

                for i in range(len(columnNames)):
                    self.__tableInfoWidget.setHorizontalHeaderItem(
                        i, QTableWidgetItem(columnNames[i]))
                for i in range(len(values)):
                    for j in range(len(values[i])):
                        self.__tableInfoWidget.setItem(
                            i, j, QTableWidgetItem(str(values[i][j])))

                delegate = AlignDelegate()

                for i in range(self.__tableInfoWidget.columnCount()):
                    self.__tableInfoWidget.setItemDelegateForColumn(i, delegate)

                cursor.close()
                conn.close()

        except sqlite3.Error as e:
            self.sigShowMessage.emit(e)


    def __delBtnToggle(self):
        self.__delBtn.setEnabled(len(self.__tableView.selectedIndexes()) > 0)


    def __showhideTableInfo(self):
        if self.__tableInfoWidget.isHidden():
            self.__tableInfoWidget.show()
            self.btn_showhide.setText("Hide")
            self.btn_showhide.update()
        else:
            self.__tableInfoWidget.hide()
            self.btn_showhide.setText("Show")
            self.btn_showhide.update()


    def __add(self):
        # Add new record
        r = self.__model.record()
        field_names = [r.fieldName(i) for i in range(r.count())]

        for field_name in field_names:
            if field_name != 'ID':  # Do not set ID, let the database handle it
                r.setValue(field_name, '')

        if not self.__model.insertRecord(-1, r):
            print(f"Error inserting record: {self.__model.lastError().text()}")
            return

        if not self.__model.submitAll():
            print(f"Error submitting record: {self.__model.lastError().text()}")
            self.__model.revertAll()
            return

        self.__model.select()

        newTransectIdx = self.__tableView.model().index(
            self.__tableView.model().rowCount() - 1, 0)
        self.__tableView.setCurrentIndex(newTransectIdx)

        new_id = self.__tableView.model().data(newTransectIdx)
        self.__model.added.emit(new_id, new_id)
        self.__tableView.edit(
            self.__tableView.currentIndex().siblingAtColumn(1))
        
        verticalScrollBar = self.__tableView.verticalScrollBar()
        verticalScrollBar.setValue(verticalScrollBar.maximum())

        self.__delBtnToggle()
        self.recordUpdated.emit()
        self.sync_signal.syncRequested.emit()


    def __updated(self, i, r):
        # send updated signal
        self.__model.updated.emit(r.value('Project'), r.value('Affiliation'))


    def __delete(self):
        rows = [idx.row() for idx in self.__tableView.selectedIndexes()]

        if not rows:
            return

        names = []
        for r_idx in rows:
            name = self.__model.data(self.__model.index(r_idx, 1))
            if name:
                names.append(name)
            self.__model.removeRow(r_idx)

        self.__model.select()

        self.__tableView.setCurrentIndex(
            self.__tableView.model().index(max(0, rows[0] - 1), 0)
        )

        self.__model.deleted.emit(names)
        self.__delBtnToggle()
        self.recordUpdated.emit()
        self.__model.select()
        self.sync_signal.syncRequested.emit()


    def __import(self):
        filename = QFileDialog.getOpenFileName(
            self, 'Select the file', '', 'Excel File (*.xlsx)')
        filename = filename[0]
        if filename:
            try:
                conn = sqlite3.connect('radartoolkit/display/resources/dbs/AntarcticaProject.sqlite') # relative path
                if conn:
                    wb = pd.read_excel(filename, sheet_name=None)
                    for sheet in wb:
                        wb[sheet].to_sql(sheet, conn, if_exists='replace', index=False)
                    conn.commit()
                    conn.close()
                    sheetname_list = list(wb.keys())
                    self.__model.setTable(sheetname_list[0])
                    self.__model.select()
                    self.__tableView.setModel(self.__model)
                    self.__tableName = sheetname_list[0]
                    self.__model.select()
                    self.lbl.setText(f"Current Table: {self.__tableName}")
                    self.sheetUpdated.emit()
                    self.recordUpdated.emit()
                    self.sync_signal.syncRequested.emit()
            except sqlite3.Error as e:
                self.sigShowMessage.emit(e)


    def __addCol(self):
        dialog = AddColDialog()
        reply = dialog.exec()
        if reply == QDialog.Accepted:
            column_name = dialog.getColumnName()
            data_type = dialog.getDataType()

            if not column_name or not data_type:
                self.sigShowMessage.emit("Column name or data type is invalid")
                return

            try:
                conn = sqlite3.connect('radartoolkit/display/resources/dbs/AntarcticaProject.sqlite') # relative path
                cursor = conn.cursor()
                cursor.execute(f'ALTER TABLE {self.__tableName} ADD COLUMN "{column_name}" {data_type}')
                self.__model.setTable(self.__tableName)
                self.__model.select()
                self.__tableView.resizeColumnsToContents()
                self.__model.addedCol.emit()
                self.recordUpdated.emit()
                cursor.close()
                conn.close()

                horizontalScrollBar = self.__tableView.horizontalScrollBar()
                horizontalScrollBar.setValue(horizontalScrollBar.maximum())
                self.sync_signal.syncRequested.emit()

            except Exception as e:
                self.sigShowMessage.emit(str(e))


    def __deleteCol(self):
        dialog = DelColDialog(self.__tableName)
        reply = dialog.exec()
        if reply == QDialog.Accepted:
            ColumnNamesToRemove = dialog.getColumnNames()
            try:
                conn = sqlite3.connect('radartoolkit/display/resources/dbs/AntarcticaProject.sqlite') # relative path
                if conn:
                    cursor = conn.cursor()
                    for column_name in ColumnNamesToRemove:
                        cursor.execute(f"ALTER TABLE {self.__tableName} DROP COLUMN {column_name}")
                        self.__model.setTable(self.__tableName)
                        self.__model.select()
                        self.__tableView.resizeColumnsToContents()
                        self.__model.deletedCol.emit()
                        self.recordUpdated.emit()
                    cursor.close()
                    conn.close()
                    self.sync_signal.syncRequested.emit()

            except sqlite3.Error as e:
                self.sigShowMessage.emit(e)


    def __export(self):
        tablename_Dialog = TableNameDialog()
        tablename_Dialog.exec()
        tablename = tablename_Dialog.getTableName()
        filename = QFileDialog.getSaveFileName(
            self, 'Export', '.', 'Excel File (*.xlsx)')
        filename = filename[0]
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        if filename:
            try:
                conn = sqlite3.connect('radartoolkit/display/resources/dbs/AntarcticaProject.sqlite') # relative path
                if conn:
                    cursor = conn.cursor()
                    mysel = cursor.execute(f"select * from {self.__tableName}")
                    columnNames = list(map(lambda x: x[0], mysel.description))
                    workbook = xlsxwriter.Workbook(filename)
                    worksheet = workbook.add_worksheet(tablename)
                    for c_idx in range(len(columnNames)):
                        worksheet.write(0, c_idx, columnNames[c_idx])

                    for i, row in enumerate(mysel):
                        for j, value in enumerate(row):
                            worksheet.write(i + 1, j, row[j])
                    workbook.close()
                    if sys.platform == 'linux' or sys.platform == 'linux2':
                        # Linux
                        subprocess.Popen(['xdg-open', filename])
                    elif sys.platform == 'darwin':
                        # macOS
                        subprocess.Popen(['open', filename])
                    elif sys.platform == 'win32':
                        # Windows
                        subprocess.Popen(['start', '', filename], shell=True)
                    cursor.close()
                    conn.close()
            except sqlite3.Error as e:
                self.sigShowMessage.emit(e)


    def __showResult(self, text):
        # index -1 will be read from all columns
        # otherwise it will be read the current column number indicated by combobox
        field_index = self.__model.record().indexOf(self.__comboBox.currentText())
        self.__proxyModel.setFilterKeyColumn(field_index)
        regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
        # regular expression can be used
        self.__proxyModel.setFilterRegularExpression(regex)


    def __currentIndexChanged(self, idx):
        self.__showResult(self.__searchBar.getSearchBar().text())


    def getModel(self):
        return self.__model


    def getView(self):
        return self.__tableView


    def changeTable(self, table_name):
        print(f"Changing table to: {table_name}")
        self.__tableName = table_name
        self.lbl.setText(f"Current Table: {self.__tableName}")
        try:
            print("Setting table on the model...")
            self.__model.setTable(self.__tableName)
            print("Table set successfully.")
            
            print("Selecting data from the table...")
            if not self.__model.select():
                print(f"Failed to select data: {self.__model.lastError().text()}")
                return
            print("Data selected successfully.")
            self.__tableView.viewport().update()
            self.__setTableInfo(schema_name='AntarcticaProject.sqlite', table_name=self.__tableName)
        except Exception as e:
            print(f"Exception occurred: {e}")



class DBWidget(QWidget):

    sigShowMessage = QtSignal(str)
    def __init__(self, sync_signal, table_name):
        super().__init__()
        self.sync_signal = sync_signal
        self.sync_signal.syncRequested.connect(self.onsyncData)
        self.__tableName = table_name
        self.__initUi()


    def __initUi(self):
       
        self.__model = SqlTableModel(self)
        self.__model.setTable(self.__tableName)
        self.__model.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.__model.beforeUpdate.connect(self.__updated)
        self.__model.select()

        self.__proxyModel = FilterProxyModel()

        self.__proxyModel.setSourceModel(self.__model)

        self.__tableView = QTableView()
        self.__tableView.setModel(self.__proxyModel)
        self.__tableView.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)

        columns_to_display = ["Project", "Affiliation", "Year", "Area"]

        record = self.__model.record()
        field_names = [record.fieldName(i) for i in range(record.count())]
        for i in range(len(field_names)):
            if field_names[i] in columns_to_display:
                pass
            else:
                self.__tableView.hideColumn(i)

        delegate = AlignDelegate()
        for i in range(self.__model.columnCount()):
            self.__tableView.setItemDelegateForColumn(i, delegate)

        self.__tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__tableView.resizeColumnsToContents()
        self.__tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.__tableView.setSortingEnabled(True)
        self.__tableView.sortByColumn(0, Qt.AscendingOrder)
        self.__tableView.setCurrentIndex(self.__tableView.model().index(0, 0))

        self.__searchBar = InstantSearchBar()
        self.__searchBar.setPlaceHolder('Search...')
        self.__searchBar.searched.connect(self.__showResult)

        self.__comboBox = QComboBox()
        
        items = ['All'] + columns_to_display
        for i in range(len(items)):
            self.__comboBox.addItem(items[i])
        self.__comboBox.currentIndexChanged.connect(self.__currentIndexChanged)

        lay = QHBoxLayout()
        lay.addWidget(self.__comboBox)
        lay.addWidget(self.__searchBar)
        lay.setContentsMargins(0, 0, 0, 0)
        btnWidget = QWidget()
        btnWidget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(btnWidget)
        lay.addWidget(self.__tableView)

        self.setLayout(lay)

        # show default result (which means "show all")
        self.__showResult('')


    def onsyncData(self):
        try:
            self.changeTable(self.__tableName)
        except Exception as e:
            print("Exception occurred while syncing data")


    def changeTable(self, table_name):
        self.__tableName = table_name
        self.__model.setTable(table_name)
        self.__model.select()
        columns_to_display = ["Project", "Affiliation", "Year", "Area"]
        header = self.__tableView.horizontalHeader()
        for i in range(self.__model.columnCount()):
            column_name = self.__model.record().fieldName(i)
            if column_name in columns_to_display:
                self.__tableView.setColumnHidden(i, False)
            else:
                self.__tableView.setColumnHidden(i, True)
        self.__tableView.viewport().update()


    def getcurrentID(self):
        index = self.__tableView.currentIndex()
        currentindex = self.__proxyModel.mapToSource(index)
        currentID = self.__model.record(currentindex.row()).value(0)  # first column is keyword ID
        return currentID


    def lookupValueByID(self, table_name, id_value, field_name):
        try:
            conn = sqlite3.connect('radartoolkit/display/resources/dbs/AntarcticaProject.sqlite') # relative path
            if conn:
                cursor = conn.cursor()

                # Check if the table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                table_exists = cursor.fetchone()
                if not table_exists:
                    cursor.close()
                    conn.close()
                    self.sigShowMessage.emit(f"Table '{table_name}' does not exist.")
                    return None

                # Check if the field exists in the table
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [info[1] for info in cursor.fetchall()]
                if field_name not in columns:
                    cursor.close()
                    conn.close()
                    self.sigShowMessage.emit(f"Field '{field_name}' does not exist in table '{table_name}'.")
                    return None

                # Perform the lookup query
                query = f"SELECT {field_name} FROM {table_name} WHERE id = ?"
                cursor.execute(query, (id_value,))
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                return result

        except sqlite3.Error as e:
            self.sigShowMessage.emit(f"Database error: {e}")
            return None


    def __updated(self, i, r):
        # send updated signal
        self.__model.updated.emit(r.value('Project'), r.value('Affiliation'))


    def __showResult(self, text):
        # index -1 will be read from all columns
        # otherwise it will be read the current column number indicated by combobox
        field_index = self.__model.record().indexOf(self.__comboBox.currentText())
        self.__proxyModel.setFilterKeyColumn(field_index)

        regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
        # regular expression can be used
        self.__proxyModel.setFilterRegularExpression(regex)


    def __currentIndexChanged(self, idx):
        self.__showResult(self.__searchBar.getSearchBar().text())


    def getModel(self):
        return self.__model


    def getView(self):
        return self.__tableView



class MapWidget(QWidget):
    
    sigShowMessage = QtSignal(str)
    def __init__(self, table_name):
        super().__init__()
        self.__tableName = table_name
        self.__initUi()


    def __initUi(self):
        self.__model = SqlTableModel(self)
        self.__model.setTable(self.__tableName)
        self.__model.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.__model.beforeUpdate.connect(self.__updated)
        self.__model.select()

        self.__proxyModel = FilterProxyModel()
        self.__proxyModel.setSourceModel(self.__model)

        self.__tableView = QTableView()
        font = QtGui.QFont()
        font.setPointSize(10)
        self.__tableView.setModel(self.__proxyModel)
        self.__tableView.setFont(font)
        self.__tableView.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        
        columns_to_display = ["Project", "Affiliation", "Year", "Area"]

        record = self.__model.record()
        field_names = [record.fieldName(i) for i in range(record.count())]
        for i in range(len(field_names)):
            if field_names[i] in columns_to_display:
                pass
            else:
                self.__tableView.hideColumn(i)

        delegate = AlignDelegate()
        for i in range(self.__model.columnCount()):
            self.__tableView.setItemDelegateForColumn(i, delegate)

        self.__tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.__tableView.resizeColumnsToContents()
        self.__tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.__tableView.setSortingEnabled(True)
        self.__tableView.sortByColumn(0, Qt.AscendingOrder)

        self.__tableView.setCurrentIndex(self.__tableView.model().index(0, 0))

        self.__searchBar = InstantSearchBar()
        self.__searchBar.setPlaceHolder('Search...')
        self.__searchBar.searched.connect(self.__showResult)

        self.__comboBox = QComboBox()
        record = self.__model.record()
        field_names = [record.fieldName(i) for i in range(record.count())]
        items = ['All'] + columns_to_display
        for i in range(len(items)):
            self.__comboBox.addItem(items[i])
        self.__comboBox.currentIndexChanged.connect(self.__currentIndexChanged)

        lay = QHBoxLayout()
        lay.addWidget(self.__comboBox)
        lay.addWidget(self.__searchBar)
        lay.setContentsMargins(0, 0, 0, 0)
        btnWidget = QWidget()
        btnWidget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(btnWidget)
        lay.addWidget(self.__tableView)

        self.setLayout(lay)

        self.__showResult('')


    def getSelectedRecordDetails(self):
        selectedIndexes = self.__tableView.selectionModel().selectedRows()

        if not selectedIndexes:
            return None
        ids = []
        details = []
        projects =[]
        for index in selectedIndexes:
            if index.isValid():
                sourceIndex = self.__proxyModel.mapToSource(index)

                record = self.__model.record(sourceIndex.row())

                id_value = record.value('ID')
                ids.append(id_value)
                field_value = self.lookupValueByID(
                    self.__tableName, id_value, 'XY_File')
                if field_value:
                    details.append(field_value[0])
                project_value = self.lookupValueByID(
                    self.__tableName, id_value, 'Project')
                if project_value:
                    projects.append(project_value[0])
        return ids, details, projects


    def getAllFilteredRecords(self):
        record_count = self.__proxyModel.rowCount()
        ids = []
        values = []
        projects =[]
        for row in range(record_count):
            index = self.__proxyModel.index(row, 0)
            sourceIndex = self.__proxyModel.mapToSource(index)
            record = self.__model.record(sourceIndex.row())
            id = record.value('ID')
            value = record.value('XY_File')
            ids.append(id)
            values.append(value)
            project_value = record.value('Project')
            projects.append(project_value)
        return ids, values, projects


    def select_record_by_id(self, record_id):
        proxyModel = self.getProxyModel()
        model = self.getModel()
        selectionModel = self.__tableView.selectionModel()

        if record_id == -1:
            selectionModel.clearSelection()
            for row in range(model.rowCount()):
                sourceIndex = model.index(row, 0)
                proxyIndex = proxyModel.mapFromSource(sourceIndex)
                if proxyIndex.isValid():
                    selectionModel.select(proxyIndex, QItemSelectionModel.Select | QItemSelectionModel.Rows)
            verticalScrollBar = self.__tableView.verticalScrollBar()
            verticalScrollBar.setValue(0) 
        else:
            for row in range(model.rowCount()):
                current_id = model.record(row).value('ID')
                if current_id == record_id:
                    sourceIndex = model.index(row, 0)
                    proxyIndex = proxyModel.mapFromSource(sourceIndex)
                    if proxyIndex.isValid():
                        selectionModel.clearSelection()
                        selectionModel.setCurrentIndex(proxyIndex,
                                                    QItemSelectionModel.Select | QItemSelectionModel.Rows)
                        verticalScrollBar = self.__tableView.verticalScrollBar()
                        location = proxyIndex.row() - 3
                        if location >= 0:
                            verticalScrollBar.setValue(location)
                        else:
                            verticalScrollBar.setValue(0)
                    break
            else:
                print("Record ID not found in the model.")


    def getProxyModel(self):
        return self.__proxyModel


    def getcurrentID(self):
        index = self.__tableView.currentIndex()
        currentindex = self.__proxyModel.mapToSource(index)
        currentID = self.__model.record(currentindex.row()).value(
            0)  # first column is keyword ID
        print(currentID)
        return currentID


    def lookupValueByID(self, table_name, id_value, field_name):
        try:
            conn = sqlite3.connect('radartoolkit/display/resources/dbs/AntarcticaProject.sqlite') # relative path
            if conn:
                cursor = conn.cursor()
                query = f"SELECT {field_name} FROM {table_name} WHERE id = ?"
                cursor.execute(query, (id_value,))
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                return result
        except sqlite3.Error as e:
            self.sigShowMessage.emit(e)


    def __updated(self, i, r):
        # send updated signal
        self.__model.updated.emit(r.value('Project'), r.value('Affiliation'))


    def __showResult(self, text):
        # index -1 will be read from all columns
        # otherwise it will be read the current column number indicated by combobox
        field_index = self.__model.record().indexOf(self.__comboBox.currentText())
        self.__proxyModel.setFilterKeyColumn(field_index)
        regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
        # regular expression can be used
        self.__proxyModel.setFilterRegularExpression(regex)


    def __currentIndexChanged(self, idx):
        self.__showResult(self.__searchBar.getSearchBar().text())


    def getModel(self):
        return self.__model


    def getView(self):
        return self.__tableView


    def onrecordUpdated(self):
        self.__model.setTable(self.__tableName)
        self.__model.select()
        self.__showResult('')



def createConnection(self):

    db_path = 'radartoolkit/display/resources/dbs/AntarcticaProject.sqlite' # relative path
    conn = QSqlDatabase.addDatabase("QSQLITE")
    conn.setDatabaseName(db_path)

    is_new_database = False

    if not os.path.exists(db_path):
        # Database file doesn't exist, attempt to create a new one
        try:
            open(db_path, 'w').close()
            is_new_database = True
        except IOError as e:
            QMessageBox.critical(
                None,
                "QTableView Example - Error!",
                f"Failed to create database file: {e}",
            )
            return False

    if not conn.open():
        QMessageBox.critical(
            None,
            "QTableView Example - Error!",
            "Database Error: %s" % conn.lastError().databaseText(),
        )
        return False

    # Initialize the database default schema if the database is new
    if is_new_database:
        tables = {
            'Antarctica_Project': """
                CREATE TABLE IF NOT EXISTS Antarctica_Project (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                    Project TEXT NOT NULL,
                    Affiliation TEXT NOT NULL,
                    Year TEXT,
                    Area TEXT,
                    Affiliation_URL TEXT NOT NULL,
                    Project_HomePage TEXT,
                    Brief_Introductions_Categories TEXT,
                    Dataset_Links TEXT,
                    Data_Levels TEXT,
                    Radar_Instrument TEXT,
                    Surveying_Coverage TEXT,
                    Pub_Status TEXT,
                    Collaboration TEXT,
                    Data_Link TEXT,
                    Ref_DOI TEXT,
                    Extra_Info TEXT
                )
            """,
            'map_data': """
                CREATE TABLE IF NOT EXISTS map_data (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                    Project TEXT NOT NULL,
                    Affiliation TEXT NOT NULL,
                    Year TEXT,
                    Area TEXT,
                    XY_File TEXT NOT NULL
                )
            """
        }

        for table_name, create_statement in tables.items():
            dropTableQuery = QSqlQuery()
            dropTableQuery.prepare(f'DROP TABLE IF EXISTS {table_name}')
            if not dropTableQuery.exec():
                print(f"Error dropping table {table_name}: {dropTableQuery.lastError().text()}")

            createTableQuery = QSqlQuery()
            createTableQuery.prepare(create_statement)
            if not createTableQuery.exec():
                print(f"Error creating table {table_name}: {createTableQuery.lastError().text()}")

    return True