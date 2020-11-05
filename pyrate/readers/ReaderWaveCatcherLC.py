""" Reader of a WaveCatcher file.
"""
import mmap
import linecache
import os

from pyrate.core.Reader import Reader


class ReaderWaveCatcher(Reader):
    __slots__ = ["f", "structure", "_event", "_n_channels", "_header_size"]

    def __init__(self, name, store, logger, f_name, structure):
        super().__init__(name, store, logger)
        self.f = f_name
        self.structure = structure

    def load(self):
        self._idx = 0

        # lines are counted from 1
        self._event = 0

        # To do: get these other two variables dynamically
        # including initiating the structure.
        self._n_channels = 8
        self._header_size = 4
        if not self.structure:
            self.structure = {f"CH{idx}": 2 * (idx + 1) for idx in range(16)}

    def read(self, name):

        if name.startswith("EVENT:"):

            self._event = self._idx * (2 * self._n_channels + 2) + self._header_size + 1

            variable, channel, offset = self._break_path(name)

            _variable_line_idx = self._event + offset

            self._read_variable(name, channel, variable, _variable_line_idx)

        elif name.startswith("INPUT:"):
            pass

    def set_n_events(self):
        """Reads number of events using the last event header."""
        if not self._n_events:

            f = open(self.f, "r", encoding="utf-8")
            mmf = mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ)

            mmf.seek(mmf.rfind(b"EVENT "))

            self._n_events = int(mmf.readline().decode("utf-8").split(" ")[1])

            mmf.close()
            f.close()

    def _read_variable(self, name, channel, variable, variable_line_idx):

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
        #print()
        #print("EVENT: ", self._idx + 1)
        #print("Channel: ", channel)
        #print("Variable: ", variable)
        #print("LineNo: ", variable_line_idx)
        #print()

        self.store.put(name, value, "TRAN")

    def _get_line(self, l_idx):
        return linecache.getline(self.f, l_idx)

    def _break_path(self, name):

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
