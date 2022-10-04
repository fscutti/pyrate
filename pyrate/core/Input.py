""" Input template class. The general structure needed for an Input type object
    e.g. a Reader. Inherits from Algrithm, and adds an index _idx, an event time
    _eventTime and if the input is loaded is_loaded.

    This should be treated as an abstract class, and should be used as a
    template for the real inputs/readers
"""

from pyrate.core.Algorithm import Algorithm

class Input(Algorithm):
    __slots__ = ["_eventID", "is_loaded", "_progress", "_hasEvent"]

    def skip_events(self, n):
        """ Skips an event - implemented however the author wants
        """
        pass

    def get_event(self):
        """ Gets the actual event information and puts it on the store 
        """
        pass

    @property
    def eventID(self):
        """ Returns the current event time
        """
        return self._eventID
    
    @property
    def hasEvent(self):
        """ Returns whether the input current has an event
        """
        return self._hasEvent

    @property
    def progress(self):
        """ Get an esimate of the progress as a value between 0 and 1
            where 0 is starting and 1 is complete
        """
        return self._progress

# EOF