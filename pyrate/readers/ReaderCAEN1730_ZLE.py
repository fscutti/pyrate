""" Reader of binary files from CAEN1730 digitizers using the ZLE firmware.

Binary data is written according to the scheme given in the ZLE manual
"""

import os
import mmap
import numpy as np

from pyrate.core.Input import Input
import pyrate.utils.functions as FN


class ReaderCAEN1730_ZLE(Input):
    __slots__ = ["_files", "_f", "_sizes", "size", "_bytes_read", "_mmf", "_inEvent", 
                 "_eventChTimes", "_eventWaveforms", "channels"]

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

        self.channels = 8
        # Set the outputs manually
        outputs = {}
        for i in range(self.channels):
            outputs.update({f"ch_{i}_timestamp": f"{self.name}_ch_{i}_timestamp",
                            f"ch_{i}_waveform": f"{self.name}_ch_{i}_waveform"})

        self.output = outputs

        # Load the first file
        self.load()

    def load(self):
        self.is_loaded = True
        self._files = [FN.find_env(f) for f in self.config["files"]]
        self._f = open(self._files[0], "rb")
        self._sizes = [os.path.getsize(f) for f in self._files]
        self.size = sum(self._sizes)
        self._bytes_read = 0

        # Pull in the first event information, ready to go
        self.read_next_event()
        # self._mmf = mmap.mmap(self._f.fileno(), length=0, access=mmap.ACCESS_READ)
        # self._f.close()

        # self._eventPos = []
        # self._mmfSize = self._mmf.size()

    def offload(self):
        self.is_loaded = False
        self._f.close()
    
    def finalise(self, condition=None):
        self.offload()

    def get_event(self, skip=False):
        if self._eventTime == 2**64:
            return False
        
        #Put the event on the store
        if not skip:
            for ch in range(self.channels):
                if ch in self._inEvent:
                    self.store.put(f"{self.output[f'ch_{ch}_timestamp']}", self._eventTime)
                    self.store.put(f"{self.output[f'ch_{ch}_waveform']}", np.array(self._eventWaveforms[ch], dtype="int32"))

        # Get the next event
        self.read_next_event()
        return True
    
    def skip_events(self, n):
        """ Skips over n events
        """
        for i in range(n):
            if not self.get_event():
                break

    def read_next_event(self):
        # Reset event
        self._eventTime = 2**64
        self._inEvent = {}
        self._eventChTimes = {}
        self._eventWaveforms = {}

        # Read in the event information
        # Need to keep reading till we get head1
        while head1 := self._f.read(4):
            head1 = int.from_bytes(head1, "little")
            if (head1 & 0xFFFF0000) == 0xa0000000:
                break
        else:
            self._f.seek(0)
            return

        head2 = self._f.read(4)
        if(head2 == bytes()):
            return False
        head2 = int.from_bytes(head2,"little")

        head3 = self._f.read(4)
        if(head3 == bytes()):
            return False
        head3 = int.from_bytes(head3,"little")

        head4 = self._f.read(4)
        if(head4 == bytes()):
            return False
        head4 = int.from_bytes(head4,"little")

        # ZLE things
        # The event size as a longword, x4 for in bytes
        eventSize = head1 & 0b00001111111111111111111111111111
        boardID = head2 & 0b11111000000000000000000000000000
        pattern = head2 & 0b00000000111111111111111100000000
        channelMaskLo = head2 & 0b11111111
        channelMaskHi = head3 & 0b11111111000000000000000000000000
        eventCount = head3 & 0b00000000111111111111111111111111
        channelMask = (channelMaskHi << 8) + (channelMaskLo)
        TTT = head4

        # Scan through the channel headers
        for i in range(self.channels):
            if channelMask & (1 << i):
                self._inEvent[i] = True
                self._eventWaveforms[i] = []
                
                #Get the baseline and record size (in words)
                sample = int.from_bytes(self._f.read(4),"little")

                baseLine = (sample & 0b11111111111111110000000000000000) >> 16
                recordSize = sample & 0b00000000000000001111111111111111

                # Scan through the record
                rawTrace = []
                for j in range(recordSize - 1):
                    sample = self._f.read(4)
                    if (sample == bytes()):
                        return False
                    sample = int.from_bytes(sample,"little")
                    
                    # If the samples being skipped
                    if (sample & 0b11110000000000000000000000000000) >> 28 == (0b1000):
                        # Add the approparite number of skipped samples to the trace
                        numSkipped = sample & 0b00001111111111111111111111111111
                        for k in range(2 * numSkipped):
                            rawTrace.append(baseLine)
                    else:
                        # Otherwise append the two samples
                        rawTrace.append(sample & 0b00000000000000000011111111111111)
                        rawTrace.append(
                            (sample & 0b00111111111111110000000000000000) >> 16
                        )

                self._eventWaveforms[i] = rawTrace

        self._eventTime = 8*((pattern << 24) + TTT)
        # Update the number of bytes read by the eventSize
        self._bytes_read += 4*eventSize
        # Update the progress
        self._progress = self._bytes_read / self.size

        return True

# EOF