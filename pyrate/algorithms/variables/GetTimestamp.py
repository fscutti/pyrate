from pyrate.core.Algorithm import Algorithm
import numpy as np
import sys


class GetTimestamp(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self):
        reader = self.store.get(f"INPUT:READER:name")
        if reader == "ReaderBlueTongueMMAP":
            timestamp = self.store.get(f"EVENT:timestamp")

        elif reader == "ReaderWaveDumpMMAP":
            timestamp = self.store.get(f"INPUT:Trigger Time Stamp")

        elif reader == "ReaderCAEN1730_RAW" or reader == "ReaderCAEN1730_ZLE" or reader == "ReaderCAEN1730_PSD":
            timestamp = self.store.get(f"EVENT:timestamp")
        
        self.store.put(self.name, timestamp)