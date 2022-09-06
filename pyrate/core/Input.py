""" Input template class. The general structure needed for an Input type object
    e.g. a Reader. Inherits from Algrithm, and adds an index _idx, an event time
    _eventTime and if the input is loaded is_loaded.
"""

from pyrate.core.Algorithm import Algorithm

class Input(Algorithm):
    __slots__ = ["_idx", "_eventTime", "is_loaded"]

    @property
    def idx(self):
        return self._idx

    def skip_events(self, n):
        """ Skips an event - implemented however the author wants
        """
        pass

    def get_event(self):
        """ Gets the actual event information and puts it on the store 
        """
        pass

    @property
    def timestamp(self):
        """ Returns the current event time
        """
        return self._eventTime

# EOF