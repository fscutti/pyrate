""" Reader of a WaveDump file. 
This version of the reader uses memory mapping to read the file:
https://docs.python.org/3.0/library/mmap.html.
"""
import mmap
# import numpy as np

from pyrate.core.Reader import Reader


class ReaderWaveDumpMMAP(Reader):
    __slots__ = [
        "f",
        "structure",
        "_event",
        "_mmf",
        "_mmidx",
        "_mmidx_offset",
        "_len_waveform",
    ]

    def __init__(self, name, store, logger, f_name, structure):
        super().__init__(name, store, logger)
        self.f = f_name
        self.structure = structure

    def load(self):
        self.is_loaded = True
        self.f = open(self.f, "r", encoding="utf-8")
        self._idx = 0

        self._mmf = mmap.mmap(self.f.fileno(), length=0, access=mmap.ACCESS_READ)
        self._mmidx = None
        self._mmidx_offset = None
        self._event = 0

        self._set_len_waveform()

        self.f.close()

    def offload(self):
        self.is_loaded = False
        self._mmf.close()

    def read(self, name):

        if name.startswith("EVENT:"):

            if self._mmidx != self._idx + self._mmidx_offset:
                self._mmidx = self._idx + self._mmidx_offset

                event = f"Event Number: {self._mmidx}"

                self._move(event)
                self._event = self._mmf.tell()

            variable = self._break_path(name)

            self._read_variable(name, variable)

        elif name.startswith("INPUT:"):

            self._read_header(name)

    def _set_len_waveform(self):
        """Set the length of recorded waveform parameter."""
        pos_current_line = self._mmf.tell()

        self._mmf.seek(self._mmf.find(b"Record Length: "), 0)
        self._len_waveform = int(self._mmf.readline().decode("utf-8").split(" ")[2])

        self._mmf.seek(pos_current_line)

    def set_n_events(self):
        """Reads number of events using the last event header.
        WaveDump files might have an offset from the first event.
        """
        if not self._n_events:
            pos_current_line = self._mmf.tell()

            self._mmf.seek(self._mmf.find(b"Event Number: "), 0)
            self._mmidx_offset = int(self._mmf.readline().decode("utf-8").split(" ")[2])

            self._mmf.seek(self._mmf.rfind(b"Event Number: "))
            self._n_events = int(self._mmf.readline().decode("utf-8").split(" ")[2])

            # N.B.: the real number of events should contain one more event.
            # We'll discard that as often is broken.
            self._n_events = self._n_events - self._mmidx_offset

            self._mmf.seek(pos_current_line)

    def _read_header(self, name):
        """Reads variable from run header and puts it in the transient store."""
        pos_current_line = self._mmf.tell()

        variable = name.split(":")[-1]

        if not "Run" in variable:
            self._move(variable)
            # Get the string of the header variable
            line = self._mmf.readline().decode("utf-8").split(variable)[-1]
            # Get rid of the junk, and type cast to int depedning on base
            value = int(line.split(" ")[-1], 16) if "0x" in line else int(line.split(" ")[-1])

        else:
            self._move(variable, "bkw")
            value = int(self._mmf.readline().decode("utf-8").split(" ")[-1])

        self.store.put(name, value, "TRAN")

        self._mmf.seek(pos_current_line)

    def _read_variable(self, name, variable):
        """Reads variable from the event and puts it in the transient store."""
        pos_current_line = self._mmf.tell()

        if variable == "RawWaveform":
            # will need to move one line forward.

            self._move("DC offset (DAC)")
            self._mmf.readline()

            value = [
                int(self._mmf.readline().decode("utf-8"))
                for w_idx in range(self._len_waveform)
            ]
            # # Convert to numpy
            # value = np.fromiter(value, dtype=np.int, count=self._len_waveform)

        else:
            self._move(variable)

            pos_variable = self._mmf.find(variable.encode("utf-8")) + len(variable)

            range_value = self._mmf[pos_variable : pos_variable + 40].decode("utf-8")

            for s in range_value.split(" ")[1:]:
                if s:
                    value = str(s.split("\n")[0])
                    break

        self.store.put(name, value, "TRAN")

        self._mmf.seek(pos_current_line)

    def _break_path(self, name):
        """Return the variable name. """

        return name.split(":")[-1]

    def _move(self, s, opt="frw"):
        """Move file position to beginning of string s.
        The option of choosing to read the file backward is given.
        If the seek operation fails one time it performs a new
        search from the beginning of the file."""

        s = s.encode("utf-8")

        if opt == "bkw":
            self._mmf.seek(self._mmf.rfind(s))
        else:
            try:
                self._mmf.seek(self._mmf.find(s, self._event))

            except ValueError:
                self._mmf.seek(self._mmf.find(s, 0))


# EOF
