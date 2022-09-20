""" Reader of a ROOT file
"""
import os
import sys
import glob

import ROOT
from pyrate.core.Input import Input

class Tree:
    """ Class to store the TTree information - not really needed but helped in
        making the first version of this reader
    """

    def __init__(self, name):
        """ Sets up the Tree
        """
        self.name = name
        self.attached = False
        self.TTree = None
        self.branches = []
    
    def setup_tree(self, f):
        """ Sets up the tree for the first time
            Takes in the file the tree lives in
        """
        self.TTree = f.Get(self.name)
        self.branches = [i.GetName() for i in self.TTree.GetListOfBranches()]
        self.attached = True


class ReaderROOT(Input):
    __slots__ = ["_files", "_f", "_files_index", "_sizes", "size", "_idx",
                 "_trees", "_tree_variables", "_obj_variables", "_nevents",
                 "_timestamp", "_events_read", "_n_total_events", "_output_format"]

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

        self._files_index = -1
        self._sizes = [os.path.getsize(f) for f in self._files]
        self.size = sum(self._sizes)
        # Set the progress to 0, unless the files are empty
        self._progress = 0 if self.size !=0 else 1
        self._events_read = 0
        # Load the first file
        self._load_next_file()

        # Set the output for the Run
        # --------------------------
        output = {}
        output.update(self._tree_variables)
        output.update(self._obj_variables)
        self.output = {k:k for k in output}

        # Get the number of entries
        # -------------------------
        self._set_nevents()
        self._n_total_events = sum(self._nevents)

        # Initialise the trees
        self._set_next_event()

    def _load_next_file(self):
        if self.is_loaded:
            self.offload()
        self._files_index += 1

        # Check if there are more files
        if self._files_index >= len(self._files):
            return

        # Load the next file
        self._f = ROOT.TFile.Open(self._files[self._files_index])

        if not self._f: return
        self.is_loaded = True
        self._idx = 0

        # Pull out the trees - this is a reader so it has to be able to pull
        # trees for the event loop to work
        # ----------------------------------------------------------------------
        self._trees = {}
        obj_setup = {}
        
        if "objects" in self.config: object_list = self.config["trees"] + self.config["objects"]
        else: object_list = self.config["trees"]
        
        for name in object_list:
            if type(name) == str:                
                # store_name = output_format.format(name=self.name, variable=name)
                # Just passed in the path - this will be the store name and
                # var name
                obj_setup[name] = name
            if type(name) == dict:
                # Passed in the name on the store and the variable name
                obj_setup.update(name)
                # for var in name:
                #     store_name = output_format.format(name=self.name, variable=var)
                #     obj_setup[store_name] = name[var]

        # Now we must build up our trees
        self._tree_variables = {}
        self._obj_variables = {}
        for variable_name, path in obj_setup.items():
            success = self.load_variables(path, variable_name)
            if not success:
                # Failed to load variable/path
                sys.exit(f"ERROR: in ReaderROOT {self.name}, {variable_name} could not be found under {path} in file {self._f}")

        # Lastly, if the timestamp has been passed in
        if "timestamp" in self.config:
            timestamp_var = self.config["timestamp"]
            if timestamp_var not in self._tree_variables:
                success = self.load_variables(timestamp_var, timestamp_var)
            if not success:
                # Uh oh
                sys.exit(f"ERROR: in ReaderROOT {self.name}, timetamp variable set to {timestamp_var} but it couldn't be found in any of the trees.")

    def load_variables(self, variable_path, variable_name):
        """ Prepeares a variable for the reader
            If it is a single branch, the setup_tree method is called, and the
            variable/branch name is noted. If it is a TTree, setup_tree is also
            called but all its branches are noted.
        """
        split_path = variable_path.split('/')
        # Build up an ever growing list of the path to search
        # only want the last two of the list
        built_up_path = ["/".join(split_path[:i]) for i in range(1, len(split_path)+1)][-2:]
        for deeper_path in built_up_path:
            obj = self._f.Get(deeper_path)
            if isinstance(obj, ROOT.TTree):
                # Ok we found the TTree, time to create it
                self.create_tree(deeper_path)
                # Now we check what variables we want to use
                if deeper_path != variable_path:
                    # Ok, we want to add just a single variable
                    store_name = self._output_format.format(name=self.name, variable=variable_name)
                    self._tree_variables[store_name] = {"branch":split_path[-1], "tree": split_path[-2]}
                else:
                    for b in self._trees[deeper_path].branches:
                        store_name = self._output_format.format(name=self.name, variable=f"{variable_name}_{b}")
                        self._tree_variables[store_name] = {"branch":b, "tree":split_path[-1]}
                return True

        obj = self._f.Get(variable_path)
        # If this is a directory add all its children
        if isinstance(obj, ROOT.TDirectory):
            # Let's add everything from the directory
            dir_objs = [i.GetName() for i in obj.GetListOfKeys()]
            self._obj_variables.update({self._output_format.format(name=self.name, variable=k):k for k in dir_objs})
            return True
        # Just check the object itself
        if obj:
            store_name = self._output_format.format(name=self.name, variable=variable_name)
            self._obj_variables[store_name] = variable_path
            return True

        # We never found anything
        return False

    def create_tree(self, tree_name):
        """ Creates a Tree if it doesn't already exist.
        """
        if tree_name not in self._trees:
            # Let's make the tree
            self._trees[tree_name] = Tree(tree_name)
            self._trees[tree_name].setup_tree(self._f)
    
    def _set_nevents(self):
        """ Sets the number of events
        """
        for f in self._files:
            self._nevents = []
            nevents = 0
            for tree in self._trees:
                n = self._trees[tree].TTree.GetEntries()
                if n > nevents:
                    nevents = n
                    self._hasEvent = True
            self._nevents.append(nevents)

    def offload(self):
        self.is_loaded = False
        self._f.Close()
    
    def initialise(self, condition=None):
        for store_name, obj_path in self._obj_variables.items():
            obj = self._f.Get(obj_path)
            self.store.save(store_name, obj)

    def finalise(self, condition=None):
        self.offload()
    
    def get_event(self, skip=False):
        """ Gets the latest event information
        """
        self._set_next_event()
        if not self._hasEvent:
            # Try loading the next file
            next_file = self._load_next_file()
            if not next_file: return False
            self._set_next_event()

        for store_name, variable in self._tree_variables.items():
            tree = self._trees[variable["tree"]]
            branch_name = variable["branch"]
            # The actual variables the govern the run
            tree.TTree.GetBranch(branch_name).GetEntry(self._idx)
            # Get the variable and put it on the store
            self.store.put(store_name, getattr(tree.TTree, branch_name))

        self._idx += 1
        self._events_read += 1
        self._progress = self._events_read / self._n_total_events
        return True

    def _set_next_event(self):
        """ Loads the trees and gets the timestamp
        """
        # Load all the trees to the latest event
        for tree_name in self._trees:
            tree = self._trees[tree_name]
            tree.TTree.LoadTree(self._idx)
        
        if "timestamp" in self.config:
            timestamp_var = self._tree_variables[self.config["timestamp"]]
            branch_name = timestamp_var["branch"]
            tree = self._trees[timestamp_var["tree"]]
            tree.TTree.GetBranch(branch_name).GetEntry(self._idx)
            self._timestamp = getattr(tree.TTree, branch_name)
        else:
            self._timestamp = self._idx
        
        self._hasEvent = bool(self._idx <= self._nevents[self._files_index])
    
    @property
    def timestamp(self):
        """ Returns the current event timestamp
        """
        return self._timestamp

# EOF
