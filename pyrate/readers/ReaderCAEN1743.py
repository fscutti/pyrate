""" Reader of binary files from CAEN1743 digitizers

Binary data is written according to the scheme given in the CAEN1743 manual
Note: This manual is slightly incorrect, there are some additional words in the data structure that currently being skipper
"""
import os
import mmap
import struct
from pyrate.utils.enums import Pyrate
import numpy as np

from pyrate.core.Reader import Reader


class ReaderCAEN1743(Reader):
    __slots__ = [
        "_fName",
        "_f",
        "_fSize",
        "_readIdx",
        "_inEvt",
        "_evtTime",
        "_lastTime",
        "_overflowCount",
        "_evtWaveforms",
        "_evtChTimes"
    ]

    def __init__(self, name, config, store, logger, f_name, structure):
        super().__init__(name, config, store, logger)
        self._fName = f_name

    def load(self):
        self.is_loaded = True
        self._f = open(self._fName, "rb")
        self._fSize = os.path.getsize(self._fName);
        self._readIdx = -1
        self._lastTime = 0;
        self._overflowCount = 0;

    def offload(self):
        self.is_loaded = False
        self._f.close()

    def read(self, name):
        if name.startswith("EVENT:"):
            if self._readIdx != self._idx:
                self._read_event()
            self._readIdx = self._idx
            # Split the request
            path = self._break_path(name)

            # Get the event value
            if path["variable"] == "timestamp":
                value = self._evtTime
            elif path["variable"] == "waveform":
                value = self._get_waveform(path["ch"])
            elif path["variable"] == "ch_timestamp":
                value = self._get_timestamps(path["ch"])

            # Add the value to the transient store
            self.store.put(name, value)

        elif name.startswith("INPUT:"):
            pass

    def set_n_events(self):
        """Reads number of events using the last event header."""
        # Seek to the start of the file
        self._f.seek(0, 0)
        self._n_events = 0
        # Scan through the entire file
        while True:
            # Read in the event info from the header
            while head1 := self._f.read(4):
                head1 = int.from_bytes(head1, "little")
                if (head1 & 0xFFFF0000) == 0xa0000000:
                    break
            else:
                self._f.seek(0, 0)
                return
            
            # If we read something, increment the event counter and skip to the next event
            self._n_events += 1
            eventSize = head1 & 0b00001111111111111111111111111111
            seekSize = 4 * (eventSize - 1)  # How far we need to jump
            # Make sure we're not seeking beyond the EOF
            if (self._f.tell() + seekSize) > self._fSize:
                break

            self._f.seek(seekSize, 1)
            
        self._f.seek(0, 0)

    def _break_path(self, path):
        """Takes a path request from pyrate and splits it into a dictionary"""
        splitPath = path.split(":")

        ret = {}
        ret["variable"] = splitPath[-1]
        if len(splitPath) > 2:
            ret["board"] = int(splitPath[1].split("_")[-1])
            if len(splitPath) > 3:
                ret["ch"] = int(splitPath[2].split("_")[-1])

        return ret

    def _get_waveform(self, ch):
        """Reads variable from the event and puts it in the transient store."""
        # If the channel is not in the event return an empty list
        # ToDo: Confirm this behaviour in pyrate
        if ch not in self._inEvt.keys():
            return Pyrate.NONE

        return np.array(self._evtWaveforms[ch], dtype="int32")

    def _get_timestamps(self, ch):
        # If the channel is not in the event return an empty list
        # ToDo: Confirm this behaviour in pyrate
        if ch not in self._evtChTimes.keys():
            return Pyrate.NONE

        # Return the waveform and mark that this channel has been read
        return self._evtChTimes[ch]

    def _read_event(self):
        # Reset event
        self._evtTime = 2 ** 64
        self._inEvt = {}
        self._evtWaveforms = {}
        self._evtChTimes = {}
        
        # Check for a valid event start and read the header
        while head1 := self._f.read(4):
            head1 = int.from_bytes(head1, "little")
            if (head1 & 0xFFFF0000) == 0xa0000000:
                break
        else:
            self._f.seek(0, 0)
            return

        head2 = self._f.read(4)
        head2 = int.from_bytes(head2, "little")
        head3 = self._f.read(4)
        head3 = int.from_bytes(head3, "little")
        head4 = self._f.read(4)
        head4 = int.from_bytes(head4, "little")
        
        # Read in the event info from the header words
        eventSize = head1 & 0b00001111111111111111111111111111
        boardID = head2 & 0b11111000000000000000000000000000
        groupMask = head2 & 0b11111111        
        evtCount = head3 & 0b00000000111111111111111111111111        
        #TTT = head4
        #self._evtTime = (pattern << 24) + TTT
        
        # Figure out what channels are in the event
        numGroups = 0
        for i in range(8):
            if groupMask & (1 << i):
                numGroups += 1
                self._inEvt[2*i] = True
                self._evtWaveforms[2*i] = []
                self._evtChTimes[2*i] =  2 ** 64
                self._inEvt[2*i + 1] = True
                self._evtWaveforms[2*i + 1] = []
                self._evtChTimes[2*i+1] =  2 ** 64

        recordSize = int((eventSize - 4) / numGroups)
        # Read in the waveform data
        for i in range(8):
            if groupMask & (1 << i):
                for j in range(recordSize):
                    sample = self._f.read(4)
                    sample = int.from_bytes(sample, "little")
                    sample0 = (sample & 0b00000000000000000000111111111111)
                    sample1 = (sample & 0b00000000111111111111000000000000) >> 12
                    other   = (sample & 0b11111111000000000000000000000000) >> 24
                    # Note: Every 17th word is not a waveform sample
                    if(j % 17 != 0):                    
                        self._evtWaveforms[2*i + 0].append(sample0 + 2048);
                        self._evtWaveforms[2*i + 1].append(sample1 + 2048);
                    elif (j >= 14 and j <= 18):
                        self._evtChTimes[2*i + 0] = (other << 8*(j-14));
                        self._evtChTimes[2*i + 1] = (other << 8*(j-14));
        
        for i in range(15):
            if(i in self._evtChTimes):
                #Handle overflows
                self._evtChTimes[i] = self._evtChTimes[i] + self._overflowCount*0b10000000000000000000000000000000000000000;
                self._evtChTimes[i] = 5* self._evtChTimes[i];
                if(self._evtChTimes[i] < self._evtTime):
                    self._evtTime = self._evtChTimes[i]
        if(self._evtTime < self._lastTime):
            self._overflowCount += 1

        self._lastTime = self._evtTime
# EOF
