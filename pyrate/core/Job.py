""" This class will handle a set of configurations 
and launch several instances of a Run homogeneous
in purpose and structure."""

from pyrate.core.Run import Run

class Job:
    def __init__(self, config):
        self.config = config
        self.runs   = []


    def setup(self):
        pass



    def load(self):
        run = Run(name = "TEST")

    def launch(self):
        #for k,v in self.config.items():
        #    print(k,v)
        self.load() 


