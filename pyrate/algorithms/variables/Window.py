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
            left: Start of the window relative to the pivot
            right: End of the window relative to the pivot

            ** The window will be defined as (pivot + left, pivot + right)
            ** To keep the pivot inside the window range, use a negative value
            ** for 'left'
        
        Window pivot:
            ** Sub variant of dyanmic mode. Requires all of Dyanmic mode's parameters
            ** plus the following
            window pivot: left/start or right/end - The index of the passed in window to 
                            use as a pivot
            pivot: A window object / iterable object with a length of 2.


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
    
    # With a standard dynamic window
    DynWindow_CHX:
        algorithm:
            name: Window
            left: -20
            right: 100
        initialise:
            output:
        execute:
            input: <Pivot object (integer)>
        pivot: <Pivot object (integer)>

    # With a dynamic window, pivoting from a window

    PromptWindow_CHX:
        algorithm:
            name: Window
            left: -20
            right: 0
            window pivot: left
        initialise:
            output:
        execute:
            input: <Pivot object (window)>
        pivot: <Pivot object (window)>
"""


import sys
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.strings import get_items
from pyrate.utils.enums import Pyrate
from pyrate.utils.functions import iterable


class Window(Algorithm):
    __slots__ = ("mode", "fixed_window", "window_pivot")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        """Prepare for the calculation"""
        # Check the config contains the left and right parameters
        if "window" in self.config["algorithm"]:
            # Store the fixed window in a way that the rest of the alg can use
            self.config["algorithm"]["left"], self.config["algorithm"]["right"] = self.str_to_window(self.config["algorithm"]["window"])
        elif "left" not in self.config["algorithm"]:
                sys.exit(f"ERROR: in config, window object '{self.name}' missing 'left' parameter")
        elif "right" not in self.config["algorithm"]:
                sys.exit(f"ERROR: in config, window object '{self.name}' missing 'right' parameter")

        if "pivot" not in self.config:
            self.mode = "fixed_window"  # Set the mode to fixed window mode
            self.fixed_window = (self.config["algorithm"]["left"], self.config["algorithm"]["right"])
            return

        # Ok, we want to use a dynamic mode
        self.mode = "dynamic"  # Set the mode to use dynamic integer pivots
        if "window pivot" in self.config["algorithm"]:           
            self.mode = "window_pivot"
            # We want to use a window as a pivot, now we just need to find out which part
            self.window_pivot = self.config["algorithm"]["window pivot"]
            if self.window_pivot == "left" or self.window_pivot == "start":
                self.window_pivot = 0
            elif self.window_pivot == "right" or self.window_pivot == "stop":
                self.window_pivot = 1
            else:
                # Redundant, I may change this.
                self.window_pivot = 1 # Take the right most variable as default


    def execute(self):
        """Calcualates the window if it's a variable, otherwise puts the window
        from the config on the store.
        """
        if self.mode == "fixed_window":
            self.store.put(self.name, self.fixed_window)
            return

        # Check the pivot is valid
        pivot = self.store.get(self.config["pivot"])
        if pivot is Pyrate.NONE:
            self.store.put(self.name, Pyrate.NONE)
            return
        
        pivot_is_iterable = iterable(pivot)
        # Check the pivot variable matches the mode
        if self.mode == "window_pivot":
            if not pivot_is_iterable:
                sys.exit(f"ERROR: Window object '{self.name}' is expecting another"
                         f" window as a pivot, but the passed in pivot has type '{type(pivot)}'.")
            pivot = pivot[self.window_pivot] # Extract the pivot point from the window
        elif pivot_is_iterable:
            sys.exit(f"ERROR: Window objet '{self.name}' is expecting an integer,"
                     f" but the passed in object '{pivot}' is iterable.")

        left = self.config["algorithm"]["left"]
        right = self.config["algorithm"]["right"]
        # Window defined as the pivot + left to the pivot + right
        # Typical windows will have a negative left value
        # Windows can and will underflow on waveforms. The user must be aware of this
        window = (int(round(pivot + left)), int(round(pivot + right)))

        self.store.put(self.name, window)


    def str_to_window(self, string):
        """ Converts a window string to a tuple
        """

        if string.lower() == "full" or string.lower() == "all":
            # Try to make into numbers
            # Want the full window, window object will be (None, None)
            window = (None, None)
        else:
            window = get_items(string)
            try:
                window = [int(i) for i in window]
            except:
                # Uh oh we couldn't find the window, but it was passed in...
                sys.exit(
                    f"ERROR: in window object '{self.name}', window '{window}' couldn't be parsed."
                )
        return window

# EOF
