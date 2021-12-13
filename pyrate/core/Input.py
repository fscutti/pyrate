""" The Input class handles the file readers for one input. 
An input is intended to be a collection of files, eventually 
organised in groups. This class also offers the possibility
to read from a database, synchronously or not, wrt to files.
"""
import os
import sys
from importlib import import_module

from pyrate.core.Reader import Reader
from pyrate.readers.ReaderROOT import ReaderROOT
#from pyrate.readers.ReaderWaveCatcherLC import ReaderWaveCatcherLC    # this reader is not the preferred one but we'll keep this line for reference.
from pyrate.readers.ReaderWaveCatcherMMAP import ReaderWaveCatcherMMAP
from pyrate.readers.ReaderBlueTongueMMAP import ReaderBlueTongueMMAP
from pyrate.readers.ReaderWaveDumpMMAP import ReaderWaveDumpMMAP
from pyrate.readers.ReaderPostgreSQL import ReaderPostgreSQL

from pyrate.utils import functions as FN
from pyrate.utils import strings as ST

GB = 1e9


class Input(Reader):
    def __init__(self, name, store, logger, iterable=(), **kwargs):
        super().__init__(name, store, logger)
        self.__dict__.update(iterable, **kwargs)

    def load(self):

        self.is_loaded = True

        self._f_idx = 0

        if not hasattr(self, "structure"):
            self.structure = {}

        if not hasattr(self, "database"):
            # The input might or not have samples associated to it.
            # If it does, it has to read from files. This is not
            # strictly necessary, as it might just want to read
            # from a database.

            g_names = {0: "0"}

            if hasattr(self, "samples"):
                if "groups" in self.samples["tags"]:

                    for g_idx, g_name in enumerate(
                        ST.get_items(self.samples["tags"]["groups"])
                    ):
                        g_names[g_idx] = g_name

            self._n_groups = len(self.files)
            self._n_files = len(self.files[0])

            self.groups = {}

            for g_idx, g_files in enumerate(self.files):

                if not isinstance(g_files, list):
                    g_files = [g_files]

                self.groups[g_names[g_idx]] = g_files
                if hasattr(self, "reader"):
                    self._set_group_reader(g_names[g_idx], self._f_idx, self.reader)
                else:
                    self._set_group_reader(g_names[g_idx], self._f_idx)

        else:
            self._set_db_reader(self.database)

        assert hasattr(self, "groups") or hasattr(
            self, "db"
        ), "ERROR: input {self.name} does not have files or a database associated to it."

    def offload(self):

        self.is_loaded = False

        if hasattr(self, "groups"):
            for g_name, g_readers in self.groups.items():
                for f_idx, reader in enumerate(g_readers):

                    if isinstance(reader, str):
                        continue

                    if reader.is_loaded:
                        g_readers[f_idx].offload()

        if hasattr(self, "db"):
            self.db.offload()

    def _read_from_groups(self, name):
        for g_name, g_readers in self.groups.items():

            # Make sure we're in the group we want to get the info from
            if "GROUP:" in name:
                req_g_name = name.split(":")

                if not g_name == req_g_name[2]:
                    # Not the right group, skip this group
                    continue

            if name.startswith("INPUT:"):
                for f_idx, reader in enumerate(g_readers):

                    if isinstance(reader, str):
                        self._set_group_reader(g_name, f_idx)

                    if name.startswith("INPUT:READER:"):
                        variable = name.split(":")[-1]
                        if variable == "name":
                            self.store.put(name, g_readers[self._f_idx].__class__.__name__, "TRAN")
                        elif variable == "slots":
                            self.store.put(name, g_readers[self._f_idx].__slots__, "TRAN")
                        elif variable == "module":
                            self.store.put(name, g_readers[self._f_idx].__class__.__module__, "TRAN")
                        else:
                            sys.exit(f"ERROR: Invalid reader variable '{variable}'\nError occured when attempting to get '{name}' from the store.")
                    else:
                        g_readers[f_idx].read(name)

            elif name.startswith("EVENT:"):
                self._set_group_reader(g_name, self._f_idx)
                g_readers[self._f_idx].read(name)

            elif name.startswith("GROUPS"):
                # Adds the group keys to the store so the user can know
                # what groups are in use without checking the config
                self.store.put(name, list(self.groups.keys()), "TRAN")

    def _read_from_database(self, name):
        self.db.read(name)

    def read(self, name):
        """Looks for the object in the entire input. Initialises readers if
        they were not. Global objects are accessed with the INPUT: prefix while
        event-related variables with the EVENT: one. The QUERY: tag, inserted
        in the name as INPUT/EVENT:QUERY:xyz is checked to understand whether to
        read from a database."""

        if "QUERY:" in name:
            self._read_from_database(name)

        else:
            self._read_from_groups(name)

    def set_n_events(self):
        """Reads number of events of the entire input."""
        if not self._n_events:

            if hasattr(self, "db"):
                self.db.set_n_events()

            if not hasattr(self, "groups"):
                self._n_events = self.db.get_n_events()

            else:
                self._n_events, g_n_events = 0, 0

                for g_name, g_readers in self.groups.items():
                    for f_idx, reader in enumerate(g_readers):

                        if isinstance(reader, str):
                            self._set_group_reader(g_name, f_idx)

                        f_n_events = g_readers[f_idx].get_n_events()
                        self._n_events += f_n_events

                    if not g_n_events:
                        g_n_events = self._n_events
                    else:
                        if not g_n_events == self._n_events:
                            sys.exit(
                                f"ERROR: inconsistent nevents for {self.name} groups"
                            )

                    self._n_events = 0
                self._n_events = g_n_events

    def set_idx(self, idx):
        """Setting the event index of the global input reader to a specific value.
        This operation requires moving/jumping to specific file readers which might
        have not been initialised yet.
        """

        if not self._n_events:
            self.set_n_events()

        if hasattr(self, "db") and not hasattr(self, "groups"):
            self.db.set_idx(idx)

        else:
            if idx > self._n_events - 1:
                # ----------------------------------------
                # Don't move outside boundaries
                # ----------------------------------------

                self._idx = -1
                return

            else:
                # use a generic group to pick up a reference reader.
                g = self.groups[list(self.groups)[0]]

                if idx > self._idx:
                    # ----------------------------------------
                    # Moving forward
                    # ----------------------------------------
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

                            for g_name, g_readers in self.groups.items():
                                g_readers[self._f_idx].set_idx(0)

                            self._idx += 1

                        else:
                            self._idx = -1
                            return

                    if (idx - self._idx) <= (
                        g[self._f_idx].get_n_events() - 1 - g[self._f_idx].get_idx()
                    ):
                        increment = g[self._f_idx].get_idx() + (idx - self._idx)

                        for g_name, g_readers in self.groups.items():
                            g_readers[self._f_idx].set_idx(increment)

                        self._idx = idx
                        return

                elif idx < self._idx:
                    # ----------------------------------------
                    # Moving backwards
                    # ----------------------------------------
                    verse = "bkw"
                    sys.exit(
                        f"ERROR: supporting moving the event index backward is still not supported!"
                    )

                else:
                    # ----------------------------------------
                    # Don't move
                    # ----------------------------------------
                    return self._idx

    def set_next_event(self):
        """Move to the next event in the sequence."""
        if hasattr(self, "db") and not hasattr(self, "groups"):
            self.db.set_next_event()

        else:
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
        instance as a trace of previous usage. Only file-oriented readers support
        this functionality.
        """
        if option == "frw":

            if self._f_idx < self._n_files - 1:
                self._f_idx += 1

                for g_name in self.groups:
                    self._set_group_reader(g_name, self._f_idx)

            else:
                self._f_idx = -1

            return self._f_idx

        elif option == "bkw":

            if self._f_idx > 0:
                self._f_idx -= 1

                for g_name in self.groups:
                    self._set_group_reader(g_name, self._f_idx)

            else:
                self._f_idx = 0

            return self._f_idx

    def _set_db_reader(self, db):
        """Instantiates the reader for the database."""
        r_name = "_".join([self.name, db["connection"]["dbname"]])

        self.db = ReaderPostgreSQL(r_name, self.store, self.logger, db)

        self.db.load()

    def _set_group_reader(self, g_name, f_idx, reader=None):
        """Instantiate different readers here. If the instance exists nothing
        is done. This function transforms a string into a reader.
        """
        if isinstance(self.groups[g_name][f_idx], str):

            r_name = "_".join([g_name, str(f_idx)])

            f_name = self.groups[g_name][f_idx]
            
            if reader:
                # The user has specified the reader they want to use
                # Try to import the reader class
                reader_module = "pyrate.readers."+reader
                try:
                    ReaderModule = import_module(reader_module)
                    ReaderClass = ReaderModule.__getattribute__(reader)
                except ImportError as err:
                    sys.exit(f"Error: {err}\n Unable to import reader '{reader}' from module '{reader_module}'\n"
                            "Check that the reader is in pyrate/readers, that the class and module have the same name, and is added the nearest __init__.py")

                self.logger.info(f"User-set reader for {f_name} to {reader}")
                reader = ReaderClass(r_name, self.store, self.logger, f_name, self.structure)
            else: 
                if f_name.endswith(".root"):
                    self.logger.info(f"Auto-setting reader for {f_name} to ReaderROOT")
                    reader = ReaderROOT(
                        r_name, self.store, self.logger, f_name, self.structure
                    )
                
                elif FN.is_bt(f_name, self.store, self.logger, self.structure):
                    # BlueTongue file
                    self.logger.info(f"Auto-setting reader for {f_name} to ReaderBlueTongueMMAP")
                    reader = ReaderBlueTongueMMAP(
                            r_name, self.store, self.logger, f_name, self.structure
                        )

                elif FN.is_wd_ascii(f_name):
                    # WaveDump file
                    self.logger.info(f"Auto-setting reader for {f_name} to ReaderWaveDumpMMAP")
                    reader = ReaderWaveDumpMMAP(
                        r_name, self.store, self.logger, f_name, self.structure
                    )
                elif FN.is_wc_ascii(f_name):
                    # WaveCatcher file
                    self.logger.info(f"Auto-setting reader for {f_name} to ReaderWaveCatcherMMAP")
                    reader = ReaderWaveCatcherMMAP(
                            r_name, self.store, self.logger, f_name, self.structure
                        )

                if not reader:
                    # Uh oh, we haven't got a reader yet!
                    self.logger.info(f"Unable to auto-set reader")
                    sys.exit("ERROR: pyrate could not determine file type. You can try specifying the reader manaully in the config.")
            
            reader.load()
            self.groups[g_name][f_idx] = reader

# EOF
