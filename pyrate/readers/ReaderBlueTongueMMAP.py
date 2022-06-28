""" Reader of a BlueTongue binary file. (Files from BlueTongue are all assumed to be binary data).
This version of the reader uses memory mapping to read the file:
https://docs.python.org/3.0/library/mmap.html.

Binary data is written according to this scheme:
    https://darkmatteraustralia.atlassian.net/wiki/spaces/SABRE/pages/32276849/DAQ+-+Data+acquisition+for+experimental+data
It is read using this method: 
    https://docs.python.org/3.8/library/struct.html

EVENT or INPUT (header) variables should be accessed using the namespace reported in the following dictionaries:
    Example: EVENT:board_2:raw_waveform_ch_3, EVENT:timestamp, INPUT:n_boards, INPUT:board_1:name, etc...


Event dictionary ->

timestamp: xyz

( ... loop on board names b_idx ... )

board_(b_idx):
    event_counter: xyz
    trigger_time_tag: xyz

    ( ... loop on channel numbers c_idx ... )

    raw_waveform_ch_(c_idx): xyz (This is the waveform)

    (only if board type is CAEN1743)

    trigger_count_ch_(c_idx) : (This is the trigger count of channel c_idx)
    time_count_ch_(c_idx) : (This is the time count of channel c_idx)


Header dictionary ->

n_boards: xyz

( ... loop on board names b_idx ... )

board_(b_idx):
    name: xyz
    type: xyz
    record_length: xyz
    n_channels: xyz
    channel_numbers: (xyx, xyx, ...)

"""
import os
import mmap
import struct
import numpy as np

from pyrate.core.Reader import Reader

from pyrate.utils import functions as FN

_T = {i: struct.calcsize(i) for i in ["I", "c", "h", "H"]}


class ReaderBlueTongueMMAP(Reader):
    __slots__ = [
        "f",
        "structure",
        "_event",
        "_mmf",
        "_hd",
        "_ev",
        "_file_size",
        "_header_size",
        "_event_size",
    ]

    def __init__(self, name, store, logger, f_name, structure):
        super().__init__(name, store, logger)
        self.f = f_name
        self.structure = structure

    def load(self):
        self.is_loaded = True

        self._file_size = os.path.getsize(self.f)

        self.f = open(self.f, "rb")
        self._idx = 0

        self._mmf = mmap.mmap(self.f.fileno(), length=0, access=mmap.ACCESS_READ)
        self._event = 0

        self._event_size = 0
        self._header_size = 0

        self._set_header_dict()
        self._set_event_dict()

        self.f.close()

    def offload(self):
        self.is_loaded = False
        self._mmf.close()

    def read(self, name):

        if name.startswith("EVENT:"):

            if self._event != self._idx * self._event_size + self._header_size:
                self._event = self._idx * self._event_size + self._header_size

                self._move(self._event)

            variable = self._break_path(name)

            self._read_variable(name, variable)

        elif name.startswith("INPUT:"):

            variable = self._break_path(name)

            self._read_header(name, variable)

    def _get_items(self, i_number, i_type, merge=False):
        """Get a number of items from the file of type i_type.
        If the option merge is given the result is merged into one string."""
        items = struct.unpack(i_number * i_type, self._mmf.read(i_number * _T[i_type]))

        if merge:
            items = "".join([i.decode("ascii") for i in items])

        return items

    def _add_to_size(self, n_bytes, of_header=False):
        """Increments event or header size by n_bytes and returns a bytes interval."""

        attr = "_event_size"

        if of_header:
            attr = "_header_size"

        start = getattr(self, attr)

        setattr(self, attr, start + n_bytes)

        return start

    def _set_header_dict(self):
        """Grab all items from the header and put them into a dictionary.
        This function also sets the header size variable.
        As we will be reading items, the pointer position needs to be preserved."""

        current_pos = self._mmf.tell()

        self._hd = {"n_boards": self._get_items(1, "I")[0]}

        # here _add_to_size is called to compute the header size
        self._add_to_size(_T["I"], of_header=True)  # Number of Boards

        for b_idx in range(1, self._hd["n_boards"] + 1):

            self._hd[f"board_{b_idx}"] = {}

            b_name_length = self._get_items(1, "I")[0]
            b_type_length = self._get_items(1, "I")[0]

            self._hd[f"board_{b_idx}"]["name"] = self._get_items(
                b_name_length, "c", True
            )
            self._hd[f"board_{b_idx}"]["type"] = self._get_items(
                b_type_length, "c", True
            )

            self._hd[f"board_{b_idx}"]["record_length"] = self._get_items(1, "I")[0]
            self._hd[f"board_{b_idx}"]["n_channels"] = self._get_items(1, "I")[0]

            self._hd[f"board_{b_idx}"]["channel_numbers"] = self._get_items(
                self._hd[f"board_{b_idx}"]["n_channels"], "I"
            )

            self._add_to_size(_T["I"], of_header=True)  # Length of Board name
            self._add_to_size(_T["I"], of_header=True)  # Length of Board type

            self._add_to_size(b_name_length * _T["c"], of_header=True)  # Board name
            self._add_to_size(b_type_length * _T["c"], of_header=True)  # Board type

            self._add_to_size(_T["I"], of_header=True)  # Record length
            self._add_to_size(_T["I"], of_header=True)  # Number of channels

            self._add_to_size(
                self._hd[f"board_{b_idx}"]["n_channels"] * _T["I"], of_header=True
            )  # Channel numbers

        self._mmf.seek(current_pos)

    def _set_event_dict(self):
        """Get size of event in bytes."""

        self._ev = {"timestamp": (1, "I", self._add_to_size(_T["I"]))}

        for b_idx in range(1, self._hd["n_boards"] + 1):

            self._ev[f"board_{b_idx}"] = {}

            self._ev[f"board_{b_idx}"]["event_counter"] = (
                1,
                "I",
                self._add_to_size(_T["I"]),
            )
            self._ev[f"board_{b_idx}"]["trigger_time_tag"] = (
                1,
                "I",
                self._add_to_size(_T["I"]),
            )

            for c_idx in self._hd[f"board_{b_idx}"]["channel_numbers"]:

                self._ev[f"board_{b_idx}"][f"raw_waveform_ch_{c_idx}"] = (
                    self._hd[f"board_{b_idx}"]["record_length"],
                    "h",
                    self._add_to_size(
                        self._hd[f"board_{b_idx}"]["record_length"] * _T["h"]
                    ),
                )

            if self._hd[f"board_{b_idx}"]["type"] == "CAEN1743":

                for c_idx in self._hd[f"board_{b_idx}"]["channel_numbers"]:

                    self._ev[f"board_{b_idx}"][f"trigger_count_ch_{c_idx}"] = (
                        1,
                        "H",
                        self._add_to_size(_T["H"]),
                    )
                    self._ev[f"board_{b_idx}"][f"time_count_ch_{c_idx}"] = (
                        1,
                        "H",
                        self._add_to_size(_T["H"]),
                    )

        self._ev["check_word"] = (1, "H", self._add_to_size(_T["H"]))

    def set_n_events(self):
        """Reads number of events using the last event header."""
        if not self._n_events:
            self._n_events = int(
                (self._file_size - self._header_size) / self._event_size
            )

    def _read_header(self, name, variable):
        """Reads variable from the header dictionary and puts it in the transient store."""

        value = FN.grab(variable, self._hd)

        self.store.put(name, value, "TRAN")

    def _read_variable(self, name, variable):
        """Reads variable from the event and puts it in the transient store."""
        pos_current_line = self._mmf.tell()

        t = FN.grab(variable, self._ev)

        items_number, items_type, items_offset = t[0], t[1], t[2]

        self._mmf.seek(items_offset, 1)

        value = self._get_items(items_number, items_type)

        if "raw_waveform" in name:
            value = np.array(value, dtype='int32')
        else:
            value = value[0]

        self.store.put(name, value, "TRAN")

        self._mmf.seek(pos_current_line)

    def _break_path(self, name):
        """Return the variable name."""

        return name.split(":")[-1]

    def _move(self, byte):
        """Move file position to byte number."""

        self._mmf.seek(byte)


# EOF
