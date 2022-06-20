""" Reader of a WaveCatcher file. 
This version of the reader uses memory mapping to read the file:
https://docs.python.org/3.0/library/mmap.html.
This makes the reading process less memory demanding but slightly slower.
This reader should be used for larger files, e.g. >= 1 GB.
"""
import mmap

from pyrate.core.Reader import Reader


class ReaderWaveCatcherMMAP(Reader):
    __slots__ = ["f", "structure", "_event", "_mmf", "_mmidx"]

    def __init__(self, name, config, store, logger, f_name, structure):
        super().__init__(name, config, store, logger)
        self.f = f_name
        self.structure = structure

    def load(self):
        self.is_loaded = True
        self.f = open(self.f, "r", encoding="utf-8")
        self._idx = 0

        self._mmf = mmap.mmap(self.f.fileno(), length=0, access=mmap.ACCESS_READ)
        self._mmidx = None
        self._event = 0

        self.f.close()

    def offload(self):
        self.is_loaded = False
        self._mmf.close()

    def read(self, name):

        if name.startswith("EVENT:"):

            if self._mmidx != self._idx + 1:
                self._mmidx = self._idx + 1

                event = f"=== EVENT {self._mmidx} ==="

                self._move(event)
                self._event = self._mmf.tell()

            variable, channel = self._break_path(name)

            self._read_variable(name, channel, variable)

        elif name.startswith("INPUT:"):

            self._read_header(name)

    def set_n_events(self):
        """Reads number of events using the last event header."""
        if not self._n_events:
            pos_current_line = self._mmf.tell()

            self._move("EVENT ", opt="bkw")

            self._n_events = int(self._mmf.readline().decode("utf-8").split(" ")[1])

            self._mmf.seek(pos_current_line)

    def _read_header(self, name):
        """Reads variable from run header and puts it in the transient store."""
        pos_current_line = self._mmf.tell()

        variable = name.split(":")[1]

        self._mmf.seek(0)

        pos_variable = self._mmf.find(variable.encode("utf-8")) + len(variable)

        range_value = self._mmf[pos_variable : pos_variable + 40].decode("utf-8")

        for s in range_value.split(" ")[1:]:
            if s:
                value = str(s).replace("[", "").replace("]", "")
                break

        self.store.put(name, value, "TRAN")

        self._mmf.seek(pos_current_line)

    def _read_variable(self, name, channel, variable):
        """Reads variable from the event  and puts it in the transient store."""
        pos_current_line = self._mmf.tell()

        if channel:
            self._move(channel)

            if variable == "RawWaveform":
                # will need to move one line forward.
                self._mmf.readline()

                range_value = self._mmf.readline().decode("utf-8")

                value = [float(s) for s in range_value.split(" ")[:-1]]

            else:
                pos_variable = self._mmf.find(variable.encode("utf-8"))

                range_value = self._mmf[pos_variable : pos_variable + 40].decode(
                    "utf-8"
                )

                for s in range_value.split(" ")[1:]:
                    if s:
                        value = float(s)
                        break
        else:
            self._move(variable)

            pos_variable = self._mmf.find(variable.encode("utf-8"))

            range_value = self._mmf[pos_variable : pos_variable + 40].decode("utf-8")

            for s in range_value.split(" ")[1:]:
                if s and not "=" in s and not s in variable:
                    value = str(s)
                    break

        self.store.put(name, value, "TRAN")

        self._mmf.seek(pos_current_line)

    def _break_path(self, name):
        """Return variable name and eventual channel."""

        t = name.split(":")

        ch, var = None, None

        if "CH" in name:
            var = t[2]
            ch = t[1].replace("CH", "CH: ")
        else:
            var = t[1]

        return var, ch

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
