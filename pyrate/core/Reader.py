""" Generic Reader base class.
N.B.: Inheriting objects reading individual files should only reimplement the functions below 
which are not fully defined, i.e. those containing the 'pass' instruction.
"""


class Reader:
    __slots__ = ["name", "store", "logger", "is_loaded", "_idx", "_n_events"]

    def __init__(self, name, store, logger):
        self.name = name
        self.store = store
        self.logger = logger
        self.is_loaded = False
        self._idx = 0
        self._n_events = None

    def load(self):
        """Initialises reader condition members and puts it in a 'read ready' condition."""
        pass

    def offload(self):
        """Closes files."""
        pass

    def read(self, name):
        """Gets object with given name. Event and global variables should be prepended a flag."""

        if "GROUP:" in name:
            pass

        if name.startswith("EVENT:"):
            pass

        elif name.startswith("INPUT:"):
            pass

    def get_idx(self):
        """Gets index of current event. """
        return self._idx

    def get_n_events(self):
        """Returns total number of events."""
        if self._n_events:
            return self._n_events
        else:
            self.set_n_events()
            return self._n_events

    def set_idx(self, idx):
        """Updates idx to defined value"""
        if not self._n_events:
            self.set_n_events()

        if idx > self._n_events - 1:
            self._idx = -1
        else:
            self._idx = idx

    def set_n_events(self):
        """Computes total number of events."""
        pass

    def set_next_event(self):
        """If the next event reading will not be valid it outputs -1."""

        if self._idx < self._n_events - 1:
            self._idx += 1
        else:
            self._idx = -1
        return self._idx

    def set_previous_event(self):
        """Sets idx to previous event."""
        pass

    def set_split_event(self):
        """Constructs idx conditions to handle event in segments."""
        pass


# EOF
