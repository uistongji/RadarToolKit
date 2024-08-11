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


""" Worker class.
    Got inspired by PyMeasure to realize the multiple threads and catch any output messages.
    
    Also this module provides a link to the `iceRadLib` module.
"""


import logging
from queue import Queue

from cookies.listeners.recorders import Recorder
from cookies.listeners.procedures import Procedure
from cookies.listeners.results import Results
from cookies.listeners.thread import StoppableThread



log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())



class Worker(StoppableThread):
    """ Worker runs the procedure and emits information about
        the procedure.
        In a child thread, a Recorder is run to write the results too.
    """
    def __init__(self, results, log_queue=None, log_level=logging.INFO):
        super(Worker, self).__init__()

        if not isinstance(results, Results):
            raise ValueError("Invalid Results object during Worker construction")
        self.results = results
        self.results.procedure.check_parameters()
        self.results.procedure.status = Procedure.QUEUED

        self.recorder = None
        self.recorder_queue = Queue()

        self.monitor_queue = Queue()
        if log_queue is None:
            log_queue = Queue()
        self.log_queue = log_queue
        self.log_level = log_level

        global log
        log = logging.getLogger()
        log.setLevel(self.log_level)

        self.context = None
        self.publisher = None
        self.procedure = None # will be changed in self.run()
        
    def join(self, timeout=0):
        try:
            super().join(timeout)
        except (KeyboardInterrupt, SystemExit):
            log.warning("User stopped Worker join prematurely")
            self.stop()
            super().join(0)
    
    def emit(self, topic, record):
        """ Emits data of some topic 
        """
        log.debug("Emitting message: %s %s", topic, record)
        if topic == 'results':
            self.recorder.handle(record)
        elif topic == 'status' or topic == 'progress' or topic == 'responses':
            self.monitor_queue.put((topic, record))

    def handle_abort(self):
        log.exception("User stopped Worker execution prematurely.")
        self.update_status(Procedure.ABORTED)
    
    def handle_error(self):
        log.exception("Worker caught an error on %r", self.procedure)
        # traceback_str = traceback.format_exc()
        # self.emit('error', traceback_str)
        self.update_status(Procedure.FAILED)

    def handle_selfabort(self):
        self.emit('error', "NOT SUPPORTED FUNCTION HANDLE.")
        self.update_status(Procedure.FAILED)


    def update_status(self, status):
        self.procedure.status = status
        self.emit('status', status)

    def shutdown(self):

        if self.procedure is not None:
            self.procedure.shutdown()
            if self.should_stop() and self.procedure.status == Procedure.RUNNING:
                self.update_status(Procedure.ABORTED)
            elif self.procedure.status == Procedure.RUNNING:
                self.update_status(Procedure.FINISHED)
                self.emit('progress', 100.)

        self.recorder.stop()
        self.monitor_queue.put(None)
    
    def run(self):
        log.info("Worker thread started")

        self.procedure = self.results.procedure

        self.recorder = Recorder(self.results, self.recorder_queue)
        self.recorder.start()

        # route Procedure methods & log
        self.procedure.should_stop = self.should_stop
        self.procedure.emit = self.emit

        log.info("Worker started running an instance of %r", self.procedure.__class__.__name__)
        self.update_status(Procedure.RUNNING)
        self.emit('progress', 0)

        try:
            self.procedure.startup()
            self.procedure.evaluate_metadata()
            self.results.store_metadata()
            self.procedure.execute()
        except (KeyboardInterrupt, SystemExit):
            self.handle_abort()
        except Exception:
            self.handle_error()
        finally:
            self.shutdown()
            self.stop()

    def __repr__(self):
        return "<{}(procedure={},should_stop={})>".format(
            self.__class__.__name__,
            self.procedure.__class__.__name__,
            self.should_stop()
        )


