""" Class to handle the event building. Will be used like an algorithm in the 
    run flow, but has extra run determining features
"""

import sys
import importlib

from pyrate.core.Input import Input

class EventBuilder(Input):
    __slots__ = ["readers", "window"]
    
    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
        self.is_loaded = False
        self.readers = {}
        self.window = self.config["window"]
        
        # Clean out the un-used parameters
        del self.config["algorithm"]
        del self.config["window"]

        for name, conf in self.config.items():
            reader_module = "pyrate.readers." + conf["reader"]
            try:
                ReaderModule = importlib.import_module(reader_module)
                ReaderClass = ReaderModule.__getattribute__(conf["reader"])
                self.readers[name] = ReaderClass(name, conf, self.store, self.logger)
            except ImportError as err:
                sys.exit(
                    f"ERROR: {err}\n Unable to import reader '{conf['reader']}' from module '{reader_module}'\n"
                    "Check that the reader is in pyrate/readers, that the class and module have the same name, and is added the nearest __init__.py"
                )

        # Set the event builder's outputs
        variables = {}
        for reader in self.readers.values():
            for key, var in reader.output.items():
                variables[key] = var

        self.output = variables

    def initialise(self):
        """ Initialises all the inputs
        """
        if self.is_loaded == False:
            self.is_loaded = True
            self._idx = 0
            for reader in self.readers.values():
                reader.initialise()
                        
    def finalise(self):
        """ Cleans up all the inputs
        """
        if self.is_loaded == True:
            self.is_loaded = False
            for reader in self.readers.values():
                reader.finalise()

    def skip_events(self, n):
        """ Skips forward by n events
        """
        for i in range(n):
            if not self.get_event():
                break

    def get_event(self):
        """ Builds the event
            The default case is to build using Timestamp-based events
            if parallel is True in the config, will just read all events from
            all readers in order
        """
        # Parallel event building (just read everything as it comes)
        if "parallel" in self.config and self.config["parallel"] == True:
            success = False
            self._idx += 1
            for reader in self.readers.values():
                success |= reader.get_event()

            return success

        # Timestamp-based event building
        self._eventTime = 2**64 # largest possible event time (uint64)
        deltaT = self.window # How far to look forwards
        success = False
        for reader in self.readers.values():
            # Get the latest reader time stamp!
            if (readerTime := reader.timestamp) < self._eventTime:
                self._eventTime = readerTime
                success = True                

        if success == False:
            return False

        self._idx += 1
        maxTime = self._eventTime + deltaT
        
        # Search for more event data in the valid block
        success = True
        while success:
            success = False        
            for reader in self.readers.values():
                if reader.timestamp <= maxTime:
                    # Ok, we found a reader with data within the maxTime
                    
                    # Check if we need to expand the maxTime based on this
                    # reader's latest timestamp
                    if((reader.timestamp + deltaT) > maxTime):
                        maxTime = (reader.timestamp + deltaT)
                    
                    # Now get the data from the reader
                    reader.get_event()
                    success = True

        return True

# EOF