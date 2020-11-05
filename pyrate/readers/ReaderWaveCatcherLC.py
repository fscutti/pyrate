""" Reader of a WaveCatcher file.
"""
import mmap
import linecache
import os

from pyrate.core.Reader import Reader


class ReaderWaveCatcherLC(Reader):
    __slots__ = ["f", "structure", "_event", "_mmf", "_n_channels", "_header_size"]

    def __init__(self, name, store, logger, f_name, structure):
        super().__init__(name, store, logger)
        self.f = f_name
        self.structure = structure

    def load(self):

        self.is_loaded = True

        f = open(self.f, "r", encoding="utf-8")
        self._mmf = mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ)
        f.close()

        linecache.lazycache(self.f, globals())

        self._idx = 0

        self._event = 0

        self._header_size = 4
        self._n_channels = int(
            self._read_header("INPUT:NB OF CHANNELS ACQUIRED", no_store=True)
        )
        if not self.structure:
            self.structure = {
                f"CH{idx}": 2 * (idx + 1) for idx in range(self._n_channels)
            }

    def offload(self):
        self.is_loaded = False
        self._mmf.close()
        linecache.clearcache()

    def read(self, name):

        if name.startswith("EVENT:"):

            self._event = self._idx * (2 * self._n_channels + 2) + self._header_size + 1

            variable, channel, offset = self._break_path(name)

            _variable_line_idx = self._event + offset

            self._read_variable(name, channel, variable, _variable_line_idx)

        elif name.startswith("INPUT:"):

            self._read_header(name)

    def set_n_events(self):
        """Reads number of events using the last event header."""
        if not self._n_events:

            self._mmf.seek(self._mmf.rfind(b"EVENT "))

            self._n_events = int(self._mmf.readline().decode("utf-8").split(" ")[1])

    def _read_header(self, name, no_store=False):
        """Reads variable from run header and puts it in the transient store."""
        variable = name.split(":")[1]

        self._mmf.seek(0)

        pos_variable = self._mmf.find(variable.encode("utf-8")) + len(variable)

        range_value = self._mmf[pos_variable : pos_variable + 40].decode("utf-8")

        for s in range_value.split(" ")[1:]:
            if s:
                value = str(s).replace("[", "").replace("]", "").replace(" ", "")
                break

        if no_store:
            return value
        else:
            self.store.put(name, value, "TRAN")

    def _read_variable(self, name, channel, variable, variable_line_idx):
        """Reads variable from the event  and puts it in the transient store."""
        line = self._get_line(variable_line_idx)

        if channel:
            if variable == "RawWaveform":

                value = [float(s) for s in line.split(" ")[:-1]]

            else:
                pos_variable = line.find(variable)
                range_value = line[pos_variable : pos_variable + 40]

                for s in range_value.split(" ")[1:]:
                    if s:
                        value = float(s)
                        break
        else:
            pos_variable = line.find(variable)
            range_value = line[pos_variable : pos_variable + 40]

            for s in range_value.split(" ")[1:]:
                if s and not "=" in s and not s in variable:
                    value = str(s)
                    break
        # print()
        # print("EVENT: ", self._idx + 1)
        # print("Channel: ", channel)
        # print("Variable: ", variable)
        # print("LineNo: ", variable_line_idx)
        # print()

        self.store.put(name, value, "TRAN")

    def _get_line(self, l_idx):
        """Get line using cached file."""
        return linecache.getline(self.f, l_idx)

    def _break_path(self, name):
        """Return variable name, eventual channel
        name and offset wrt the start of the event."""

        t = name.split(":")

        var, ch, offset = None, None, 0

        if "CH" in name:
            var = t[2]
            ch = t[1]

            offset += self.structure[ch]

            if var == "RawWaveform":
                offset += 1
        else:
            var = t[1]
            offset += 1
        return var, ch, offset


# EOF
