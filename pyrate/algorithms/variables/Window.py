""" The window algorithm determines a 'window' - a tuple containing a start and
    stop (start, stop) that other algorithms can use to work on. e.g. charge 
    region, moment regions etc.

    Required parameters:
        Fixed mode:
            window: x1, x2 - two numbers separated by commas indicating the
                             start and stop of the window
                    full - use the string 'full' or 'all' to set the window
                           tuple to (None, None) i.e. the full waveform         
        Dynamic mode:
            pivot: An object with a single sample or time (will be rounded to 
                   the nearest integer)
            left: How many samples before the pivot to start the window
            right: How many samples after the pivot to end the window

    Required states:
        initialise:
            output:
        execute:
            input: (optional) Pivot object
            output: (required only if no input provided)

    Example config:
    # With a fixed window
    Window_CHX:
        algorithm:
            name: Window
            window: 0, 50
        initialise:
            output:
        execute:
            output:
    
    # With a dynamic window, pivoting from a window

    PromptWindow_CHX:
        algorithm:
            name: Window
            left: 20
            right: 0
            window pivot: left
        initialise:
            output:
        execute:
            input: <Pivot object>
        pivot: <Pivot object (variable)>
"""


import sys
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.strings import get_items


class Window(Algorithm):
    __slots__ = ("mode", "fixed_window", "window_pivot")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        """Prepare for the calculation"""
        # Check we haven't been given a fixed window
        if "window" in self.config["algorithm"]:
            self.mode = "fixed_window"  # Set the mode to fixed window mode
            window = self.config["algorithm"]["window"]
            if window.lower() == "full" or window.lower() == "all":
                # Try to make into numbers
                # Want the full window, window object will be (None, None)
                self.fixed_window = (None, None)
            else:
                window = get_items(self.config["algorithm"]["window"])
                try:
                    self.fixed_window = [int(i) for i in window]
                except:
                    # Uh oh we couldn't find the window, but it was passed in...
                    sys.exit(
                        f"ERROR: in config, window passed in but values couldn't be parsed: {window}"
                    )

        elif "window pivot" in self.config["algorithm"]:

            self.mode = "window_pivot"
            # We want to use a window as a pivot, now we just need to find out which part
            self.window_pivot = self.config["algorithm"]["window pivot"]
            if self.window_pivot == "left" or self.window_pivot == "start":
                self.window_pivot = 0
            elif self.window_pivot == "right" or self.window_pivot == "stop":
                self.window_pivot = 1

            if "left" not in self.config["algorithm"]:
                sys.exit(f"ERROR: in config, window missing left parameter")
            if "right" not in self.config["algorithm"]:
                sys.exit(f"ERROR: in config, window missing right parameter")

        else:

            self.mode = "dynamic"  # Set the mode to use dynamic integer pivots
            # Better check the left and right parameters have been given
            if "left" not in self.config["algorithm"]:
                sys.exit(f"ERROR: in config, window missing left parameter")
            if "right" not in self.config["algorithm"]:
                sys.exit(f"ERROR: in config, window missing right parameter")

    def execute(self):

        """Calcualates the window if it's a variable, otherwise puts the window
        from the config on the store.
        """
        if self.mode == "fixed_window":
            window = self.fixed_window

        elif self.mode == "dynamic":
            # Ok, we're actually calculating it
            # Get the 'pivot' - e.g. the start of the pulse
            pivot = self.store.get(self.config["pivot"])

        elif self.mode == "window_pivot":
            # This time we'll define the pivot as the left or right of a passed in window
            pivot_window = self.store.get(self.config["pivot"])
            pivot = pivot_window[self.window_pivot]

        # Shared common pivot calculation for dynamic and window_pivot modes
        if self.mode == "dynamic" or self.mode == "window_pivot":
            # Check the pivot isn't invalid
            if pivot == -999 or pivot is None:
                window = -999
            else:
                # The window is defined by a left and right buffer on the start
                left = self.config["algorithm"]["left"]
                right = self.config["algorithm"]["right"]
                window = (int(round(pivot - left)), int(round(pivot + right)))
                if window[0] < 0:
                    # outside the range of the waveform, I've chosen to make
                    # it give a valid window even thought it failed, in case
                    # it is useful
                    window = (0, window[0])

        self.store.put(self.name, window)


# EOF
