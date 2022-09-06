""" Class to handle the event building. Will be used like an algorithm in the 
    run flow, but has extra run determining features
"""

import sys
import importlib

from pyrate.core.Input import Input

class EventBuilder(Input):
    __slots__ = ["readers"]
    
    def __init__(self, name, base, config, store, logger):
        super().__init__(name, base, config, store, logger)
        self.is_loaded = False
        self.readers = {}
        
        for name, conf in config["input"].items():
            reader_module = "pyrate.readers." + conf["reader"]
            try:
                ReaderModule = importlib.import_module(reader_module)
                ReaderClass = ReaderModule.__getattribute__(self.reader)
                self.readers[name] = ReaderClass(name, conf, self.store, self.logger)
            except ImportError as err:
                sys.exit(
                    f"ERROR: {err}\n Unable to import reader '{conf['reader']}' from module '{reader_module}'\n"
                    "Check that the reader is in pyrate/readers, that the class and module have the same name, and is added the nearest __init__.py"
                )

        output_variables = {}
        for reader in self.readers.values():
            for key, var in reader.output:
                output_variables[key] = var

        self.output = output_variables


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

    def execute(self):
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
        self._eventTime = 2**64
        deltaT = self.config["window"] # How far to look forwards
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