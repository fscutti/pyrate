""" Class to handle the event building. Will be used like an algorithm in the 
    run flow, but has extra run determining features
"""

import pyrate.utils.functions as FN

from pyrate.core.Input import Input

LONG_MAX = 2**64

class EventBuilder(Input):
    __slots__ = ["readers", "window"]
    
    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
        self.is_loaded = False
        self.readers = {}
        if "parallel" not in config or ("parallel" in config and config["parallel"] != True):
            self.window = self.config["window"]
        else:
            self.window = None

        # Clean out the un-used parameters
        reader_configs = {k:v for k, v in self.config.items() 
                            if k != "algorithm" and k != "window" and k != "parallel"}

        # Load the readers
        for name, reader_config in reader_configs.items():
            ReaderClass = FN.class_factory(reader_config["reader"])
            self.readers[name] = ReaderClass(name, reader_config, self.store, self.logger)

        # Set the event builder's outputs
        variables = {}
        for reader in self.readers.values():
            for _, var in reader.output.items():
                # can't use the key because it would clash
                variables[var] = var

        self.output = variables

    def initialise(self, condition=None):
        """ Initialises all the inputs
        """
        if self.is_loaded == False:
            self.is_loaded = True
            for reader in self.readers.values():
                reader.initialise()
                        
    def finalise(self, condition=None):
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
            all readers in order. Based on MSMG
        """
        # Set internal progress checker to the max and find the lowest
        current_progress = 1

        # ----------------------------------------------------------
        # Parallel event building (just read everything as it comes)
        if "parallel" in self.config and self.config["parallel"] == True:
            success = False
            self._eventTime = 0
            for reader in self.readers.values():
                success |= reader.get_event()

                # Check the progress
                if reader.progress < current_progress:
                    current_progress = reader.progress
            
            # Update the EventBuilder's progress
            self._progress = current_progress

            return success

        # ------------------------------
        # Timestamp-based event building
        self._eventTime = LONG_MAX # largest possible event time (uint64)
        deltaT = self.window # How far to look forwards
        success = False
        for reader in self.readers.values():
            # Get the latest reader time stamp!
            if reader.hasEvent and (readerTime := reader.timestamp) < self._eventTime:
                self._eventTime = readerTime
                success = True                

        if success == False:
            # No more events!
            return False

        maxTime = self._eventTime + deltaT
        
        # Search for more event data in the valid block
        success = True
        while success:
            success = False
            for reader in self.readers.values():
                if reader.hasEvent and reader.timestamp <= maxTime:
                    # Ok, we found a reader with data within the maxTime

                    if reader.timestamp < (self._eventTime - deltaT):
                        # Uh oh, looks like we've gone back in time
                        print(f"WARNING: The timestamp of reader {reader.name} ({reader.timestamp}) is more than {deltaT} before the event time {self._eventTime}.")

                    # Check if we need to expand the maxTime based on this
                    # reader's latest timestamp
                    if((reader.timestamp + deltaT) > maxTime):
                        maxTime = (reader.timestamp + deltaT)
                    
                    # Now get the data from the reader
                    reader.get_event()
                    success = True

                # Check the progress
                if reader.progress < current_progress:
                    current_progress = reader.progress
            
            # Update the EventBuilder's progress
            self._progress = current_progress

        return True

# EOF