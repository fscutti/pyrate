""" Reader of a PostgreSQL database. 
"""
import sys
import psycopg2

from pyrate.core.Reader import Reader


class ReaderPostgreSQL(Reader):
    __slots__ = ["db", "_db_connection", "_db_cursor", "_dbidx", "_tables"]

    def __init__(self, name, store, logger, db):
        super().__init__(name, store, logger)
        self.db = db

    def load(self):
        self.is_loaded = True
        try:
            self._db_connection = psycopg2.connect(
                " ".join([f"{k}='{v}'" for k, v in self.db["connection"].items()])
            )

        except (Exception, psycopg2.Error) as error:
            sys.exit(
                f"ERROR: database connection required for dbname {self.db['connection']['dbname']} has failed."
            )

        self._db_cursor = self._db_connection.cursor()
        self._tables = self.db["tables"]

        self._dbidx = None
        self._idx = 0

    def offload(self):
        self.is_loaded = False
        self._db_cursor.close()
        self._db_connection.close()

    def read(self, name):

        if name.startswith("EVENT:"):

            table, event, variable = self._break_path(name)

            self._read_variable(name, table, event, variable)

        elif name.startswith("INPUT:"):

            query = self._break_path(name)

            self._read_data(name, query)

    def _read_data(self, name, query):
        """Executes query on the database."""

        self._db_cursor.execute(query)

        value = self._db_cursor.fetchall()

        self.store.put(name, value, "TRAN")

    def _read_variable(self, name, table, row, variable):
        """Reads variable from specific row, considered to be an event."""

        self._db_cursor.execute(f"SELECT {variable} FROM {table} OFFSET {row} LIMIT 1")

        value = self._db_cursor.fetchall()[0][0]

        self.store.put(name, value, "TRAN")

    def set_n_events(self):
        """Reads number of events which in this case are the table rows."""
        if not self._n_events:
            self._db_cursor.execute(f"SELECT COUNT(*) FROM {self._tables[0]};")
            self._n_events = int(self._db_cursor.fetchall()[0][0])

    def _break_path(self, name):
        """Return variable name and eventual channel."""

        t = name.split("QUERY:")[1]

        if "(" in t:
            return t.replace("(", "").replace(")", "")
        else:
            tab, ev, var = t.split(":")
            return tab, ev, var


# EOF
