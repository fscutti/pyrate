""" Retrieves trigger timestamps for each sub-event recorded in the PSD reader, and puts on store.
    This is necessarey when, for example, triggering on one channel with the PSD reader, whilst collecting waveforms
    from another when said first channel is triggered. The PSD firmware will not shift the pulse in the second channel
    by the delay in physical signals, and it will instead appear at the same point in the waveform as the pulse in the first.
    Instead trigger timestamps for each channel (sub-event) are saved. 

    Required states:
        execute:
            output:

    No required parameters.
    
    Example config:

    CHXTimestamp:
        algorithm:
            name: ChannelTimestamps
            channel: X
        execute:
            output:

"""

from pyrate.core.Algorithm import Algorithm
import numpy as np
import sys
from pyrate.utils.enums import Pyrate


class ChannelTimestamps(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self):
        reader = self.store.get(f"INPUT:READER:name")
        channel = self.config["algorithm"]["channel"]

        # This only applies for the PSD reader, so if any other user is being used it will just return a NONE
        if reader == "ReaderCAEN1730_PSD":
            timestamps = self.store.get(f"EVENT:ch_timestamps")

            # Maybe there's a better way to do this, but at the moment this requires
            # a separate object for each channel.
            # We could maybe check the key for each dict coming in and save the output as [Ch, Timestamp], but that maybe is confusing
            if channel in timestamps.keys():
                ch_timestamp = timestamps[channel]
            else:
                self.store.put(self.name, Pyrate.NONE)
                return

        else:
            self.store.put(self.name, Pyrate.NONE)
            return
        
        self.store.put(self.name, ch_timestamp)