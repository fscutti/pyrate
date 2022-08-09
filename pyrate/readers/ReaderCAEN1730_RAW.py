""" Reader of binary files from CAEN1730 digitizers using the raw firmware.
This version of the reader uses memory mapping to read the file:
https://docs.python.org/3.0/library/mmap.html.

Binary data is written according to the scheme given in the CAEN1730 manual
"""
import os
import mmap
import struct
from pyrate.utils.enums import Pyrate
import numpy as np

from pyrate.core.Reader import Reader


class ReaderCAEN1730_RAW(Reader):
    __slots__ = [
        "f",
        "_mmf",
        "_mmfSize",
        "_eventPos",
        "_readIdx",
        "_inEvt",
        "_evtTime",
        "_evtWaveforms",
    ]

    def __init__(self, name, config, store, logger, f_name, structure):
        super().__init__(name, config, store, logger)
        self.f = f_name

    def load(self):
        self.is_loaded = True

        self.f = open(self.f, "rb")
        self._mmf = mmap.mmap(self.f.fileno(), length=0, access=mmap.ACCESS_READ)
        self.f.close()

        self._eventPos = []
        self._mmfSize = self._mmf.size()
        self._readIdx = -1

    def offload(self):
        self.is_loaded = False
        self._mmf.close()

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
        self._mmf.seek(0, 0)
        self._n_events = 0

        # Scan through the entire file
        while True:
            # Read in the event info from the header
            self._eventPos.append(self._mmf.tell())
            while head1 := self._mmf.read(4):
                head1 = int.from_bytes(head1, "little")
                if (head1 & 0xFFFF0000) == 0xa0000000:
                    break
            else:
                self._mmf.seek(0, 0)
                return
            # If we read something, increment the event counter and skip to the next event
            self._n_events += 1
            eventSize = head1 & 0b00001111111111111111111111111111

            seekSize = 4 * (eventSize - 1)  # How far we need to jump
            # Make sure we're not seeking beyond the EOF
            if (self._mmf.tell() + seekSize) > self._mmfSize:
                break

            self._mmf.seek(seekSize, 1)

        self._mmf.seek(0, 0)

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
        if ch not in self._inEvt.keys():
            return Pyrate.NONE

        # Return the waveform and mark that this channel has been read
        return self._evtTime

    def _read_event(self):
        # Reset event
        self._evtTime = 2 ** 64
        self._inEvt = {}
        self._evtWaveforms = {}

        self._mmf.seek(self._eventPos[self._idx], 0)
        # Read in the event info from the header

        while head1 := self._mmf.read(4):
            head1 = int.from_bytes(head1, "little")
            if (head1 & 0xFFFF0000) == 0xa0000000:
                break
        else:
            self._mmf.seek(0, 0)
            return
        eventSize = head1 & 0b00001111111111111111111111111111

        head2 = self._mmf.read(4)
        head2 = int.from_bytes(head2, "little")
        boardID = head2 & 0b11111000000000000000000000000000
        pattern = head2 & 0b00000000111111111111111100000000
        channelMaskLo = head2 & 0b11111111

        head3 = self._mmf.read(4)
        head3 = int.from_bytes(head3, "little")
        channelMaskHi = head3 & 0b11111111000000000000000000000000
        evtCount = head3 & 0b00000000111111111111111111111111

        head4 = self._mmf.read(4)
        head4 = int.from_bytes(head4, "little")
        TTT = head4

        self._evtTime = (pattern << 24) + TTT
        channelMask = (channelMaskHi << 8) + (channelMaskLo)

        # Figure out what channels are in the event
        numCh = 0

        for i in range(15):
            if channelMask & (1 << i):
                numCh += 1
                self._inEvt[i] = True
                self._evtWaveforms[i] = []

        recordSize = int(2 * (eventSize - 4) / numCh)
        # Read in the waveform data

        for i in range(15):
            if channelMask & (1 << i):
                for j in range(recordSize):
                    sample = self._mmf.read(2)
                    self._evtWaveforms[i].append(int.from_bytes(sample, "little"))


# EOF
