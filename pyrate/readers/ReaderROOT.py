""" Reader of a ROOT file
"""

import os
import sys
import sys
import glob
import numpy as np

from pyrate.core.Input import Input
from pyrate.utils.functions import iterable


class ReaderROOT(Input):
    __slots__ = ["_files", "_f", "_files_index", "_sizes", "size", "_idx",
                 "_tree", "_variables", "_obj_variables", "_nevents",
                 "_events_read", "_total_nevents", "_output_format"]

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
        
        # Set the output format
        self._output_format = "{name}_{variable}" # Default formatting
        if "output" in self.config:
            # The user has provided a custom output formatting
            self._output_format = self.config["output"]

        # Prepare all the files
        # ---------------------
        self.is_loaded = False
        self._files = []
        for f in self.config["files"]:
            f = os.path.expandvars(f)
            self._files += sorted(glob.glob(f))
        if len(self._files) == 0:
            sys.exit(f"ERROR: in reader {self.name}, no files were found.")

        self._files_index = 0
        self._sizes = [os.path.getsize(f) for f in self._files]
        self.size = sum(self._sizes)
        # Set the progress to 0, unless the files are empty
        self._progress = 0 if self.size !=0 else 1
        self._events_read = 0
        self._total_nevents = self._get_total_events()
        # Load the first file
        self._load_next_file()

        # Set the output for the Run
        # --------------------------
        output = {}
        output.update(self._variables)
        output.update(self._obj_variables)
        self.output = output.keys()

    def _load_next_file(self):
        if self.is_loaded:
            self.offload()

        # Check if there are more files
        if self._files_index >= len(self._files):
            return

        # Load the next file
        # Always avoid the top-level 'import ROOT'.
        import ROOT
        self._f = ROOT.TFile.Open(self._files[self._files_index])

        if not self._f: return
        self.is_loaded = True
        self._idx = 0

        # Load the TTree - this is a reader so it has to have a
        # tree for the event loop to work
        self._tree = self._f.Get(self.config["tree"])
        if not self._tree:
            sys.exit(f"ERROR: in ReaderROOT {self.name}, tree {self.config['tree']} could not be found in file {self._f}")

        # Pull out the tree variables
        # ----------------------------------------------------------------------
        branches = [i.GetName() for i in self._tree.GetListOfBranches()]
        self._variables = {}
        if "variables" in self.config:
            self._variables = self._parse_config_list(self.config["variables"])
            for _, branch in self._variables.items():
                if branch not in branches:
                    sys.exit(f"ERROR: in ReaderROOT {self.name}, {branch} could not be found in tree {self.config['tree']}")
        else:
            # We want all the variables from the tree
            for branch in branches:
                store_name = self._output_format.format(name=self.name, variable=branch)
                self._variables[store_name] = branch

        # If the timestamp has been passed in, get it and use it
        if "timestamp" in self.config:
            timestamp_var = self.config["timestamp"]
            store_name = self._output_format.format(name=self.name, variable=timestamp_var)
            if timestamp_var not in self._variables and store_name not in self._variables:
                if timestamp_var not in branches:
                    sys.exit(f"ERROR: in ReaderROOT {self.name}, timetamp variable set to {timestamp_var} but it wasn't found in the tree {self.config['tree']}.")
                # ok, we put the timestamp var in the variables list
                self._variables[store_name] = timestamp_var
            self.config["timestamp"] = store_name # How we'll access it from now on
        
        # Finally, let's load up the other objects if theyre there
        self._obj_variables = {}
        if "objects" in self.config:
            obj_vars = self._parse_config_list(self.config["objects"])
            for obj_store_name, path in obj_vars.items():
                obj = self._f.Get(path)
                if isinstance(obj, ROOT.TDirectory):
                    # Let's add everything from the directory
                    dir_objs = [i.GetName() for i in obj.GetListOfKeys()]
                    self._obj_variables.update({self._output_format.format(name=self.name, variable=k):k for k in dir_objs})
                elif not obj:
                    sys.exit(f"ERROR: in ReaderROOT {self.name}, can't find {path} in file {self._files[self._files_index]}.")
                else:
                    self._obj_variables[obj_store_name] = path
        
        # Initialise the trees
        self._nevents = self._tree.GetEntriesFast()
        self.read_next_event()
        self._files_index += 1

    def _parse_config_list(self, config):
        """ Helper to parse a part of the config. Generates the store name too
        """
        var_dict = {}
        for variable in config:
            if type(variable) == str:                
                # Just passed in the path - this will be the store name and
                # var name
                store_name = self._output_format.format(name=self.name, variable=variable)
                var_dict[store_name] = variable
            elif type(variable) == dict:
                # Passed in the name on the store and the variable name
                for var_name, path in variable.items():
                    store_name = self._output_format.format(name=self.name, variable=var_name)
                    var_dict[store_name] = path
        return var_dict
    
    def _get_total_events(self):
        """ Gets the entries for each of the files
        """
        # Always avoid the top-level 'import ROOT'.
        import ROOT
        nevents_list = []
        for file_name in self._files:
            try:
                f = ROOT.TFile(file_name)
            except OSError:
                sys.exit(f"ERROR: in ReaderROOT {self.name}, file {file_name} couldn't be opened.\n"
                          "Please ensure the path and name is correct, and the file is of the correct type.")
            tree = f.Get(self.config["tree"])
            if not tree:
                sys.exit(f"ERROR: in ReaderROOT {self.name}, tree {self.config['tree']} could not be found in file {file_name}")
            nevents_list.append(tree.GetEntriesFast())
            f.Close()
        return sum(nevents_list)

    def offload(self):
        if self.is_loaded:
            self.is_loaded = False
            self._f.Close()
    
    def initialise(self, condition=None):
        """ Pull out the objects if needed
        """
        for store_name, obj_path in self._obj_variables.items():
            obj = self._f.Get(obj_path)
            self.store.save(store_name, obj)        

    def finalise(self, condition=None):
        self.offload()

    def read_next_event(self):
        """ Loads the trees and gets the timestamp
        """
        self._hasEvent = False
        if self._idx > self._nevents:
            return False

        # Load all the tree to the latest event
        self._tree.LoadTree(self._idx)
        if "timestamp" in self.config:
            branch_name = self._variables[self.config["timestamp"]]
            self._tree.GetBranch(branch_name).GetEntry(self._idx)
            self._eventID = getattr(self._tree, branch_name)
        else:
            self._eventID = self._idx
        self._hasEvent = True

        self._events_read += 1
        self._progress = self._events_read / self._total_nevents
        self._idx += 1
        return True
    
    def get_event(self, skip=False):
        """ Gets the latest event information
        """
        if not self._hasEvent:
            return False

        for store_name, branch_name in self._variables.items():
            # The actual variables the govern the run
            self._tree.GetBranch(branch_name).GetEntry(self._idx) # Get the right entry
            # Get the variable and put it on the store
            value = getattr(self._tree, branch_name)
            if iterable(value):
                # I cannot believe this is so much faster but it is 
                # For future reference, libROOTPythonizations is super slow
                # I suspect there's an issue with the __array_interface,
                # particularly the GetSizeOfType() helper method. 
                value = np.array(list(value), copy=False) # copy=False? might cause seg fault?
                # Annoying conversion but necessary for now
                if value.dtype == np.int64:
                    value = value.astype(np.int32)
                if not value.size:
                    continue
            self.store.put(store_name, value)

        if not self.read_next_event():
            self._load_next_file()

        return True

    def skip_events(self, n):
        """ Doesn't do anything except increment the index
        """
        self._idx += n

# EOF
