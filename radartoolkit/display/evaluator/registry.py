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


""" Selections of Data Evaluators.
"""

from ..reg.basereg import BaseRegItem, BaseRegistry, RegType


DEFAULT_EVALUATOR= "Image Plot"


class EvaluatorRegItem(BaseRegItem):
    """ 
    Fields: ['name', 'absClassName', 'shortCut', 'pythonPath']
    """

    FIELDS = BaseRegItem.FIELDS[:1] + ['shortCut'] + BaseRegItem.FIELDS[1:]
    TYPES = BaseRegItem.TYPES[:1] + [RegType.ShortCut] + BaseRegItem.TYPES[1:]
    LABELS = BaseRegItem.LABELS[:1] + ['ShortCut'] + BaseRegItem.LABELS[1:]
    STRETCH = BaseRegItem.STRETCH[:1] + [False] + BaseRegItem.STRETCH[1:]

    def __init__(self, name='', absClassName='', pythonPath='', shortCut='', info=''):
        
        super(EvaluatorRegItem, self).__init__(name=name, 
                                               absClassName=absClassName, 
                                               pythonPath=pythonPath)
        self._data['shortCut'] = shortCut
        self._info = info
        

    @property
    def shortCut(self):
        """ Keyboard short cut """
        return self._data['shortCut']
    

    @property
    def info(self):
        return self._info


    @property
    def axesNames(self):
        """ 
        The axes names of the inspector.
        """
        return [] if self.cls is None else self.cls.axesNames()
    

    @property
    def nDims(self):
        """ 
        The number of axes of this inspector.
        """
        return len(self.axesNames)
    

    def create(self, collector, tryImport=True):
        """ 
        Creates an inspector of the registered and passes the collector to the constructor.
        Tries to import the class if tryImport is True.
        Raises ImportError if the class could not be imported.
        ====>
        cls(collector) creats an instance, e.g: PgImagePlot2d
        """
        cls = self.getClass(tryImport=tryImport)
        if not self.successfullyImported:
            raise ImportError("Class not successfully imported: {}".format(self.exception))
        return cls(collector)



class EvaluatorRegistry(BaseRegistry):
    """ 
    Class that maintains the collection of registered inspector classes.
    See the base class documentation for more info.
    """

    ITEM_CLASS = EvaluatorRegItem

    def __init__(self):
        super(EvaluatorRegistry, self).__init__()


    @property
    def registryName(self):
        return "evaluator"


    def getDefaultItems(self):
        """ 
        Returns a list with the default plugins in the inspector registry.
        """
        plugins =   [
            EvaluatorRegItem('Table', 
                             'display.evaluator.pgs.table.TableInspector',
                             shortCut="Ctrl+1",
                             info="Table"),

            EvaluatorRegItem('Image Plot', 
                             'display.evaluator.pgs.pgplot2d.PgPlots2DCanvas',
                             shortCut="Ctrl+2",
                             info="2D Image Plot")
                    ]
        
        return plugins
