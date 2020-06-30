""" This class will handle a set of configurations 
and launch several instances of a Run homogeneous
in purpose and structure."""


class Job:
    def __init__(self, config):
        self.config = config

    def launch(self):
        print("Hello World")
