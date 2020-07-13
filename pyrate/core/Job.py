""" This class will handle a set of configurations 
and launch several instances of a Run homogeneous
in purpose and structure.
"""
import os
from utils import strings as s
from pyrate.core.Run import Run

class Job:
    def __init__(self, config):
        self.config = config

    def setup(self):
        """ Initialise 'private' data members.
        """
         
        # list of run files {name:[files]}
        input_file_list = self.get_file_list()          
        self.runs = {r:[f for f in input_file_list if r in f.split("/")[-1]] for r in self.get_run_names(input_file_list)}


        # list of outputs
        # list of algorithms
        # 


    def get_file_list(self):
        """ Get list of input files.
        """
        input_file_list = []
        for path in self.config["input"]["path"]:
            input_file_list.extend(os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
        return input_file_list


    def get_run_names(self, input_file_list):
        """ The run name is everything but the name of the file.
        """
        input_run_names = []
        for f in input_file_list:
            for group in self.config["input"]["files"]:
                input_run_names.extend(s.remove_tag_from_name(f,t) for t in s.get_items(group) if t in f)
        
        return s.remove_duplicates(input_run_names)



    def load(self):
        #run = Run(name = "TEST")
        pass

    def launch(self):
        #for k,v in self.config.items():
        #    print(k,v)
        #self.load() 
        self.setup() 


