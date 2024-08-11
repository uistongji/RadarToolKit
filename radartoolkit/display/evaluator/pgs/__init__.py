#!/usr/bin.env python

import logging

logger = logging.getLogger(__name__)

try:
    import pyqtgraph as pg
except Exception as ex:
    logger.exception(ex)
    raise ImportError("PyQtGraph 0.10.0 or higher required")

logger.debug("Imported PyQtGraph: {}".format(pg.__version__))

def setPgConfigOptions(**kwargs):
    """ Sets the PyQtGraph config options and emits a log message
    """
    for key, value in kwargs.items():
        logger.debug("Setting PyQtGraph config option: {} = {}".format(key, value))
        print("Setting PyQtGraph config option: {} = {}".format(key, value))

    pg.setConfigOptions(**kwargs)


# Sets some config options
setPgConfigOptions(exitCleanup=False, crashWarning=True,
                   antialias=False,     # Anti aliasing of lines having width > 1 may be slow (OS-X)
                   leftButtonPan=True,  # If False, left button drags a rubber band for zooming
                   foreground='k',      # Default foreground color for axes, labels, etc.
                   background='w')      # Default background for GraphicsWidget