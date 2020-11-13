""" Reader of a PostgreSQL database. 
"""
import psycopg2

from pyrate.core.Reader import Reader


class ReaderPostgreSQL(Reader):
    __slots__ = ["f", "structure"]

    def __init__(self, name, store, logger, f_name, structure):
        super().__init__(name, store, logger)
        self.f = f_name
        self.structure = structure

    def load(self):
        self.is_loaded = True
        self._idx = 0
        pass

    def offload(self):
        self.is_loaded = False
        pass

    def read(self, name):

        if name.startswith("EVENT:"):
            pass

        elif name.startswith("INPUT:"):
            pass

    def set_n_events(self):
        """Reads number of events using the last event header."""
        if not self._n_events:
            pass

    def _break_path(self, name):
        """Return variable name and eventual channel."""
        pass


# EOF
