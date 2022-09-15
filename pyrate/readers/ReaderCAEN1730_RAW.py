""" Reader of binary files from CAEN1730 digitizers using the RAW firmware.

Binary data is written according to the scheme given in the RAW manual
"""

import os
import glob
import numpy as np

from pyrate.core.Input import Input

# Maximum length of the trace without a warning
MAX_TRACE_LENGTH = 50000
LONG_MAX = 2**64

class ReaderCAEN1730_RAW(Input):
    __slots__ = ["_files", "_f", "_files_index", "_sizes", "size", "_bytes_read", 
                 "_inEvent", "timeshift", "_eventWaveforms", "channels",
                 "_large_waveform_warning"]

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

        self.channels = 8
        self.timeshift = 0 if "timeshift" not in config else config["timeshift"]
        # Set the outputs manually
        outputs = {}
        for ch in range(self.channels):
            output_format = "{name}_ch{ch}_{variable}" # Default formatting
            if "output" in config:
                # The user has provided a custom output formatting
                output_format = config["output"]
            outputs.update({f"{ch}_timestamp": output_format.format(name=self.name, ch=ch, variable="timestamp"), 
                            f"{ch}_waveform": output_format.format(name=self.name, ch=ch, variable="waveform")})

        self.output = outputs

        # Prepare all the files
        self.is_loaded = False
        self._files = []
        for f in self.config["files"]:
            f = os.path.expandvars(f)
            self._files += sorted(glob.glob(f))

        self._files_index = 0
        self._sizes = [os.path.getsize(f) for f in self._files]
        self._bytes_read = 0
        self.size = sum(self._sizes)
        # Set the progress to 0, unless the files are empty
        self._progress = 0 if self.size !=0 else 1

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

        if not self._f: return
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
        
        #Put the event on the store
        if not skip:
            for ch in range(self.channels):
                if ch in self._inEvent:
                    self.store.put(f"{self.output[f'{ch}_timestamp']}", self._eventTime)
                    self.store.put(f"{self.output[f'{ch}_waveform']}", np.array(self._eventWaveforms[ch], dtype="int32"))

        # Get the next event
        if not self.read_next_event():
            self._load_next_file()

        return True
    
    def skip_events(self, n):
        """ Skips over n events
        """
        for i in range(n):
            if not self.get_event(skip=True):
                break

    def read_next_event(self):
        # Reset event
        self._eventTime = LONG_MAX
        self._hasEvent = False
        self._inEvent = {}
        self._eventWaveforms = {}

        # Read in the event information
        # Need to keep reading till we get head1
        while head1 := self._f.read(4):
            head1 = int.from_bytes(head1, "little")
            if (head1 & 0xFFFF0000) == 0xa0000000:
                break
        else:
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

        # RAW things
        # The event size as a longword, x4 for in bytes
        eventSize = head1 & 0b00001111111111111111111111111111
        boardID = head2 & 0b11111000000000000000000000000000
        pattern = head2 & 0b00000000111111111111111100000000
        channelMaskLo = head2 & 0b11111111
        channelMaskHi = head3 & 0b11111111000000000000000000000000
        eventCount = head3 & 0b00000000111111111111111111111111
        channelMask = (channelMaskHi << 8) + (channelMaskLo)
        TTT = head4

       # Figure out what channels are in the event
        numCh = 0

        for i in range(self.channels):
            if channelMask & (1 << i):
                numCh += 1
                self._inEvent[i] = True
                self._eventWaveforms[i] = []

        recordSize = int(2*(eventSize - 4)/numCh)
        
        # Read in the waveform data
        for i in range(self.channels):
            if channelMask & (1 << i):
                for j in range(recordSize):
                    sample = self._f.read(2)
                    if (sample == bytes()):
                        return False
                    self._eventWaveforms[i].append(int.from_bytes(sample,"little"))
            
                # Check for extra large waveforms
                if not self._large_waveform_warning and len(self._eventWaveforms[i]) > MAX_TRACE_LENGTH:
                    print(f"WARNING: Extra large waveform detected in {self.name}, channel {i} has length {len(self._eventWaveforms[i])}."
                        "Double check the reader matches the firmware")
                    self._large_waveform_warning = True

        self._eventTime = 8*((pattern << 24) + TTT) + self.timeshift
        
        # Update the number of bytes read by the eventSize
        self._bytes_read += 4*eventSize
        # Update the progress
        self._progress = self._bytes_read / self.size
        self._hasEvent = True

        return True

# EOF