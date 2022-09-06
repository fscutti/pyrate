""" Reader of binary files from CAEN1730 digitizers using the PSD firmware.
This version of the reader uses memory mapping to read the file:
https://docs.python.org/3.0/library/mmap.html.

Binary data is written according to the scheme given in the PSD manual
"""

import mmap
import numpy as np

from pyrate.core.Input import Input
import pyrate.utils.functions as FN


class ReaderCAEN1730_PSD(Input):
    __slots__ = ["_files", "_f", "_mmf", "_inEvent", "_eventChTimes", "_eventWaveforms",
                 "channels"]

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

        # Load the first file
        self.load()

        self.channels = 8
        # Set the outputs manually
        self._output = {}
        for i in range(self.channels):
            self._output.update({f"ch_{i}:Timestamp": f"EVENT:board_0:ch_{i}:Timestamp", f"ch_{i}:waveform": f"EVENT:board_0:ch_{i}:waveform"})

    def load(self):
        self.is_loaded = True
        self._files = [FN.find_env(f) for f in self.config["files"]]
        self._f = open(self._files[0], "rb")
        self._mmf = mmap.mmap(self._f.fileno(), length=0, access=mmap.ACCESS_READ)
        self._f.close()

        # self._eventPos = []
        # self._mmfSize = self._mmf.size()

    def offload(self):
        self.is_loaded = False
        self._mmf.close()

    def initialise(self, condition=None):
        self.read_next_event()
    
    def finalise(self, condition=None):
        self.offload()

    def get_event(self, skip=False):
        if(self._eventTime == 2**64):
            return False
        
        #Put the event on the store
        if not skip:
            for ch in range(self.channels):
                if ch in self._inEvent:
                    self.store.put(f"{self.output[f'ch_{ch}:Timestamp']}", self._eventChTimes[ch])
                    self.store.put(f"{self.output[f'ch_{ch}:waveform']}", np.array(self._eventWaveforms[ch], dtype="int32"))

        # Get the next event
        self.read_next_event()
        return True
    
    def read_next_event(self):
        #Reset event
        self._eventTime = 2**64
        self._inEvent = {}
        self._eventChTimes = {}
        self._eventWaveforms = {}

        # Read in the event information
        # Need to keep reading till we get head1
        while head1 := self._mmf.read(4):
            head1 = int.from_bytes(head1, "little")
            if (head1 & 0xFFFF0000) == 0xa0000000:
                break
        else:
            self._mmf.seek(0, 0)
            return

        head2 = self._mmf.read(4)
        if(head2 == bytes()):
            return False
        head2 = int.from_bytes(head2,"little")

        head3 = self._mmf.read(4)
        if(head3 == bytes()):
            return False
        head3 = int.from_bytes(head3,"little")

        head4 = self._mmf.read(4)
        if(head4 == bytes()):
            return False
        head4 = int.from_bytes(head4,"little")        

        eventSize = head1 & 0b00001111111111111111111111111111
        dualChannelMask =  (head2 & 0b11111111)
        evtCount = head3 & 0b00000000111111111111111111111111

        #Scan through the channel headers
        for i in range(self.channels):
            if dualChannelMask & (1 << i):
                chHead1 = self._mmf.read(4)
                if (chHead1 == bytes()):
                    return False
                chHead1 = int.from_bytes(chHead1, "little")

                chHead2 = self._mmf.read(4)
                if (chHead2 == bytes()):
                    return False              
                chHead2 = int.from_bytes(chHead2, "little")

                aggregateSize = chHead1 & 0b00000000001111111111111111111111
                recordSize = chHead2 & 0b00000000000000001111111111111111

                chTime = self._mmf.read(4)
                if (chTime == bytes()):
                    return False
                chTime = int.from_bytes(chTime, "little")
                ch = 2 * i + ((chTime & 0b10000000000000000000000000000000) >> 31)

                self._eventWaveforms[ch] = []
                self._inEvent[ch] = True
                recordSize = int(recordSize *8/2)
                for j in range(recordSize):
                    sample = self._mmf.read(4)
                    sample = int.from_bytes(sample,"little")
                    self._eventWaveforms[ch].append((sample & 0b00000000000000000011111111111111))
                    self._eventWaveforms[ch].append((sample & 0b00111111111111110000000000000000) >> 16)

                extras = self._mmf.read(4)
                if(extras == bytes()):
                    return False
                extras = int.from_bytes(extras, "little")

                charge = self._mmf.read(4)
                if(charge == bytes()):
                    return False
                charge = int.from_bytes(charge, "little")

                qLong = (charge & 0b11111111111111110000000000000000) >> 16
                qShrt = charge & 0b00000000000000000111111111111111
                timeHi = (extras & 0b11111111111111110000000000000000) << 15
                timeLo = chTime & 0b01111111111111111111111111111111
                self._eventChTimes[ch] = timeHi + timeLo

                if self._eventChTimes[ch] < self._eventTime:
                    # Is this necessary???
                    self._eventChTimes[ch] = 2*self._eventChTimes[ch]
                    self._eventTime = self._eventChTimes[ch]
        
        return True

# EOF
