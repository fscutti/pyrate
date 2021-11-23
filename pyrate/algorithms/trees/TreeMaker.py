""" Creates and fills a ROOT TTree.
https://root.cern.ch/doc/master/classTTree.html


myTreeObject:
       algorithm:
           name: TreeMaker
       trees:
         - my/folder/path/myTreeName:
               numbers:
                   int: myIntBranch1, myIntBranch2, ...
                   float: myFloatBranch1, myFloatBranch2, ...
               vectors:
                   int: myIntVectorBranch1, myIntVectorBranch2, ...
                   float: myFloatVectorBranch1, myFloatVectorBranch2, ...
         - my/folder/path/myOtherTreeName:
               etc ...
"""

#import psutil

import os
import sys
import ROOT as R
from array import array
from ctypes import c_longlong

from pyrate.core.Algorithm import Algorithm

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN
from pyrate.utils import enums

GB = 1e9
MB = 1e6

_Type = {
    "int": {"python": "i", "root": "I", "vector": "int"},
    "uint": {"python": "I", "root": "i", "vector": "unsigned int"},
    "short": {"python": "h", "root": "S", "vector": "short"},
    "ushort": {"python": "H", "root": "s", "vector": "unsigned short"},
    "long": {"python": "l", "root": "L", "vector": "long"},
    "ulong": {"python": "L", "root": "l", "vector": "unsigned long"},
    "float": {"python": "d", "root": "D", "vector": "double"}, # Python arrays don't have float32's
    "double": {"python": "d", "root": "D", "vector": "double"},
    "bool": {"python": "H", "root": "O", "vector": "bool"},
    "string": {"python": "u", "root": "C", "vector": "string"} # Strings should be stored in vectors
}

class Branch:
    """ Class to store branch information 
    """
    def __init__(self, name, datatype=None, vector=False, event_based=True, create_now=False):
        self.name = name
        if not self.name.replace("_", "").isalnum():
            print(f"Warning: Branch name contains non-alphanumeric characters '{self.name}'")
        
        if datatype == None:
            sys.exit(f"ERROR: in branch {self.name} - datatype not provided.")
        self.datatype = datatype
        self.vector = vector
        self.event_based = event_based
        self.initialised = False
        self.linked = False
        if create_now:
            self.initialise()

    # def initialise(self, data, type_override=None):
    def initialise(self):
        # Check if what's being passed in is iterable (stored in array)
        # self.vector = FN.iterable(data)
        # Automatic type getting - WIP
        # Try to get the correct datatype
        # if self.vector:
        #     self.datatype = python_to_root_type(data, vector_type=self.vector)
        # else:
        #     self.datatype, self.nptype = python_to_root_type(data)
        if self.vector:
            self.data = R.vector(_Type[self.datatype]["vector"])()
        else:
            self.data = array(_Type[self.datatype]["python"], [0])
            # self.data = np.zeros(1, dtype=self.nptype)
        self.initialised = True

    def fill_branch(self, data):
        if not self.initialised:
            # Need to create all the branch machinery
            self.initialise(data)

        isiter = FN.iterable(data)
        if not isiter and self.vector == True:
            print("Error: input data is not iterable, but this branch ({}) expects an array".format(self.name))
            print("Input data type: {}, branch datatype: {}, storage datatype: {}".format(type(data), self.datatype, type(self.data)))
            sys.exit(1)
        if isiter and not self.vector:
            print("Error: input data is iterable, but this branch ({}) expects a single element".format(self.name))
            print("Input data type: {}, branch datatype: {}, storage datatype: {}".format(type(data), self.datatype, self.data.dtype))
            sys.exit(1)
        assert(isiter==self.vector)
        if self.vector:
            # Clear just in case
            try:
                self.data[0] # Test if we can access it
                self.data.clear()
            except:
                pass
            # for val in data: self.data.push_back(val) # old method
            if self.datatype == "string":
                # Special case for strings, we store a string in a string vector, where the first element contains the full string
                self.data.push_back(data)
            else:
                self.data.assign(data)
        else:
            self.data[0] = data

    def clear_vector(self):
        """ Clears the vector of a branch. Only works if vector=True
        """
        if not self.vector:
            return
        self.data.clear()

class Tree:
    """ Class to store tree information
        Build your Tree structure first, then call initialise() to make the
        TTree structure accordingly
    """
    def __init__(self, name, outfile, path=None, branch_list=[], event=False, create_now=False):
        self.name = name
        self.outfile = outfile
        self.path = path if path!=None else self.name
        self.TTree =  None
        self.initialised = False
        self.event = event      # Type of TTree, to be updated with each event loop or not
        self.branches = {}
        if branch_list:
            for branch in branch_list:
                self.add_branch(branch)
        if create_now:
            self.initialise()

    def add_branch(self, branch):
        """ Adds branch to the tree storage
        """
        if branch in self.branches:
            # Uh oh, branch already in branch list 
            sys.exit(f"Error: branch ({branch.name}) already stored in branch list of this Tree.\nPlease remove it first (or don't add it twice?)")
        self.branches[branch.name] = branch
        if self.initialised:
            # TTree already created, so we better link this new branch
            if branch.linked:
                # uh oh, branch already linked to a TTree
                sys.exit(f"Error: branch ({branch.name}) already linked to a TTree")
            self.link_branch(branch)

    def initialise(self):
        """ Actually makes the trees structure in the structure and adds all the
            branches into the tree. Typically called by the detector class
        """
        
        self.TTree = R.TTree(self.name, self.name)
        # self.TTree.SetMaxTreeSize((int(1 * MB)))
        self.initialised = True
    
    def link_all_branches(self):
        """ Links all the branches. Requires that the branches all be initialised
            properly
        """
        for branch_name in self.branches:
            branch = self.branches[branch_name]
            if not branch.linked:
                self.link_branch(branch)
    
    def link_branch(self, branch):
        """ Links branch to the TTree. Requires TTree to be initialised
        """
        if not self.TTree:
            self.initialise()
        if branch.linked:
            sys.exit("Error: Branch already linked")
        if not branch.initialised:
            sys.exit(f"Error initialising Tree - branch '{branch.name}' hasn't been initialised yet. Fill it with some data or initialise it manually.")
        if branch.vector:
            branch_instance = self.TTree.Branch(branch.name, self.branches[branch.name].data)
        else:
            branch_instance = self.TTree.Branch(branch.name, self.branches[branch.name].data, branch.name + '/' + _Type[branch.datatype]["root"])
        branch_instance.SetFile(self.outfile)
        branch.linked = True
    
    def fill_branch(self, branch_name, data):
        """ Runs the fill branch comamnd, filling branch_name with data
        """
        if branch_name not in self.branches:
            sys.exit(f"Error filling branch: '{branch_name}' not in Tree '{self.name}'")
        if not self.branches[branch_name].initialised:
            # Need to initialise the branch
            self.branches[branch_name].initialise(data)
        # Now we can check if the branch has been linked
        if not self.branches[branch_name].linked:
            self.link_branch(self.branches[branch_name])
        self.branches[branch_name].fill_branch(data)
    
    def store(self):
        """ Runs the Fill function on the TTree
            Clears the branch variables
        """
        self.TTree.Fill()
        # Now it's been filled we better clear the vectors
        for branch in self.branches:
            # Only do it if necessary
            if self.branches[branch].vector:
                self.branches[branch].clear_vector()

    def remove_branch(self, branch):
        """ Removes branch to the tree storage
            Does not remove the TBranch from the TTree as this isnt possible.
            Won't be accessed anymore (hopefully)
        """
        del self.branches[branch.name]


class TreeMaker(Algorithm):
    # __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)
        self.tree_dict = None
        self.out_file = None

    def initialise(self, config):
        """Defines a tree dictionary."""
        # self.store.put(config["name"], "PYRATE:none")
        out_file = self.store.get(f"OUTPUT:{config['name']}", "PERM")
        self.store.put(f"{config['name']}:File", out_file)

        trees = {}
        # Get all trees
        for tree in [t for t in config["trees"]]:
            for t_path_name, t_variables in tree.items():
                t_path = os.path.dirname(t_path_name) # If using a path, otherise empty
                t_name = os.path.basename(t_path_name)
                # create the instance of the new tree
                trees[t_name] = Tree(t_name, out_file, path=t_path, event=True, create_now=True)
                # Now set up all the variables in the tree

                # Loop through whether it's event-based on single
                for fill_type in t_variables:
                    # Determines if it will be event-based or filled once per run
                    if "event" in fill_type.lower():
                        event_based = True
                    elif "single" in fill_type.lower() or "run" in fill_type.lower():
                        event_based = False
                    # Loop through vector and scalar type branches
                    for vec_scalar in t_variables[fill_type]:
                        # loop over datatypes
                        for datatype, vars in t_variables[fill_type][vec_scalar].items():
                            for var in ST.get_items(vars):
                                # loop over individual variables
                                if "vector" in vec_scalar:
                                    # Storing vectors
                                    new_branch = Branch(var, datatype=datatype, vector=True, event_based=event_based, create_now=True)
                                if "scalar" in vec_scalar or "number" in vec_scalar:
                                    # Storing scalars
                                    new_branch = Branch(var, datatype=datatype, vector=False, event_based=event_based, create_now=True)
                                # Add the new branch to the TTree
                                trees[t_name].add_branch(new_branch)

        self.store.put(f"{config['name']}:trees", trees, "PERM")

    def execute(self, config):
        """Fills in the ROOT tree dictionary with event data.
        """
        trees = self.store.get(f"{config['name']}:trees", "PERM")

        # Fill all the branches in the trees if they're event-based
        for tree in trees:
            for branch_name in trees[tree].branches:
                # Only want to fill the branches that are event-based
                if trees[tree].branches[branch_name].event_based:
                    value = self.store.get(branch_name, "TRAN")
                    trees[tree].branches[branch_name].fill_branch(value)

            # Save all the values into the Tree
            trees[tree].store()
    
    def finalise(self, config):
        """ Fill in the single/run-based variables
        """
        trees = self.store.get(f"{config['name']}:trees", "PERM")
        # Fill all the branches in the trees if they're run-based
        for tree in trees:
            for branch_name in trees[tree].branches:
                # Only want to fill the branches that are run-based
                if not trees[tree].branches[branch_name].event_based:
                    value = self.store.get(branch_name, "PERM")
                    trees[tree].branches[branch_name].fill_branch(value)
            # Save all the values into the Tree
            trees[tree].store()

        # Write the objects to the file - this is the most important step
        self.store.get(f"{config['name']}:File").Write("", R.TObject.kOverwrite)

        # Store itself on the store with SKIP_WRITE code to show we have nothing 
        # to return.
        self.store.put(config["name"], enums.Pyrate.SKIP_WRITE)

# EOF
