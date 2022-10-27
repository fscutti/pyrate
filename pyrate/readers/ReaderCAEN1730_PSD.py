""" Reader of binary files from CAEN1730 digitizers using the PSD firmware.
This version of the reader uses memory mapping to read the file:
https://docs.python.org/3.0/library/mmap.html.

Binary data is written according to the scheme given in the PSD manual
"""

import os
import sys
import glob
import numpy as np

from pyrate.core.Input import Input
from pyrate.utils.enums import Pyrate

from pyrate.utils import functions as FN

# Maximum length of the trace without a warning
MAX_TRACE_LENGTH = 50000
LONG_MAX = 2**64


class ReaderCAEN1730_PSD(Input):
    __slots__ = [
        "_f",
        "_files",
        "_size",
        "_files_index",
        "_bytes_read",
        "_inEvent",
        "_variables",
        "_eventChTimes",
        "_eventWaveforms",
        "_baseline",
        "_qLong",
        "_qShort",
        "channels",
        "timeshift",
        "_large_waveform_warning",
    ]

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

        self.channels = 8
        self.timeshift = 0 if "timeshift" not in config else config["timeshift"]
        # Set the outputs manually
        self._variables = {}
        for ch in range(self.channels):
            output_format = "{name}_ch{ch}_{variable}"  # Default formatting
            if "output" in config:
                # The user has provided a custom output formatting
                output_format = config["output"]
            self._variables.update(
                {
                    f"{ch}_timestamp": output_format.format(
                        name=self.name, ch=ch, variable="timestamp"
                    ),
                    f"{ch}_waveform": output_format.format(
                        name=self.name, ch=ch, variable="waveform"
                    ),
                    f"{ch}_baseline": output_format.format(
                        name=self.name, ch=ch, variable="baseline"
                    ),
                    f"{ch}_qLong": output_format.format(
                        name=self.name, ch=ch, variable="qLong"
                    ),
                    f"{ch}_qShort": output_format.format(
                        name=self.name, ch=ch, variable="qShort"
                    ),
                }
            )

        self.output = self._variables.values()

        # Prepare all the files

        self.is_loaded = False

        self._files = FN.collect_files(config["files"])
        if not self._files:
            sys.exit(f"ERROR: in reader {self.name}, no files were found.")

        self._size = sum([os.path.getsize(f) for f in self._files])

        self._files_index = 0
        self._bytes_read = 0

        # Set the progress to 0, unless the files are empty
        self._progress = 0 if self._size != 0 else 1

        # Set the large waveform warning flag to false
        self._large_waveform_warning = False

        # Load the first file
        self._load_next_file()

    def _load_next_file(self):
        if self.is_loaded:
            self.offload()

        # Check if there are more files
        if self._files_index >= len(self._files):
            return

        # Load the next file
        self._f = open(self._files[self._files_index], "rb")

        if not self._f:
            return
        self.is_loaded = True
        self._files_index += 1

        # Pull in the first event information, ready to go
        self.read_next_event()

    def offload(self):
        self.is_loaded = False
        self._f.close()

    def finalise(self, condition=None):
        self.offload()

    def get_event(self, skip=False):
        if not self._hasEvent:
            return False

        # Put the event on the store
        if not skip:
            for ch in range(self.channels):
                if ch in self._inEvent:
                    self.store.put(
                        f"{self._variables[f'{ch}_timestamp']}", self._eventChTimes[ch]
                    )
                    self.store.put(
                        f"{self._variables[f'{ch}_waveform']}",
                        np.array(self._eventWaveforms[ch], dtype="int32"),
                    )
                    self.store.put(
                        f"{self._variables[f'{ch}_baseline']}", self._baseline[ch]
                    )
                    self.store.put(f"{self._variables[f'{ch}_qLong']}", self._qLong[ch])
                    self.store.put(
                        f"{self._variables[f'{ch}_qShort']}", self._qShort[ch]
                    )

        # Get the next event
        if not self.read_next_event():
            self._load_next_file()

        return True

    def skip_events(self, n):
        """Skips over n events"""
        for i in range(n):
            if not self.get_event(skip=True):
                break

    def read_next_event(self):
        # Reset event
        # Declare all the variables
        self._eventID = LONG_MAX  # Largest possible number, invalid value
        self._hasEvent = False
        self._inEvent = {}
        self._eventChTimes = {}
        self._eventWaveforms = {}
        self._baseline = {}
        self._qShort = {}
        self._qLong = {}

        # Read in the event information
        # Need to keep reading till we get head1
        while head1 := self._f.read(4):
            head1 = int.from_bytes(head1, "little")
            if (head1 & 0xFFFF0000) == 0xA0000000:
                break
        else:
            return False

        head2 = self._f.read(4)
        if head2 == bytes():
            return False
        head2 = int.from_bytes(head2, "little")

        head3 = self._f.read(4)
        if head3 == bytes():
            return False
        head3 = int.from_bytes(head3, "little")

        head4 = self._f.read(4)
        if head4 == bytes():
            return False
        head4 = int.from_bytes(head4, "little")

        # print(head1, head2, head3, head4)

        # The event size as a longword, x4 for in bytes
        eventSize = head1 & 0b00001111111111111111111111111111
        dualChannelMask = head2 & 0b11111111
        evtCount = head3 & 0b00000000111111111111111111111111

        # Scan through the channel headers
        for i in range(self.channels):
            if dualChannelMask & (1 << i):
                chHead1 = self._f.read(4)
                if chHead1 == bytes():
                    return False
                chHead1 = int.from_bytes(chHead1, "little")

                chHead2 = self._f.read(4)
                if chHead2 == bytes():
                    return False
                chHead2 = int.from_bytes(chHead2, "little")

                dualTrace = (chHead2 & 0b10000000000000000000000000000000) >> 31
                chargeEnabled = (chHead2 & 0b01000000000000000000000000000000) >> 30
                timeEnabled = (chHead2 & 0b00100000000000000000000000000000) >> 29
                extrasEnabled = (chHead2 & 0b00010000000000000000000000000000) >> 28
                samplesEnabled = (chHead2 & 0b00001000000000000000000000000000) >> 27
                extrasOpEnabled = (chHead2 & 0b00000100000000000000000000000000) >> 26
                extrasWord = (chHead2 & 0b00000011100000000000000000000000) >> 23

                aggregateSize = chHead1 & 0b00000000001111111111111111111111
                recordSize = chHead2 & 0b00000000000000001111111111111111

                chTime = self._f.read(4)
                if chTime == bytes():
                    return False
                chTime = int.from_bytes(chTime, "little")
                ch = 2 * i + ((chTime & 0b10000000000000000000000000000000) >> 31)

                self._eventWaveforms[ch] = []
                self._inEvent[ch] = True
                recordSize = int(recordSize * 8 / 2)
                for j in range(recordSize):
                    sample = self._f.read(4)
                    sample = int.from_bytes(sample, "little")
                    self._eventWaveforms[ch].append(
                        (sample & 0b00000000000000000011111111111111)
                    )
                    self._eventWaveforms[ch].append(
                        (sample & 0b00111111111111110000000000000000) >> 16
                    )

                extras = self._f.read(4)
                if extras == bytes():
                    return False
                extras = int.from_bytes(extras, "little")

                charge = self._f.read(4)
                if charge == bytes():
                    return False
                charge = int.from_bytes(charge, "little")

                qLong = (charge & 0b11111111111111110000000000000000) >> 16
                qShort = charge & 0b00000000000000000111111111111111
                self._qLong[ch] = qLong
                self._qShort[ch] = qShort

                if extrasWord == 0b000:
                    self._baseline[ch] = (
                        extras & 0b00000000000000001111111111111111
                    ) / 4  # divide by 4 as per manual
                else:
                    self._baseline[ch] = Pyrate.NONE

                timeHi = (extras & 0b11111111111111110000000000000000) << 15
                timeLo = chTime & 0b01111111111111111111111111111111
                self._eventChTimes[ch] = timeHi + timeLo

                # Convert to ns
                self._eventChTimes[ch] = 2 * self._eventChTimes[ch]

                # Find the smallest event channel time, and set it to the
                # reader's event time
                if self._eventChTimes[ch] < self._eventID:
                    self._eventID = self._eventChTimes[ch] + self.timeshift

                # Check for extra large waveforms
                if (
                    not self._large_waveform_warning
                    and len(self._eventWaveforms[ch]) > MAX_TRACE_LENGTH
                ):
                    print(
                        f"WARNING: Extra large waveform detected in {self.name}, channel {i} has length {len(self._eventWaveforms[ch])}.\n"
                        "Double check the reader matches the firmware"
                    )
                    self._large_waveform_warning = True

        # Update the number of bytes read by the eventSize
        self._bytes_read += 4 * eventSize
        # Update the progress
        self._progress = self._bytes_read / self._size
        self._hasEvent = True

        return True


# EOF
