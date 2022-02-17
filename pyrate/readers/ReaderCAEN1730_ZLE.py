""" Reader of binary files from CAEN1730 digitizers using the zle firmware.
This version of the reader uses memory mapping to read the file:
https://docs.python.org/3.0/library/mmap.html.

Binary data is written according to the scheme given in the ZLE manual
"""
import os
import mmap
import struct

from pyrate.core.Reader import Reader


class ReaderCAEN1730_ZLE(Reader):
    __slots__ = [
        "f",
        "_mmf",
        "_mmfSize",
        "_eventPos",
        "_readIdx",
        "_inEvt",
        "_evtTimestamp",
        "_evtWaveforms",
    ]

    def __init__(self, name, store, logger, f_name, structure):
        super().__init__(name, store, logger)
        self.f = f_name

    def load(self):
        self.is_loaded = True

        self.f = open(self.f, "rb")
        self._mmf = mmap.mmap(self.f.fileno(), length=0, access=mmap.ACCESS_READ)
        self.f.close()

        self._eventPos = []
        self._mmfSize = self._mmf.size()

    def offload(self):
        self.is_loaded = False
        self._mmf.close()

    def read(self, name):
        if self._readIdx != self._idx:
            self._read_event()
            self._readIdx = self._idx

        if name.startswith("EVENT:"):
            # Split the request
            path = self._break_path(name)

            # Get the event value
            if path["variable"] == "timestamp":
                value = self._evtTime
            elif path["variable"] == "waveform":
                value = self._get_waveform(path["ch"])

            # Add the value to the transiant store
            self.store.put(name, value, "TRAN")

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
            head1 = self._mmf.read(4)
            if head1 == bytes():
                break

            # If we read something, increment the event counter and skip to the next event
            self._n_events += 1
            head1 = int.from_bytes(head1, "little")
            eventSize = head1 & 0b00001111111111111111111111111111

            seekSize = 4 * (eventSize - 1)  # How far we need to jump
            # Make sure we're not seeking beyond the EOF
            if (self._mmf.tell() + seekSize) > self._mmfSize:
                break

            self._mmf.seek(seekSize, 1)

        self._mmf.seek(0, 0)
        self._readIdx = -1

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
        #If the channel is not in the event return an empty list
        #ToDo: Confirm this behaviour in pyrate
        if(ch not in self._inEvt.keys()):
            return [0]

        return self._currentEventWaveforms[ch]

    def _read_event(self):
        #Reset event
        self._evtTime = 2**64
        self._inEvt = {};
        self._evtWaveforms = {}

        self._mmf.seek(self._eventPos[self._idx],0)
        #Read in the event info from the header

        head1 = self._mmf.read(4)
        head1 = int.from_bytes(head1, "little")
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
        
        #Read in the waveform data
        for i in range(15):
            if channelMask & (1 << i):
                self._inEvt[i] = True
                self._evtWaveforms[i] = []
                
                #Get the baseline and record size (in words)
                sample = int.from_bytes(self._mmf.read(4),"little")

                baseLine = (sample & 0b11111111111111110000000000000000) >> 16
                recordSize = sample & 0b00000000000000001111111111111111

                # Scan through the record
                rawTrace = []
                for j in range(recordSize - 1):
                    sample = int.from_bytes(self._mmf.read(4), "little")

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

                self._evtWaveforms[i] = rawTrace


# EOF
