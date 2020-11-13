""" Reader of a PostgreSQL database. 
"""
import psycopg2

from pyrate.core.Reader import Reader


class ReaderPostgreSQL(Reader):
    __slots__ = ["db", "_db_connection", "_db_cursor"]

    def __init__(self, name, store, logger, db):
        super().__init__(name, store, logger)
        self.db = db

    def load(self):
        self.is_loaded = True
        try:
            self._db_connection = psycopg2.connect(
                " ".join([f"{k}='{v}'" for k, v in self.db.items()])
            )

        except (Exception, psycopg2.Error) as error:
            sys.exit(
                f"ERROR: database connection required for dbname {self.db['dbname']} has failed."
            )

        self._db_cursor = self._db_connection.cursor()

    def offload(self):
        self.is_loaded = False
        self._db_cursor.close()
        self._db_connection.close()

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
