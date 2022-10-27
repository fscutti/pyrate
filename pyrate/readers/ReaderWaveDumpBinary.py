""" Reader of CAEN WaveDump
"""

import os
import sys
import glob
import numpy as np

from pyrate.core.Input import Input

# Maximum length of the trace without a warning
BIN_HEADER = 24
MAX_TRACE_LENGTH = 50000
LONG_MAX = 2**64


class ReaderWaveDumpBinary(Input):
    __slots__ = [
        "_files",
        "_f",
        "_files_index",
        "_sizes",
        "size",
        "_bytes_read",
        "_variables",
        "_waveform",
        "timeshift",
        "_prevEventTime",
        "_eventTimeOverflows",
    ]

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

        self.timeshift = 0 if "timeshift" not in config else config["timeshift"]
        # Set the outputs manually
        output_format = "{name}_{variable}"  # Default formatting
        if "output" in config:
            # The user has provided a custom output formatting
            output_format = config["output"]
        self._variables = {
            "timestamp": output_format.format(name=self.name, variable="timestamp"),
            "waveform": output_format.format(name=self.name, variable="waveform"),
        }

        self.output = self._variables.values()

        # Prepare all the files
        self.is_loaded = False
        self._files = []
        for f in self.config["files"]:
            f = os.path.expandvars(f)
            self._files += sorted(glob.glob(f))
        if len(self._files) == 0:
            sys.exit(f"ERROR: in reader {self.name}, no files were found.")

        self._files_index = 0
        self._sizes = [os.path.getsize(f) for f in self._files]
        self._bytes_read = 0
        self.size = sum(self._sizes)
        # Set the progress to 0, unless the files are empty
        self._progress = 0 if self.size != 0 else 1

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
        self._prevEventTime = 0
        self._eventTimeOverflows = 0

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
            self.store.put(f"{self._variables[f'timestamp']}", self._eventID)
            self.store.put(
                f"{self._variables[f'waveform']}",
                np.array(self._waveform, dtype="int32"),
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
        self._waveform = []

        head1 = self._f.read(4)
        if head1 == "":
            return False
        head1 = int.from_bytes(head1, "little")
        head2 = self._f.read(4)
        if head2 == "":
            return False
        head2 = int.from_bytes(head2, "little")
        head3 = self._f.read(4)
        if head3 == "":
            return False
        head3 = int.from_bytes(head3, "little")
        head4 = self._f.read(4)
        if head4 == "":
            return False
        head4 = int.from_bytes(head4, "little")
        head5 = self._f.read(4)
        if head5 == "":
            return False
        head5 = int.from_bytes(head5, "little")
        head6 = self._f.read(4)
        if head6 == "":
            return False
        head6 = int.from_bytes(head6, "little")

        self._bytes_read += BIN_HEADER

        event_size = head1
        record_length = (head1 - BIN_HEADER) // 2
        # board_id = head2
        # channel = head3
        # event_number = head4
        # pattern = head5
        trigger_time_stamp = head6

        # Work out the eventTime, handling overflows
        self._eventID = (self._eventTimeOverflows * 2**31) + trigger_time_stamp
        if self._eventID < self._prevEventTime:
            self._eventTimeOverflows += 1
            self._eventID = (self._eventTimeOverflows * 2**31) + trigger_time_stamp
        self._prevEventTime = self._eventID

        i = 0
        while i < record_length and (value := self._f.read(2)):
            self._waveform.append(int(value))
            self._bytes_read += 2
            i += 1

        if i < record_length:
            # Uh oh we didn't get a full waveform
            return False

        # Update the progress
        self._progress = self._bytes_read / self.size
        self._hasEvent = True

        return True


# EOF
