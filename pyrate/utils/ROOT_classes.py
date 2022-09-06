"""Utility classes."""

import ROOT as R
import numpy as np
import ctypes

def maxint(t, signed=False):
    """Calculates the max integer value for ctype integers
    Takes in a ctypes.c_<type>() e.g. ctypes.c_int()
    """
    if signed:
        return 2 ** (8 * ctypes.sizeof(t) - 1) - 1
    return 2 ** (8 * ctypes.sizeof(t)) - 1

_Type = {
    "int": {"python": "i", "root": "I", "vector": "int", "invalid": -999},
    "uint": {
        "python": "I",
        "root": "i",
        "vector": "unsigned int",
        "invalid": maxint(ctypes.c_uint()),
    },
    "short": {"python": "h", "root": "S", "vector": "short", "invalid": -999},
    "ushort": {
        "python": "H",
        "root": "s",
        "vector": "unsigned short",
        "invalid": maxint(ctypes.c_ushort()),
    },
    "long": {"python": "l", "root": "L", "vector": "long", "invalid": -999},
    "ulong": {
        "python": "L",
        "root": "l",
        "vector": "unsigned long",
        "invalid": maxint(ctypes.c_ulong()),
    },
    "float": {
        "python": "d",
        "root": "D",
        "vector": "double",  # Python arrays don't have float32's
        "invalid": float("nan"),
    },
    "double": {
        "python": "d",
        "root": "D",
        "vector": "double",
        "invalid": float("nan"),
    },
    "bool": {"python": "H", "root": "O", "vector": "bool", "invalid": 0},
    "string": {
        "python": "u",
        "root": "C",
        "vector": "string",  # Strings should be stored in vectors
        "invalid": "",
    },
}

class Color(int):
    """Create a new R.TColor object with an associated index.
    https://root-forum.cern.ch/t/how-to-form-a-color-t-from-a-tcolor/25013/2.
    """

    def __new__(cls, r, g, b, name=""):
        self = int.__new__(cls, R.TColor.GetFreeColorIndex())
        self.object = R.TColor(self, r, g, b, name, 1.0)
        self.name = name
        return self


class ColorFinder:
    """Handles color matching with ROOT ones starting from an arbitrary pixel."""

    def __init__(self, r, g, b):
        self.my_color = np.array((r, g, b))
        self._c = R.TColor()

    def match(self):
        """Find closest color within ROOT color wheel."""
        self._init_wheel()

        tmp_dist = 0.0
        match_color = None

        for root_color in self._wheel:
            dist = np.linalg.norm(root_color - self.my_color)

            if tmp_dist > dist or not type(match_color).__module__ == np.__name__:
                match_color = root_color
                tmp_dist = dist

        return self._c.GetColor(match_color[0], match_color[1], match_color[2])

    def _init_wheel(self):
        """Initialise ROOT color wheel."""

        self._wheel = []

        colors = {
            (-10, 15): [R.kRed, R.kBlue, R.kGreen, R.kMagenta, R.kCyan, R.kYellow],
            (-9, 20): [R.kPink, R.kAzure, R.kSpring, R.kOrange, R.kViolet, R.kTeal],
            (0, 1): [R.kBlack, R.kWhite],
            (0, 4): [R.kGray],
        }

        for (shift, window), color_list in colors.items():
            for c in color_list:

                self._wheel.extend(
                    [
                        np.array(
                            (
                                R.gROOT.GetColor(c + i + shift).GetRed(),
                                R.gROOT.GetColor(c + i + shift).GetGreen(),
                                R.gROOT.GetColor(c + i + shift).GetBlue(),
                            )
                        )
                        for i in range(window)
                    ]
                )


# EOF
