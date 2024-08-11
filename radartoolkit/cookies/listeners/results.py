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


""" Results class.
    Got inspired by PyMeasure to realize the multiple threads and catch any output messages.
    
    Also this module provides a link to the `iceRadLib` module.
"""


import logging, os, sys
from importlib.machinery import SourceFileLoader
import pandas as pd

from .procedures import Procedure
from ..bindings import QtSlot, QtWidgets


log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())



class CSVFormatter(logging.Formatter):
    # inherited from: logging.Formatter 
    # -> Formatter instances are used to convert a LogRecord to text in detail.
    """ creates a csv formatter for a given list of columns (=header).
        
        :param columns(list): list of the column names
        :paran delimiter(str): delimiter between columns
    """
    def __init__(self, columns, delimiter='#', LINE_BREAK='\n'):
        super(CSVFormatter, self).__init__()
        self.columns = columns
        self.units = Procedure.parse_columns(columns)
        self.delimiter = delimiter
        self.LINE_BREAK = LINE_BREAK

    def format(self, record={}):
        """Formats a record as csv.
            :param record(dct): record to format.
            :type record: dict
            :return: a string
        """
        line = []
        # check_class(record, dict, allow_none=False)
        for key, values in record.items():
            if "STEP" in key or 'COMPLETED TIME' == key:
                line.append(f" {key}: {values}")
            else:
                line.append(f" {key}: ")
                for value in values:
                    line.append(f"\t{value}")
        line.append("-"*37)
        line = [self.delimiter + h for h in line]

        return Results.LINE_BREAK.join(line)

    def format_header(self):
        return self.delimiter.join(self.columns)



# This should be re-written for information display
class Results:
    """ The Results class provides a convenient interface to reading and
    writing data in connection with a :class:`.Procedure` object.

    :cvar COMMENT: The character used to identify a comment (default: #)
    :cvar DELIMITER: The character used to delimit the data (default: ,)
    :cvar LINE_BREAK: The character used for line breaks (default \\n)
    :cvar CHUNK_SIZE: The length of the data chuck that is read

    :param procedure: Procedure object
    :param logging: The data filename where the data is or should be stored
    """

    COMMENT = '#'
    DELIMITER = ':'
    LINE_BREAK = "\n"
    CHUNK_SIZE = 1000


    def __init__(self, procedure, logName=None, logging=None):
        if not isinstance(procedure, Procedure):
            raise ValueError("Results require a Procedure object")
        self.procedure = procedure
        self.procedure_class = procedure.__class__
        self.parameters = procedure.parameter_objects()
        self._header_count = -1
        self._metadata_count = -1

        self.formatter = CSVFormatter(columns=self.procedure.DATA_COLUMNS)

        if isinstance(logging, (list, tuple)):
            loggings, logging = logging, logging[0]
        else:
            loggings = [logging]
        self.logging = logging
        self.loggings = loggings
        

        # initialize and add logger
        self.logName = os.path.basename(logName)
        self.logFileName = logName
        self.logger = self._setupLogger()
        self.procedure.logger = self.logger
        
        self._data = None

        if os.path.exists(logging): # assume header is already written
            self.reload()                     # perform a full data reloading of the existed file data.
            self.procedure.status = Procedure.FINISHED
        else:
            for filename in self.loggings:
                with open(filename, 'w') as fd:
                    fd.write(self.header())
                    fd.write(self.LINE_BREAK)
                    # fd.write(self.labels())

                self._data = None


    def __getstate__(self):
        """ Gets all information required to reconstruct the procedure
        """
        self._parameters = self.procedure.parameter_values()
        self._class = self.procedure.__class__.__name__
        module = sys.modules[self.procedure.__module__]
        self._package = module.__package__
        self._module = module.__name__
        self._file = module.__file__

        state = self.__dict__.copy()
        del state['procedure']
        del state['procedure_class']
        return state
    

    def __setstate__(self, state):
        self.__dict__.update(state)

        # restore the procedure
        module = SourceFileLoader(self._module, self._file).load_module()
        cls = getattr(module, self._class)

        self.procedure = cls()
        self.procedure.setParameters(self._parameters)
        self.procedure.refresh_parameters()

        self.procedure_class = cls

        del self._parameters
        del self._class
        del self._package
        del self._module
        del self._file


    def header(self):
        """ Returns a text header to accompany a datafile 
            so that the procedure can be reconstructed.
        """
        h = []
        # procedure = self.procedure_class
        # procedure = re.search("'(?P<name>[^']+)'",
        #                       repr(self.procedure_class)).group("name") 
        h.append(" Procedure: <%s>" % self.procedure.__repr__())
        h.append(" Processing Flow:") 
        for name, explaination in self.procedure.FLOWNODES.items():
            h.append("\t*{}: {}".format(name, explaination))
        h.append('')
        h.append("-------------- Details --------------")
        self._header_count = len(h)
        h = [Results.COMMENT + line for line in h] # commen each line
        return Results.LINE_BREAK.join(h) # + Results.COMMENT + Results.LINE_BREAK
    

    def labels(self):
        """ Returns the columns labels as a string to be written to the file
        """
        return self.formatter.format_header() + Results.LINE_BREAK
    

    def format(self, data):
        """ Returns a formatted string containing the data to be written to a file
        """
        return self.formatter.format(data)


    def reload(self):
        """ Preforms a full reloading of the file data, 
            neglecting any changed in the comments
        """
        chunks = pd.read_csv(
            self.logging,
            comment=Results.COMMENT,
            chunksize=Results.CHUNK_SIZE,
            iterator=True)
        try:
            self._data = pd.concat(chunks, ignore_index=True)
        except Exception:
            self._data = chunks.read()


    def __repr__(self):
        # print(object): <**.xx object at space>
        return "<{}(filename='{}',procedure={},shape={})>".format(
            self.__class__.__name__, self.logging,
            self.procedure.__class__.__name__,
            self.data.shape)
    

    def store_metadata(self):
        pass


    def _setupLogger(self):
        if self.logName is None:
            self.logger = None
            return
        
        logger = logging.getLogger(self.logName)
        logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(self.logFileName) # file handler
        fh.setLevel(logging.DEBUG)

        # stream handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)
        return logger
    

    def closeLogger(self):
        handlers = self.logger.handlers[:]
        for handler in handlers:
            handler.close()
            self.logger.removeHandler(handler)

    @property
    def nodeName(self):
        return self.procedure.nodeName
    
    
    @property
    def procType(self):
        return self.procedure._exeParameters['PROC']
    





