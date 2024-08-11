#!/usr/bin.env python

from ..bindings import QtCore

def getWidgetState(qWindow):
    """ Gets the QWindow or QWidget state as a QByteArray.

        Since Qt does not provide this directly we hack this by saving it to the QSettings
        in a temporary location and then reading it from the QSettings.

        :param widget: A QWidget that has a saveState() methods
    """
    settings = QtCore.QSettings()
    settings.beginGroup('temp_conversion')
    try:
        settings.setValue("winState", qWindow.saveState())
        return bytes(settings.value("winState"))
    finally:
        settings.endGroup()


def Hex2RGB(hex):
    if '#' in hex:
        hex = hex.replace('#', '')

    r = int(hex[0:2],16)
    g = int(hex[2:4],16)
    b = int(hex[4:6], 16)
    rgb = [r,g,b]
    return rgb