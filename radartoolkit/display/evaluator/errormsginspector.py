

""" Error Msg Widget for displaying.
"""

from .abstract import AbstractInspector
from ..utils.check_class import check_is_a_string
from ..config.ctis.groupcti import MainGroupCti


class ErrorMsgInspector(AbstractInspector):

    
    def __init__(self, collector, msg, parent=None):

        super(ErrorMsgInspector, self).__init__(collector, parent=parent)

        check_is_a_string(msg)
        self.msg = msg

        self._config = self._createConfig()
        self.setCurrentIndex(self.ERROR_PAGE_IDX)


    @classmethod
    def axesNames(cls):
        return tuple()


    def _createConfig(self):
        """ Creates a config tree item (CTI) hierarchy containing default children.
        """
        rootItem = MainGroupCti('message inspector')
        return rootItem


    def updateContents(self, reason=None, initiator=None):
        """ Override updateContents. Shows the error error message
        """
        self.setCurrentIndex(self.ERROR_PAGE_IDX)
        self._showError(msg=self.msg)

           





