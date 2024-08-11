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


""" Various functions related to logging
"""


import logging
import logging.config
import os.path
import json

from ..utils.dirs import ensureDirectoryExists, normRealPath, rtkLogDirectory
from ..utils.misc import replaceStringsInDict
from ..settings import LOGGING_FILE

logger = logging.getLogger(__name__)


def findStreamHandlersInConfig():
    """ Searches for a handlers with 'stream' their name. Returns a list of handlers.
    """
    rootLogger = logging.getLogger()
    #logger.debug("Searching for Handlers in the root logger haveing 'stream' in their name")
    foundHandlers = []
    for handler in rootLogger.handlers:
        #logger.debug("  handler name: {}".format(handler.name))
        if 'stream' in handler.name.lower():
            foundHandlers.append(handler)

    return foundHandlers


def initLogging(configFileName=None, streamLogLevel=None):
    """ Configures logging given a (JSON) config file name.

        If configFileName is None, load the default logging.

        :param configFileName: JSON file with log config.
        :param streamLogLevel: If given it overrides the log level of StreamHandlers in the config. All messages below
            this level will be suppressed.
    """
    if configFileName is None:
        configFileName = LOGGING_FILE

    with open(configFileName, 'r') as stream:
        lines = stream.readlines()
        cfgLines = ''.join(lines)

    # Ensure the directory exists if @logDir@ is in the JSON file.
    logDir = rtkLogDirectory()
    if '@logDir@' in cfgLines:
        ensureDirectoryExists(logDir)

    configDict = json.loads(cfgLines)
    configDict = replaceStringsInDict(configDict, "@logDir@", logDir)

    logging.config.dictConfig(configDict)

    if streamLogLevel:
        # Using getLevelName to get the level number. This undocumented behavior has been upgraded
        # to documented behavior in Python 3.4.2.
        # See https://docs.python.org/3.4/library/logging.html#logging.getLevelName
        levelNr = logging.getLevelName(streamLogLevel.upper()) - 1
        #logging.disable(levelNr)

        for streamHandler in findStreamHandlersInConfig():
            logger.debug("Setting log level to {} in handler: {} ".format(levelNr, streamHandler))
            streamHandler.setLevel(levelNr)

    logging.info("Initialized logging from: '{}'".format(normRealPath(configFileName)))
    logging.info("Default location of log files: '{}'".format(logDir))


def log_dictionary(dictionary, msg='', logger=None, level='debug', item_prefix='    '):
    """ Writes a log message with key and value for each item in the dictionary.

        :param dictionary: the dictionary to be logged
        :type dictionary: dict
        :param name: An optional message that is logged before the contents
        :type name: string
        :param logger: A logging.Logger object to log to. If not set, the 'main' logger is used.
        :type logger: logging.Logger or a string
        :param level: log level. String or int as described in the logging module documentation.
            Default: 'debug'.
        :type level: string or int
        :param item_prefix: String that will be prefixed to each line. Default: two spaces.
        :type item_prefix: string
    """
    level_nr = logging.getLevelName(level.upper())

    if logger is None:
        logger = logging.getLogger('main')

    if msg :
        logger.log(level_nr, "Logging dictionary: {}".format(msg))

    if not dictionary:
        logger.log(level_nr,"{}<empty dictionary>".format(item_prefix))
        return

    max_key_len = max([len(k) for k in dictionary.keys()])
    for key, value in sorted(dictionary.items()):
        logger.log(level_nr, "{0}{1:<{2}s} = {3}".format(item_prefix, key, max_key_len, value))


def make_log_format(
        ascTime = True,
        processId = False,
        threadName = False,
        threadId = False,
        fileLine = True,
        loggerName = False,
        level = True):
    """ Creates a format string to use in logging.basicConfig.

        Use example:
            logging.basicConfig(level="DEBUG", format=makeLogFormat(fileLine=False))
    """
    parts = []
    if ascTime:
        parts.append('%(asctime)s')

    if processId:
        parts.append('pid=%(process)5d')

    if threadName:
        parts.append('%(threadName)15s')

    if threadId:
        parts.append('id=0x%(thread)x')

    if fileLine:
        parts.append('%(filename)25s:%(lineno)-4d')

    if loggerName:
        parts.append("%(name)30s")

    if level:
        parts.append('%(levelname)-7s')

    parts.append('%(message)s')
    return " : ".join(parts)