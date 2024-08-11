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


""" Recorder class.
    Got inspired by PyMeasure to realize the multiple threads and catch any output messages.
    
    Also this module provides a link to the `iceRadLib` module.
"""


import logging
import logging.handlers
from logging import StreamHandler, FileHandler

from .thread import StoppableThread


class QueueListener(logging.handlers.QueueListener):
    def is_alive(self):
        try:
            return self._thread.is_alive()
        except AttributeError:
            return False
        

class Monitor(QueueListener):

    def __init__(self, results, queue):
        console = StreamHandler()
        console.setFormatter(results.formatter)

        super().__init__(queue, console)
        

class Listener(StoppableThread):
    """
        Base class for Threads that need to listen for messages 
        and can be stopped by a thread-safe method call
    """

    def __init__(self, port, topic='', timeout=0.01):
        """
            Constructs the Listener object with a subscriber port
            over which to listen for messages

            :param port: TCP port to listen on
            :param topic: Topic to listen on
            :param timeout: Timeout in secons to re-check stop flag
        """
        super().__init__()

        self.port = port
        self.topic = topic
        self.context = ''
        self.timeout = timeout

    
class Recorder(QueueListener):
    """ 
        Recorder loads the initial Results for a filepath and
        appends data by listening for it over a queue. The queue
        ensures that no data is lost between the Recorder and Worker.
    """
    def __init__(self, results, queue, **kwargs):
        """ 
            Constructs a Recorder to record the Procedure data into
            the file path, by waiting for data on the subscription port
        """
        handlers = []
        for filename in results.loggings:
            fh = FileHandler(filename=filename, **kwargs)
            fh.setFormatter(results.formatter)
            fh.setLevel(logging.NOTSET)
            handlers.append(fh)
        super(Recorder, self).__init__(queue, *handlers)
    
    def stop(self):
        for handler in self.handlers:
            handler.close()
        
        super().stop()



