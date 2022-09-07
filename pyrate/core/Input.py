""" Input template class. The general structure needed for an Input type object
    e.g. a Reader. Inherits from Algrithm, and adds an index _idx, an event time
    _eventTime and if the input is loaded is_loaded.
"""

from pyrate.core.Algorithm import Algorithm

class Input(Algorithm):
    __slots__ = ["_idx", "_eventTime", "is_loaded", "_progress"]

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
    
    @Algorithm.output.setter
    def output(self, outputs):
        """ Re-usable setter for inputs
        """
        self._output = outputs

    @property
    def progress(self):
        """ Get an esimate of the progress as a value between 0 and 1
            where 0 is starting and 1 is complete
        """
        return self._progress

# EOF