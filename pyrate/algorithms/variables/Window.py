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
            right: How many samples after the pivot to start the window

    Required states:
        initialise:
            output:
        execute:
            input: (optional) Pivot object
            output: SELF

    Example config:
    # With a fixed window
    Window_CHX:
        algorithm:
            name: Window
            window: 0, 50
        initialise:
            output:
        execute:
            output: SELF
    
    # With a dynamic window
    PromptWindow_CHX:
        algorithm:
            name: Window
            left: 20
            right: 0
        initialise:
            output:
        execute:
            input: <Pivot object>
            output: SELF
        pivot: <Pivot object (variable)>
"""

import sys
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.strings import get_items

class Window(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)
    
    def initialise(self, config):
        """ Prepare for the calculation
        """
        # Check we haven't been given a fixed window
        if "window" in config["algorithm"]:
            window = get_items(config["algorithm"]["window"])
            # Try to make into numbers
            if window.lower() == "full" or window.lower() == "all":
                # Want the full window, window object will be (None, None)
                window = (None, None)
            else:
                try:
                    window = [int(i) for i in window]
                except:
                    # Uh oh we couldn't find the window, but it was passed in...
                    sys.exit(f"ERROR: in config, window passed in but values couldn't be parsed: {window}")
            self.store.put(f"{config['name']}:window", window)
        else:
            # Better check the left and right parameters have been given
            if "left" not in config["algorithm"]:
                sys.exit(f"ERROR: in config, window missing left parameter")
            if "right" not in config["algorithm"]:
                sys.exit(f"ERROR: in config, window missing right parameter")

    def execute(self, config):
        """ Calcualates the window if it's a variable, otherwise puts the window
            from the config on the store.
        """
        if self.store.check(f"{config['name']}:window"):
            window = self.store.get(f"{config['name']}:window")

        else:
            # Ok, we're actually calculating it
            # Get the 'pivot' - e.g. the start of the pulse
            pivot = self.store.get(config["pivot"])
            # Check the pivot isn't invalid
            if pivot == -999 or pivot is None:
                window = -999
            else:
                # The window is defined by a left and right buffer on the start
                left = config["algorithm"]["left"]
                right = config["algorithm"]["right"]
                window = (int(round(pivot - left)), int(round(pivot + right)))
        
        self.store.put(config["name"], window)

# EOF