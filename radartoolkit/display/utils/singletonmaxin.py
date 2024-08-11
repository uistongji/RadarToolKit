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


import logging
logger = logging.getLogger(__name__)


class SingletonMixin(object):
    """ Mixin to ensure the class is a singleton.

        The instance method is thread-safe but the returned object not! You still have to implement
        your own locking for that.
    """
    __singletons = {}

    def __init__(self, **kwargs):
        super(SingletonMixin, self).__init__(**kwargs)

        cls = type(self)
        logger.debug("Creating singleton: {} (awaiting lock)".format(cls))
        cls._checkNotYetPresent()
        SingletonMixin.__singletons[cls] = self



    @classmethod
    def instance(cls, **kwargs):
        """ Returns the singleton's instance.
        """
        if cls in SingletonMixin.__singletons:
            return SingletonMixin.__singletons[cls]
        else:
            return cls(**kwargs)


    @classmethod
    def _checkNotYetPresent(cls):
        """ Checks that the newClass is not yet present in the singleton

            Also check that no descendants are present. This is typically due to bugs.
        """
        assert cls not in SingletonMixin.__singletons, "Constructor called twice: {}".format(cls)

        for existingClass in SingletonMixin.__singletons.keys():
            assert not issubclass(cls, existingClass), \
                "Sub type of {} already present: {}".format(cls, existingClass)

            assert not issubclass(existingClass, cls), \
                "Ancestor of {} already present: {}".format(cls, existingClass)