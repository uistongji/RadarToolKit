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


""" ImageBox Widget
"""


import pathlib
import requests

from display.bindings import Qt, QtCore, QtWidgets, QtGui



class ImageBox(QtWidgets.QLabel):
    def __init__(self, source=None, parent=None, keepAspectRatio=True, smoothScale=True, ratio=None):
        
        super().__init__()

        self.source = source
        self.animated = False
        self.ratio = ratio

        self.keepAspectRatio = keepAspectRatio
        self.smoothScale = smoothScale

        if self.source is not None: self.setSource(self.source)


    def __repr__(self):
        return f"<pyqt5Custom.ImageBox(animated={self.animated})>"


    def setSource(self, source):
        self.source = source

        if isinstance(self.source, pathlib.Path):
            self.source = str(self.source)

        if isinstance(self.source, str):

            if self.source.startswith("http"):

                if self.source.endswith(".gif"):
                    r = requests.get(self.source)

                    with open("temp.gif", "wb") as f:
                        f.write(r.content)

                    self.animated = True
                    self.orgmovie = QtGui.QMovie("temp.gif")
                    self.movie = self.orgmovie
                    self.setMovie(self.movie)
                    self.movie.start()

                else:
                    r = requests.get(self.source)

                    self.animated = False
                    self.orgpixmap = QtGui.QPixmap.fromImage(QtGui.QImage.fromData(r.content))
                    self.pixmap = QtGui.QPixmap(self.orgpixmap)
                    self.setPixmap(self.pixmap)

            else:
                if source.endswith(".gif"):
                    self.animated = True
                    self.movie =QtGui.QMovie(source)
                    self.setMovie(self.movie)
                    self.movie.start()

                else:
                    self.animated = False
                    self.orgpixmap = QtGui.QPixmap(source)
                    self.pixmap = QtGui.QPixmap(source)
                    self.setPixmap(self.pixmap)

        elif isinstance(self.source, QtGui.QPixmap):
            self.animated = False
            self.orgpixmap = QtGui.QPixmap(self.source)
            self.pixmap = QtGui.QPixmap(self.source)
            self.setPixmap(self.pixmap)

        elif isinstance(self.source, QtGui.QImage):
            self.animated = False
            self.orgpixmap = QtGui.QPixmap.fromImage(self.source)
            self.pixmap = QtGui.QPixmap.fromImage(self.source)
            self.setPixmap(self.pixmap)

        elif isinstance(self.source, QtGui.QMovie):
            self.animated = True
            self.movie = QtGui.QMovie(self.source)
            self.setMovie(self.movie)
            self.movie.start()

        else:
            raise TypeError(f"QImage(source: Union[str, pathlib.Path, QPixmap, QImage, QMovie]) -> Argument 1 has unexpected type '{type(self.source)}'")

        self.resizeEvent(None)


    def resizeEvent(self, event):
        w, h = self.width(), self.height()

        if self.ratio != None: 
            t = self.ratio[0]
            k = self.ratio[1]
        else:
            t = (Qt.FastTransformation, Qt.SmoothTransformation)[self.smoothScale]
            k = (Qt.IgnoreAspectRatio, Qt.KeepAspectRatio)[self.keepAspectRatio]

        if self.animated:
            self.movie.setScaledSize(QtCore.QSize(w, h))

        else:
            self.pixmap = self.orgpixmap.scaled(w, h, aspectMode=k, mode=t, )
            self.setPixmap(self.pixmap)