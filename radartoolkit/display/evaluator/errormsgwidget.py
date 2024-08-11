#!/usr/bin.env python

""" Widgets for displaying error messages.
"""

from ..widgets.basepanel import BasePanel
from ..widgets.imagebox import ImageBox
from ..bindings import QtWidgets, Qt, QtGui
from ..settings import ICONS_DIR

import logging, os


logger = logging.getLogger(__name__)


class ErrorMsgWidget(BasePanel):

    def __init__(self, parent=None, msg=''):
        
        super(ErrorMsgWidget, self).__init__(parent=parent)

        self.borderColor = QtGui.QColor(190, 190, 190)
        self.hoverBackground = QtGui.QColor(245, 245, 245)
        self.borderRadius = 26
        self.borderWidth = 6

        self._initErrorMsgWidget()
    

    def _initErrorMsgWidget(self):

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

        self.imagebox = ImageBox(os.path.join(ICONS_DIR, "warn.png"),keepAspectRatio=True)
        self.warnmsglabel = QtWidgets.QLabel("Error Message Display")
        self.layout.addWidget(self.imagebox)
        self.layout.addWidget(self.warnmsglabel, alignment=Qt.AlignHCenter)

    def paintEvent(self, event):

        pt = QtGui.QPainter()
        pt.begin(self)
        pt.setRenderHint(QtGui.QPainter.Antialiasing, on=True)

        pen = QtGui.QPen(self.borderColor, self.borderWidth, Qt.DotLine, Qt.RoundCap)
        pt.setPen(pen)

        pt.drawRoundedRect(self.borderWidth, self.borderWidth, self.width()-self.borderWidth*2, self.height() - self.borderWidth*2, self.borderRadius, self.borderRadius)

        pt.pen()
        


    def setError(self, msg=None):

        if msg is not None:
            self.warnmsglabel.setText(msg)