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


""" Thread class.
    Got inspired by PyMeasure to realize the multiple threads and catch any output messages.
    
    Also this module provides a link to the `iceRadLib` module.
"""


import logging

from threading import Thread, Event
from time import time


log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())



class InterruptableEvent(Event):
    """
        This subclass solves the problem indicated in bug
        https://bugs.python.org/issue35935 that prevents the
        wait of an Event to be interrupted by a KeyboardInterrupt.
    """
    def wait(self, timeout=None):
        if timeout is None:
            while not super().wait(0.1):
                pass
        else:
            timeout_start = time()
            while not super().wait(0.1) and time() <= timeout_start + timeout:
                pass
    

class StoppableThread(Thread):
    """
        Base class for Threads which requires the ability to be stopped
        by a thread-safe method call
    """
    def __init__(self):
        super().__init__()
        self._should_stop = InterruptableEvent()
        self._should_stop.clear()

    def join(self, timeout=0):
        """
            Joins the current thread and forces it to stop
            after the timeout if necessary

            :param timeout: Timeout duration in seconds
        """
        self._should_stop.wait(timeout)
        if not self.should_stop():
            self.stop()
        return super().join(0)
    
    def stop(self):
        self._should_stop.set()

    def should_stop(self):
        return self._should_stop.is_set()
    
    def __repr__(self):
        return "<{}(should stop={})>".format(
            self.__class__.__name__, self.should_stop())

    
