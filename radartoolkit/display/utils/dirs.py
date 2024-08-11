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


r""" Default config and log directories under the different platforms.

    Config files are stored in a subdirectory of the baseConfigLocation. Log files are stored
    in a subdirectory of the baseLocalDataLocation. These are: ::

        Windows:
            baseConfigLocation    -> C:\Users\<user>\AppData\Local
            baseLocalDataLocation -> C:\Users\<user>\AppData\Local

        OS-X:
            baseConfigLocation    -> ~/Library/Preferences
            baseLocalDataLocation -> ~/Library/Application Support

        Linux:
            baseConfigLocation    -> ~/.config
            baseLocalDataLocation -> ~/.local/share

    See http://doc.qt.io/qt-5/qsettings.html#platform-specific-notes.
"""

import logging
import os.path
import platform

from info import ORGANIZATION_NAME, SCRIPT_NAME

logger = logging.getLogger(__name__)


def homeDirectory() -> str:
    """ Returns the user's home directory.

        See: https://stackoverflow.com/a/4028943/625350
    """
    return os.path.expanduser("~")


def normRealPath(path):
    """ Returns the normalized real path.

        If the path is empty or None it is returned as-is. This is to prevent expanding to the
        current directory in case of undefined paths.
    """
    if path:
        return os.path.normpath(os.path.realpath(path))
    else:
        return path


def ensureDirectoryExists(dirName):
    if not os.path.exists(dirName):
        logger.info("Creating directory: {}".format(normRealPath(dirName)))
        os.makedirs(dirName)


def checkFileExists(fileName) -> bool:
    """ checks whether file exists """
    return os.path.exists(fileName)


def ensureFileExists(pathName) -> str:
    """ Creates an empty file file if it doesn't yet exist. Also creates necessary directory path.

        :returns: the normRealPath of the path name.
    """      
    pathName = normRealPath(pathName)
    dirName, fileName = os.path.split(pathName)
    ensureDirectoryExists(dirName)

    if not os.path.exists(pathName):
        logger.info("Creating empty file: {}".format(pathName))
        with open(pathName, 'w') as f:
            f.write('')
    
    assert os.path.isfile(pathName), \
        "File does not exist or is a directory: {!r}".format(pathName)
    return pathName



################
# Config files #
################

def baseConfigLocation() -> str:
    r""" Gets the base configuration directory (for all applications of the user).

        See the module doc string at the top for details.
    """
    # Same as QtCore.QStandardPaths.AppConfigLocation, but without having to import Qt
    sysName = platform.system()

    if sysName == "Darwin":
        configDir = os.path.join(homeDirectory(), 'Library', 'Preferences')
    elif sysName == "Linux":
        configDir = os.path.join(homeDirectory(), '.config')
    elif sysName == "Windows":
        configDir = os.environ.get("LOCALAPPDATA", os.path.join(homeDirectory(), 'AppData', 'Local'))
    else:
        raise AssertionError("Unknown Operating System: {}".format(sysName))

    assert configDir, "No baseConfigLocation found."
    return normRealPath(configDir)


def rtkConfigDirectory() -> str:
    """ Gets the RTK configuration directory.
        The config directory is platform dependent. (See the module doc string at the top).
    """
    return os.path.join(baseConfigLocation(), ORGANIZATION_NAME, SCRIPT_NAME)


def rtkLogDirectory():
    r""" Returns the directory where RTK can store its log files.

        This is the 'logs' subdirectory of the rtkLocalDataDirectory()
    """
    return os.path.join(rtkConfigDirectory(), 'logs')

