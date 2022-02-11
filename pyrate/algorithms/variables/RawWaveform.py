""" Gets raw waveform. Pretty simple.
    Gets the raw trace from the appropriate reader, and puts it on the transient
    store as a numpy array. The input is a string is passed to and interpreted 
    by the reader.

    Required states:
        initialise:
            output:
        execute:
            input: <Waveform string>
    
    Example config:
    
    RawWaveform_CHX:
        algorithm: 
            name: RawWaveform
        initialise:
            output:
        execute:
            input: EVENT:board_0:ch_x:waveform, 
                    EVENT:board_0:raw_waveform_ch_x, EVENT:RawWaveform
        waveform_bt: EVENT:board_0:raw_waveform_ch_x
        waveform_md: EVENT:board_0:ch_x:waveform
        waveform_wd: EVENT:RawWaveform

    Todo: Standardise the way the readers interpret the string. This will 
            remove the need to check for the reader, and the need for mulitple
            inputs strings.
"""

import sys
import numpy as np
from pyrate.core.Algorithm import Algorithm

class RawWaveform(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
    
    def initialise(self):
        """ Prepares the reader type to get the right waveform depending on the 
            input
        """
        # First we find out what kind of grouping is being used
        groups = ['0']

        # Temporary, needs fixing, not generalised for all possible group structures
        if groups[0] == '0':
            # Default, no group specified
            reader = self.store.get("INPUT:READER:name")
        else:
            reader = self.store.get(f"INPUT:READER:GROUP:name")
        
        # Store the reader in a unique way to be used later (PERM store)
        self.store.put(f"{self.name}:reader", reader)
    
    def execute(self):
        """ Gets the raw trace from the reader and puts it on the store
        """
        # First find out what reader we're using
        reader = self.store.get(f"{self.name}:reader")

        if reader == "ReaderWaveDumpMMAP":
            RawWaveform = self.store.get(self.config["waveform_wd"])
        elif reader == "ReaderCAEN1730_ZLE" or reader == "ReaderCAEN1730_RAW":
            RawWaveform = self.store.get(self.config["waveform_md"])
        elif reader == "ReaderBlueTongueMMAP":
            RawWaveform = self.store.get(self.config["waveform_bt"])
        elif reader == "ReaderWaveCatcherMMAP":
            sys.exit("Uh oh, WaveCatcher doesn't have a RawWaveform...")

        # convert to numpy array
        RawWaveform = np.array(RawWaveform)
        self.store.put(self.name, RawWaveform)

# EOF
