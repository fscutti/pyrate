"""Utility classes."""

import ROOT as R
import numpy as np

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
