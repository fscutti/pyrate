""" Retrieves trigger timestamps for each event from various readers in pyrate, and puts on store.
    NB: WaveDump timestamps will have overflow, and will need a correction based on th number of clock overflows present.
    This may require another algorithm.

    Required states:
        execute:
            output:

    No required parameters.
    
    Example config:

    Timestamp:
    algorithm:
      name: GetTimestamp
    execute:
      output:

    Todo: Include a clock overflow correction for wavedump/any other reader that needs it.

"""

from pyrate.core.Algorithm import Algorithm
import numpy as np
import sys


class GetTimestamp(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self):
        # Gets reader and checks it against readers in pyrate, gets timestamp based on reader syntax and puts on store.
        reader = self.store.get(f"INPUT:READER:name")
        if reader == "ReaderBlueTongueMMAP":
            timestamp = self.store.get(f"EVENT:timestamp")

        elif reader == "ReaderWaveDumpMMAP":
            timestamp = self.store.get(f"INPUT:Trigger Time Stamp")

        elif reader == "ReaderCAEN1730_RAW" or reader == "ReaderCAEN1730_ZLE" or reader == "ReaderCAEN1730_PSD":
            timestamp = self.store.get(f"EVENT:timestamp")
        
        self.store.put(self.name, timestamp)