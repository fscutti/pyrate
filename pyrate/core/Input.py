""" Input template class. The general structure needed for an Input type object
    e.g. a Reader. Inherits from Algrithm, and adds an index _idx, an event time
    _eventTime and if the input is loaded is_loaded.

    This should be treated as an abstract class, and should be used as a
    template for the real inputs/readers
"""

from pyrate.core.Algorithm import Algorithm
import glob
import os
import sys

class Input(Algorithm):
    __slots__ = ["_eventID", "is_loaded", "_progress", "_hasEvent", "_files", "_size"]


    def _init_files(self):

        if not "files" in self.config:
            sys.exit(f"ERROR: {self.name} is trying to collect files but the path has not been specified.")

        self._files = []
        for f in self.config["files"]:

            f = os.path.expandvars(f)
            self._files += sorted(glob.glob(f))

        if not self._files:
            sys.exit(f"ERROR: in reader {self.name}, no files were found.")

        self._size = sum([os.path.getsize(f) for f in self._files])


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
