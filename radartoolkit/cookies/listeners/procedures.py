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


""" Abstract Procedure class.
    Got inspired by PyMeasure to realize the multiple threads and catch any output messages.
    
    Also this module provides a link to the `iceRadLib` module.
"""


import logging
import sys
import inspect
import re
from copy import deepcopy
from importlib.machinery import SourceFileLoader
import pint
import os

from cookies.listeners.parameters import (Parameter, Measurable, Metadata)
from cookies.bindings import QtSignal, QtSlot, QtCore, QtWidgets
from cookies.utils.plugin import Plugin


log = logging.getLogger()
log.addHandler(logging.NullHandler())

ureg = pint.get_application_registry()



class InteruptError(Exception):
    pass



class Procedure(Plugin):
    """
    Provides the base class of a procedure to organize the experiment
    execution. Procedures should be run by Workers to ensure that
    asynchronous execution is properly managed.

    .. code-block:: python

        procedure = Procedure()
        results = Results(procedure, data_filename)
        worker = Worker(results, port)
        worker.start()

    Inheriting classes should define the startup, execute, and shutdown
    methods as needed. The shutdown method is called even with a
    software exception or abort event during the execute method.

    If keyword arguments are provided, they are added to the object as
    attributes.
    """

    DATA_COLUMNS = []
    MEASURE = {}
    FINISHED, FAILED, ABORTED, QUEUED, RUNNING, LOST = 0, 1, 2, 3, 4, 5
    STATUS_STRINGS = {
        FINISHED: 'FINISHED', FAILED: 'FAILED',
        ABORTED:  'ABORTED',  QUEUED: 'QUEUED',
        RUNNING:  'RUNNING',  LOST:   'LOST' 
    }
    FLOWNODES = {}

    # Required execute parameters for the currently selected procedure
    # Should be overriden in descendants.
    PROCEDURE_PARAMS = [] 
    _parameters = {}
    _exeParameters = {}

    def __init__(self, moduleName=None, absPythonPath=None, **kwargs):
        """
        Constructor.
        """
        super(Procedure, self).__init__(moduleName=moduleName, 
                                        absPythonPath=absPythonPath
                                    )

        self.status = Procedure.QUEUED
        self.logger = None
        self.outputs = {}
        self.outputsRoot = {}

        self._updateParameters()
        self._updateMetadata()
        for key in kwargs:
            if key in self._parameters.keys():
                setattr(self, key, kwargs[key])
                log.info(f'Setting parameter {key} to {kwargs[key]}')


    @property
    def procedureName(self):
        return "PROCEDURE"
    

    @property
    def name(self):
        return "Unknown"


    @property
    def status(self):
        """
        Returns the status of the current activated procedure.
        """
        return self._status
    

    @status.setter
    def status(self, value):
        """
        Resets the status of the current activated procedure.
        """
        self._status = value
                     
    
    @staticmethod
    def parse_columns(columns):
        """Get columns with any units in parentheses.
        For each column, if there are matching parentheses containing text
        with no spaces, parse the value between the parentheses as a Pint unit. For example,
        "Source Voltage (V)" will be parsed and matched to :code:`Unit('volt')`.
        Raises an error if a parsed value is undefined in Pint unit registry.
        Return a dictionary of matched columns with their units.

        :param columns: List of columns to be parsed.
        :type record: dict
        :return: Dictionary of columns with Pint units.
        """
        units_pattern = r"\((?P<units>[\w/\(\)\*\t]+)\)"
        units = {}
        for column in columns:
            match = re.search(units_pattern, column)
            if match:
                try:
                    units[column] = ureg.Quantity(match.groupdict()['units']).units
                except pint.UndefinedUnitError:
                    raise ValueError(
                        f"Column \"{column}\" with unit \"{match.groupdict()['units']}\""
                        " is not defined in Pint registry. Check procedure "
                        "DATA_COLUMNS contains valid Pint units.")
        return units

    def gen_measurement(self):
        """Create MEASURE and DATA_COLUMNS variables for get_datapoint method."""
        self.MEASURE = {}
        for item, parameter in inspect.getmembers(self.__class__):
            if isinstance(parameter, Measurable):
                if parameter.measure:
                    self.MEASURE.update({parameter.name: item})

        if not self.DATA_COLUMNS:
            self.DATA_COLUMNS = Measurable.DATA_COLUMNS

        # Validate DATA_COLUMNS fit pymeasure column header format
        self.parse_columns(self.DATA_COLUMNS)


    def get_datapoint(self):
        data = {key: getattr(self, self.MEASURE[key]).value for key in self.MEASURE}
        return data


    def measure(self):
        data = self.get_datapoint()
        log.debug("Produced numbers: %s" % data)
        self.emit('results', data)


    def _updateParameters(self):
        """ Collects all the Parameter objects for the procedure and stores
        them in a meta dictionary so that the actual values can be set in
        their stead
        """
        if not self._parameters:
            self._parameters = {}
        for item, parameter in inspect.getmembers(self.__class__):
            if isinstance(parameter, Parameter):
                self._parameters[item] = deepcopy(parameter)
                if parameter.is_set():
                    setattr(self, item, parameter.value)
                else:
                    setattr(self, item, None)


    def parameters_are_set(self):
        """ Returns True if all parameters are set """
        for name, parameter in self._parameters.items():
            if getattr(self, name) is None:
                return False
        return True
    

    def check_parameters(self):
        """ Raises an exception if any parameter is missing before calling
        the associated function. Ensures that each value can be set and
        got, which should cast it into the right format. Used as a decorator
        @check_parameters on the startup method
        """
        for name, parameter in self._parameters.items():
            value = getattr(self, name)
            if value is None:
                raise NameError("Missing {} '{}' in {}".format(
                    parameter.__class__, name, self.__class__))
            

    def parameter_values(self):
        """ Returns a dictionary of all the Parameter values and grabs any
        current values that are not in the default definitions
        """
        result = {}
        for name, parameter in self._parameters.items():
            value = getattr(self, name)
            if value is not None:
                parameter.value = value
                setattr(self, name, parameter.value)
                result[name] = parameter.value
            else:
                result[name] = None
        return result


    def parameter_objects(self):
        """ Returns a dictionary of all the Parameter objects and grabs any
        current values that are not in the default definitions
        """
        result = {}
        for name, parameter in self._parameters.items():
            value = getattr(self, name)
            if value is not None:
                parameter.value = value
                setattr(self, name, parameter.value)
            result[name] = parameter
        return result
    

    def refresh_parameters(self):
        """ Enforces that all the parameters are re-cast and updated in the meta
        dictionary
        """
        for name, parameter in self._parameters.items():
            value = getattr(self, name)
            parameter.value = value
            setattr(self, name, parameter.value)


    def setParameters(self, parameters={}, except_missing=True):
        """ Sets a dictionary of parameters and raises an exception if additional
        parameters are present if except_missing is True
        """        
        for name, value in parameters.items():
            if name in self._parameters:
                self._parameters[name].value = value
                setattr(self, name, self._parameters[name].value)
            else:
                if except_missing:
                    raise NameError("Parameter '{}' does not belong to '{}'".format(
                        name, repr(self)))
                

    def setExeParameters(self, procedureItem, proc):
        # sanity check
        assert len(procedureItem) >= len(self.PROCEDURE_PARAMS), \
            "ProcedureItem should satisfy: {}. ".format(self.PROCEDURE_PARAMS) + \
            "However has missed important parameters. Please recheck the inputs."
        for idx, name in enumerate(self.PROCEDURE_PARAMS):
            value = procedureItem[idx]
            self._exeParameters[name] = value
        self._exeParameters['PROC'] = proc


    def _updateMetadata(self):
        """ Collects all the Metadata objects for the procedure and stores
        them in a meta dictionary so that the actual values can be set and used
        in their stead
        """
        self._metadata = {}

        for item, metadata in inspect.getmembers(self.__class__):
            if isinstance(metadata, Metadata):
                self._metadata[item] = deepcopy(metadata)

                if metadata.is_set():
                    setattr(self, item, metadata.value)
                else:
                    setattr(self, item, None)


    def evaluate_metadata(self):
        """ Evaluates all Metadata objects, fixing their values to the current value
        """
        for item, metadata in self._metadata.items():
            # Evaluate the metadata, fixing its value
            value = metadata.evaluate(parent=self, new_value=getattr(self, item))

            # Make the value of the metadata easily accessible
            setattr(self, item, value)


    def metadata_objects(self):
        """ Returns a dictionary of all the Metadata objects
        """
        return self._metadata
    

    def startup(self):
        """ 
        Executes the commands needed at the start-up of the measurement
        """
        pass


    def execute(self):
        """ 
        Preforms the commands needed for the processing itself. 
        During execution the shutdown method will always be run following this method.
        This includes when Exceptions are raised.
        """
        pass


    def shutdown(self):
        """ Executes the commands necessary to shut down the instruments
        and leave them in a safe state. This method is always run at the end.
        """
        pass

    def emit(self, topic, record):
        raise NotImplementedError('should be monkey patched by a worker')
    

    def should_stop(self):
        raise NotImplementedError('should be monkey patched by a worker')
    

    def get_estimates(self):
        """ Function that returns estimates that are to be displayed by
        the EstimatorWidget. Must be reimplemented by subclasses. Should
        return an int or float representing the duration in seconds, or
        a list with a tuple for each estimate. The tuple should consists
        of two strings: the first will be used as the label of the
        estimate, the second as the displayed estimate.
        """
        raise NotImplementedError('Must be reimplemented by subclasses')

    def __str__(self):
        result = repr(self) + "\n"
        for parameter in self._parameters.items():
            result += str(parameter)
        return result

    def __repr__(self):
        return "<{}(status={},parameters_are_set={})>".format(
            self.__class__.__name__, self.STATUS_STRINGS[self.status],
            self.parameters_are_set()
        )
    




class LostProcedure(Procedure):
    """ 
    Handles the case when a :class:`.Procedure` object whose dependt modules can not be imported
    as well as the class: `.Procedure` object can not be imported during loading in the :class:`.Results` class.
    """
    _API = None

    def __init__(self, parameters):
        super(LostProcedure, self).__init__()
        self._parameters = parameters


    def startup(self):
        raise NotImplementedError("LostProcedure can not be run")






class IceProcedure(Procedure):
    
    Responses = Parameter('Responses', default='')
    # Results = Parameter('Results', default='')

    DATA_COLUMNS = ['Responses']
    CSV_COLUMNS = []

    FLOWNODES = {
        'breakout': 'breakout *.dat into bxds.bin',
        'pik1': 'unfocused-SAR (coherent stacking, pulse compression, incoherent stacking)',
        'chirp_stats': 'calculate & evaluate chirp stats',
        'plot': 'print results as *.pdf'}
    
    DEFAULT_API = "iceradlib"
    DEFAULT_ABSPYPATH = "/Volumes/CAROLINA/RTK_UPDATING_CAROLINA/iceRadLib"

    def __init__(self, moduleName=None, absPythonPath=None, **kwargs):
        """
        Constructor.
        """
        moduleName = self.DEFAULT_API if moduleName is None else moduleName
        absPythonPath = self.DEFAULT_ABSPYPATH if absPythonPath is None else absPythonPath

        super(IceProcedure, self).__init__(moduleName=moduleName, 
                                           absPythonPath=absPythonPath,
                                           **kwargs
                                        )
        self._nodeName = ''
        self._sigMedia = NewSignalMedia()


    def __repr__(self) -> str:
        return type(self).__name__
    

    @property
    def nodeName(self):
        if len(self.PROCEDURE_PARAMS) == 0:
            return self._nodeName
        else:
            name = 'NOT SPECIFIED'
            return name
        
    
    @property
    def season(self):
        return self._exeParameters["SEASON"] if "SEASON" in self._exeParameters else " "
    

    @property
    def flight(self):
        return self._exeParameters["FLIGHT"] if "FLIGHT" in self._exeParameters else " "
    

    @property
    def radar(self):
        return self._exeParameters["RADAR"] if "RADAR" in self._exeParameters else " "
    

    @property
    def platform(self):
        return self._exeParameters["PLATFORM"] if "PLATFORM" in self._exeParameters else " "
        

    @property
    def sigMedia(self):
        # private, cannot be modified.
        return self._sigMedia


    def startup(self):
        raise NotImplementedError(
            "Descendant should override this functionality.")


    def execute(self, cls):

        try:
            instance = cls()
            if isinstance(instance, QtCore.QObject):
                instance._sigSendMsgs.connect(self._emitMsgs)
                instance._sigSendResults.connect(self._emitResults)

            # 
            instance._running(**self._exeParameters)
            self._emitMsgs(['progress', 100, True])

        except ModuleNotFoundError as mnf_ex:
            self._emitMsgs(['responses', f'Module not found: {mnf_ex}', False])
            raise ModuleNotFoundError(mnf_ex)

        except ImportError as imp_ex:
            self._emitMsgs(['responses', f'Import error: {imp_ex}', False])
            raise  # Ensure that the error propagates

        except Exception as ex:
            self._emitMsgs(['responses', f'{ex}', False])
            raise  # Ensure that the error propagates

        finally:
            # ensure the signals are disconnected
            if 'instance' in locals() and isinstance(instance, QtCore.QObject):
                instance._sigSendMsgs.disconnect(self._emitMsgs)
                instance._sigSendResults.disconnect(self._emitResults)


# try:
#     instance = cls()
#     if isinstance(instance, QtCore.QObject):
#         instance._sigSendMsgs.connect(self._emitMsgs)
#         instance._sigSendResults.connect(self._emitResults)

#     try:
#         instance._running(**self._exeParameters)
#     except Exception as ex:
#         self._emitMsgs(['responses', f'Failed during execution: {ex}', False])
#         raise  # Re-raise the exception to be handled elsewhere
#     else:
#         self._emitMsgs(['progress', 100, True])

# except ModuleNotFoundError as mnf_ex:
#     self._emitMsgs(['responses', f'Module not found: {mnf_ex}', False])
#     raise  # Ensure that the error propagates

# except ImportError as imp_ex:
#     self._emitMsgs(['responses', f'Import error: {imp_ex}', False])
#     raise  # Ensure that the error propagates

# except Exception as ex:
#     self._emitMsgs(['responses', f'Unexpected error: {ex}', False])
#     raise  # Ensure that the error propagates

# finally:
#     # ensure the signals are disconnected
#     if 'instance' in locals() and isinstance(instance, QtCore.QObject):
#         instance._sigSendMsgs.disconnect(self._emitMsgs)
#         instance._sigSendResults.disconnect(self._emitResults)





    def _sigNewProductsEmitted(self, label='', product=None):
        """ Descendant should override this functionality 
            when a new product is generated and required to be emitted. 
            ::product: product path
        """
        if product is not None and os.path.exists(product): 
            self._exeParameters['PROC'] = label
            self._exeParameters['PRODUCT'] = product
        self.sigMedia.emitNewProducts(self._exeParameters)


    @QtSlot(list)
    def _emitMsgs(self, results):
        """
        Receive message and do the emitting.

        Parameters
        ----------
        results: list
            [src, msg, True/False]
        src: str,
            depends on the contentd needed to present. E.g., progress, responses.
        msg: typing.Any,
            messages needed to display in the panel.
        `Ture/False`: bool,
            True if termination is required.
        """
        assert len(results) >= 2, "The results list must contain at least 2 elements."
        if results[0] == "responses" and len(results) >= 3:
            self.logger.log(results[2], results[1])
        
        # emit the messages to the display panel
        self.emit(results[0], results[1])


    @QtSlot(str)
    def _emitResults(self, results):
        """
        Only accept the results of folder or path, str.

        Parameters
        ----------
        results: str
        """
        # if isinstance(result, str) and os.path.exists(result):
        #     self._sigNewProductsEmitted(label='BO', product=result)
        #     self._setOutputs(result)
        self._setOutputs(results)


    def _setOutputs(self, results):
        """
        Sets up the outputs by recursionly going through the folder.
        Only accepts *.pdf
        """
        for keyName, result in results.items():
            if keyName not in self.outputs:
                self.outputs[keyName] = []
                self.outputsRoot[keyName] = result

            for root, _, files in os.walk(result):
                for file in files:
                    if file.lower().endswith(".pdf") and not file.lower().startswith(".") \
                        and file not in self.outputs[keyName]:
                        self.outputs[keyName].append(os.path.join(root, file))







class ProcedureWrapper:
    """ 
    Make the procedure wrapper.
    """
    
    def __init__(self, procedure):
        self.procedure = procedure


    def __getstate__(self):
        """
        Get all information needed to reconstruct the procedure.
        """

        self._parameters = self.procedure.parameter_values()
        self._class = self.procedure.__class__.__name__
        module = sys.modules[self.procedure.__module__]
        self._package = module.__package__
        self._module = module.__name__
        self._file = module.__file__

        state = self.__dict__.copy()
        del state['procedure']
        return state


    def __setstate__(self, state):
        
        self.__dict__.update(state)

        # Restore the procedure
        module = SourceFileLoader(self._module, self._file).load_module()
        cls = getattr(module, self._class)

        self.procedure = cls()
        self.procedure.setParameters(self._parameters)
        self.procedure.refresh_parameters()

        del self._parameters
        del self._class
        del self._package
        del self._module
        del self._file




class NewSignalMedia(QtCore.QObject):
    """ 
    As an inter-media to emit signal and connect signal-slot,
    since the procedure is not a PySide6.QtCore.QObject thus can not emit signal.
    """

    sigNewProducts = QtSignal(dict)
    sigShowMessage = QtSignal(str)

    def __init__(self, parent=None):
        super(NewSignalMedia, self).__init__(parent)

    def emitNewProducts(self, dct):
        # sanity check
        if 'PROC' in dct.keys() and 'PRODUCT' in dct.keys():
            self.sigNewProducts.emit(dct)
            


