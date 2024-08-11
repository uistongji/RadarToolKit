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


""" RadarToolKit(RTK).
    The current version of RTK only supports the functions for the Ice Sounding Radar (ISR).
    The Rest is still under development and will be provided in the future.

    Five modules shall be installed and imported correctly in order to empower the functionalities.
    Under some restricted policies, some parts of the modules can only be obtained with request.
    
    # Contact: ...
"""


from __future__ import print_function

import logging, sys, os, argparse

from info import PROJECT_NAME, EXIT_CODE_RESTART, VERSION
from display.widgets.misc import setApplicationStyleSheet, setApplicationQtStyle

logger = logging.getLogger('RadarToolKit')
logging.basicConfig(level='DEBUG',
                    stream=sys.stderr,
                    format='%(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-8s: %(message)s')


def browse(registeredFiles=None,
           inspectorFullName=None,
           qtStyle=None,
           styleSheet=None,
           settingsFile=None):
    """ Opens the main window for the persistent settings and executes the application.

        :param registeredFiles: dict={'func': [fileNames/filefolders]} which will directl added 
            to the repository/in the process of 'func'. So far, func is only supported with
            'bo'/'pik1'/'view' (do nothing but added to the repository).
        :param inspectorFullName: The full path name of the inspector will be imported.
        :param qtStyle: name of qtStyle (E.g. fusion).
        :param styleSheet: a path to an optional Qt Cascading Style Sheet.
        :param settingsFile: file with persistent settings. If None a default will be used.
    """
    # creates and runs the RTKApplication in a loop to 'restart' application when the plugin registry was edited.
    while True:
        logger.debug("<entrace::browse> starting the browsed window ...")
        rtkApplication = _createRTKApplication(
            registeredFiles=registeredFiles,
            inspectorFullName=inspectorFullName,
            qtStyle=qtStyle,
            styleSheet=styleSheet,
            settingsFile=settingsFile)
        
        exitCode = rtkApplication.execute()

        logger.debug("<entrace::browse> RTKApp finished with the exit code: {}".format(exitCode))
        if exitCode != EXIT_CODE_RESTART:
            return exitCode
        else:
            logger.info("----- Restart requested. The Qt event loop will be restarted. -----\n")


def _createRTKApplication(registeredFiles=None,
                          inspectorFullName=None,
                          qtStyle=None,
                          styleSheet=None,
                          settingsFile=None
                          ):
    """ creates an RTK-Application """

    from display.bindings import QtWidgets, QtCore
    from rtkapp import RTKApplication

    rtkApp = RTKApplication(settingsFile, inspectorFullName, registeredFiles)
    rtkApp.loadSettings(inspectorFullName)

    try:
        QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    except Exception as ex:
        logger.debug("<entrace::browse> AA_UseHighDpiPixmaps not available: {}.".format(ex))
    
    if qtStyle:
        availableStyles = QtWidgets.QStyleFactory.keys()
        if qtStyle not in availableStyles:
            logger.warning("<entrace::browse> Qt style '{}' is not available on this computer. Use one of: {}"
                           .format(qtStyle, availableStyles))
        else:
            setApplicationQtStyle(qtStyle)

    if not os.path.exists(styleSheet):
        logger.debug("<entrace::browse> Stylesheet not found: {}".format(styleSheet))
    setApplicationStyleSheet(styleSheet)

    return rtkApp


def infoRetrival(args, DEBUGGING=False):
    """ retrival relevant information and returns a dict """

    from rtkapp import RTKApplication

    rtkApp = RTKApplication(args.settingsFile)
    logger.debug("<entrace::infoRetrival> '# RadarToolKit App' registered. ")

    info = {}

    if DEBUGGING:
        info['version'] = "{} version: {}".format(PROJECT_NAME, VERSION)
        info['inspectors'] = []
        for regItem in rtkApp.inspectorRegistry.items:
            info['inspectors'].append({regItem.name: regItem.info}) 
        info['rtis'] = []
        for rtiItem in rtkApp.fileRegistry.items:
            info['rtis'].append({rtiItem.name: regItem.data['info']})
    else:
        if args.version:
            info['version'] = "{} version: {}".format(PROJECT_NAME, VERSION)
    
        if args.list_inspectors:
            info['inspectors'] = []
            for regItem in rtkApp.inspectorRegistry.items:
                info['inspectors'].append({regItem.name: regItem.info}) 
    
        if args.list_fileTypes:
            info['rtis'] = []
            for rtiItem in rtkApp.fileRegistry.items:
                info['rtis'].append({rtiItem.name: regItem.data['info']})

        if args.intro:
            pass
    return info


def configPrintAndModify(args):

    logger.info("Python version: {}".format(sys.version).replace('\n', ''))
    from display.bindings import API_PYSIDE6, PYSIDE_VERSION, QT_VERSION
    logger.info("Using {} Python Qt bindings (PYSIDE_VERSION: {}, QT_VERSION: {})"
                .format(API_PYSIDE6, PYSIDE_VERSION, QT_VERSION))

    args.qtStyle = os.environ.get("QT_STYLE_OVERRIDE", "Fusion") if not args.qtStyle else args.qtStyle
    args.styleSheet = os.environ.get("RTK_STYLE_SHEET", '') if not args.styleSheet else args.styleSheet

    logger.info("Using qt style: {}".format(args.qtStyle))

    from display.settings import CSS_DIR
    if not args.styleSheet:
        styleSheet = os.path.join(CSS_DIR, "rtk.css")
        description = "default"
    else:
        styleSheet = os.path.abspath(args.styleSheet)
        description = "user-defined"
    logger.info("Using {} style sheet: {}".format(description, styleSheet))
    return args


def main():
    """ starts the RTK application & mainwindow """
    
    from display.utils.misc import removeProcessSerialNumber
    from display.utils.logs import initLogging

    parser = argparse.ArgumentParser(description="{} version: {}".format(PROJECT_NAME, VERSION))

    parser.add_argument('-v', '--version', action='store_true',
                        help="Prints the program version and exits")
    parser.add_argument('registeredFiles', metavar='FILE', nargs='*',
                        help="""Dict={'func': [fileNames/filefolders]} which will directl added
                            to the repository/in the process of 'func'. So far, func is only supported with
                            'bo'/'pik1'/'view' (do nothing but added to the repository). """)
    parser.add_argument('-i', '--inspector', dest='inspector',
                        help="""The name of inspector that will be opened at the start-up, e.g., ImagePlot2D.""")
    parser.add_argument('--list-inspectors', dest='list_inspectors', action = 'store_true',
        help="""Prints a list of available inspectors for the -i option, and exits.""")
    parser.add_argument('--list-availbleRegistry', dest='list_fileTypes', action = 'store_true',
        help="""Prints a list of available file types that can be loaded and exits.""")
    parser.add_argument('--IntroducationOfRTK', dest='intro', action = 'store_true',
        help="""Prints the RadarToolKit information and exits.""") 
    
    # ---------------- config parameters group ---------------- # 
    cfgGroup = parser.add_argument_group(
        "config options", description="Options related to style and configuration.")
    cfgGroup.add_argument('--qt-style', dest='qtStyle', help='Qt style. E.g.: fusion')
    cfgGroup.add_argument('--qss', dest='styleSheet',
                        help="Name of Qt Style Sheet file. If not set, the RTK default style "
                             "sheet will be used.")
    cfgGroup.add_argument('-c', '--config-file', metavar='FILE', dest='settingsFile',
        help="Configuration file with persistent settings. When using a relative path the settings "
             "file is loaded/saved to the radartoolkit settings directory.")
    cfgGroup.add_argument('--log-config', metavar='FILE', dest='logConfigFileName',
                        help='Logging configuration file. If not set a default will be used.')
    cfgGroup.add_argument('-l', '--log-level', dest='log_level', default='',
        help="Log level. If set, only log messages with a level higher or equal than this will be "
             "printed to screen (stderr). Overrides the log level of the StreamHandlers in the "
             "--log-config file. Does not alter the log level of log handlers that write to a "
             "file.",
        choices=('debug', 'info', 'warning', 'error', 'critical'))

    args = parser.parse_args(removeProcessSerialNumber(sys.argv[1:]))

    # setup logging configuration
 
    if any([args.version, args.list_inspectors, 
            args.list_fileTypes, args.intro]):
        info = infoRetrival(args)
       
        exitCode = 0 # if usr clicked any buttons
        sys.exit(exitCode) 

    logger.info("######################################")
    logger.info("---   Starting RadarToolKit(RTK)   ---")
    logger.info("######################################")
    logger.info("{} version: {}".format(__doc__, VERSION))

    logger.debug("argv: {}".format(sys.argv))
    logger.debug("Entrance to RTK module file: {}".format(__file__))
    logger.debug("PID: {}".format(os.getpid()))

    logger.info("----------  Configuration  ----------")
    args = configPrintAndModify(args)

    # browse will create an RTKApplication with one-specified mainWindow
    browse(registeredFiles=args.registeredFiles,
           inspectorFullName=args.inspector,
           qtStyle=args.qtStyle,
           styleSheet=args.styleSheet,
           settingsFile=args.settingsFile)
           
    logger.info("Launched: {}".format(PROJECT_NAME))

if __name__ == "__main__":

    main() 
