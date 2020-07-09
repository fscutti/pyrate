""" This class is the core of the execution """


class Run:
    def __init__(self,name,finput,foutput,algs):
        self.name    = name
        self.finput  = finput
        self.foutput = foutput
        self.algs    = algs
    
    def initialise(self):
        pass

    def execute(self):
        pass

    def finalise(self):
        pass

    def launch(self):
        print(self.name)
