""" Base class for reading input files. 
"""
import sys

from pyrate.core.Reader import Reader
from pyrate.readers.ReaderROOT import ReaderROOT

from pyrate.utils import functions as FN
from pyrate.utils import strings as ST


class Input(Reader):
    def __init__(self, name, store, logger, iterable=(), **kwargs):
        super().__init__(name, store, logger)
        self.__dict__.update(iterable, **kwargs)

    def load(self):

        self._f_idx = 0

        if not hasattr(self, "structure"):
            self.structure = {}

        g_names = {0: "0"}
        if hasattr(self, "group"):
            for g_idx, g_name in enumerate(ST.get_items(self.group)):
                g_names[g_idx] = g_name

        self.groups = {}
        for g_idx, g_files in enumerate(self.files):
            self.groups[g_names[g_idx]] = g_files
            self._init_reader(g_names[g_idx], self._f_idx)

        self._n_files = len(self.files)

    def read(self, name):
        """Looks for the object in the entire input. Initialises readers if
        they were not. Global objects are accessed with the INPUT: prefix while
        event-related variables with the EVENT: one."""

        n_tags = name.split("_")

        for g_name, g_readers in self.groups.items():

            if len(self.groups) > 1:
                if not ST.check_tag(g_name, n_tags):
                    continue

            if "INPUT:" in name:
                for f_idx, reader in enumerate(g_readers):

                    if isinstance(reader, str):
                        self._init_reader(g_name, f_idx)

                    g_readers[f_idx].read(name)

            elif "EVENT:" in name:
                self._init_reader(g_name, self._f_idx)

                g_readers[self._f_idx].read(name)

    def set_n_events(self):
        """Reads number of events of the entire input."""
        if not self._n_events:

            self._n_events = 0
            for g_name, g_readers in self.groups.items():
                for f_idx, reader in enumerate(g_readers):

                    if isinstance(reader, str):
                        self._init_reader(g_name, f_idx)

                    self._n_events += g_readers[f_idx].get_n_events()
                if self._n_events:
                    break

    def set_idx(self, idx):

        g = self.groups["0"]

        if idx > self._idx:
            verse = "frw"

            while (idx - self._idx) > (
                g[self._f_idx].get_n_events() - 1 - g[self._f_idx].get_idx()
            ):

                if self._move_readers(verse) > -1:

                    # increment global index to match last index of previous file.
                    self._idx += (
                        g[self._f_idx - 1].get_n_events()
                        - 1
                        - g[self._f_idx - 1].get_idx()
                    )

                    # increment global index to match first index of next file.
                    # To do: loop over readers here
                    g[self._f_idx].set_idx(0)
                    self._idx += 1

                else:
                    self.idx = -1

                    return self._idx

            if (idx - self._idx) <= (
                g[self._f_idx].get_n_events() - 1 - g[self._f_idx].get_idx()
            ):
                # increment global index to match the gap.
                # To do: loop over readers here
                g[self._f_idx].set_idx((idx - self._idx))
                self._idx = idx

                return self._idx

        elif idx < self._idx:
            verse = "bkw"

        else:
            return self._idx

    def set_next_event(self):
        """Move to the next event in the sequence."""
        for g_name, g_readers in self.groups.items():

            if g_readers[self._f_idx].set_next_event() < 0:
                if self._move_readers("frw") < 0:

                    self._idx = -1
                    return self._idx

                else:
                    self._idx += 1
                    return self._idx

        self._idx += 1
        return self._idx

    def _move_readers(self, option="frw"):
        """Advances the file index to the next valid group of files  withing
        the boundary of their number. This function is "transforming" a string
        to a class (the individual reader instances) so it will leave a class
        instance as a trace of previous usage.
        """
        if option == "frw":

            if self._f_idx < self._n_files - 1:
                self._f_idx += 1

                for g_name in self.groups:
                    self._init_reader(g_name, self._f_idx)

            else:
                self._f_idx = -1

            return self._f_idx

        elif option == "bkw":

            if self._f_idx > 0:
                self._f_idx -= 1

                for g_name in self.groups:
                    self._init_reader(g_name, self._f_idx)

            else:
                self._f_idx = 0

            return self._f_idx

    def _init_reader(self, g_name, f_idx):
        """Instantiate different readers here. If the instance exists nothing
        is done. This function transforms a string into a reader.
        """
        if isinstance(self.groups[g_name][f_idx], str):

            r_name = "_".join([g_name, str(f_idx)])

            f = self.groups[g_name][f_idx]

            if f.endswith(".root"):
                reader = ReaderROOT(r_name, self.store, self.logger, f, self.structure)

            elif f.endswith(".dat"):
                pass

            elif f.endswith(".txt"):
                pass

            reader.load()

            self.groups[g_name][f_idx] = reader


# EOF
