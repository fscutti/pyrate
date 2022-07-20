""" Creates and fills a ROOT TTree based on the config
https://root.cern.ch/doc/master/classTTree.html

    Required parameters:
        trees: Valid config of trees containing all the variables and their branch
                names sorted by the appropriate datatypes and fill-type
        
        Config requirememnts: TreeMaker uses a specialised config that maps out
            the shape and variables in the TTree, listed in the "trees"
            parameter. "trees" contains a list (using the yaml list 
            character '-'). Each tree must then separate its variables 
            (branches) into 'event' or 'single' fill-types, then 'vector' or
            'scalar' types, and finally the variable's data type. Objects can
            be listed as a comma separated string, and will be filled into
            the tree with the branch name the same as the object name.
                e.g. 
                Tree1:
                    event:
                        float: Baseline_CH0, Charge_CH0, Skew_CH0
                        vector<int>: RawWaveform_CH0
            
            TreeMaker also supports custom branch names - branch names distinct
            from the object name they point to and store. To do this, instead of
            and object name, the TreeMaker must be passed a branch name and an
            object name pairing as follows: Branch_name: Object_name. 
            To use this functionality, objects must be listed in the tree with 
            yaml's list syntax (-). It also supports direct use of in-line
            dictionaries as per yaml parsing.
            The following example shows a range of possible syntaxes. Note that 
            within the list, regular comma separated string passing is still 
            possible.
                e.g.
                Tree1:
                    event:
                        float: 
                            - Baseline: Baseline_CH0                # Single custom branch
                            - {Charge: Charge_CH0, Skew: Skew_CH0}  # Multiple custom branches 
                            - CFDTime_CH0, Timestamp_CH0,           # Older comma separated strings still compatible
                                LeadingEdge_CH0
                        vector<float>: CorrectedWaveform: CorrectedWaveform_CH0
      
    
    Required states:
        initialise:
            input:
        execute:
            input: <Execute objects to be stored>
        finalise:
            input: <Finalise objects>
    
    Example config:
    
    TreeObject:
        algorithm:
            name: TreeMaker
        initialise:
            input: RawWaveform_CH0, CorrectedWaveform_CH0, Baseline_CH0, Charge_CH0
                   Skew_CH0, CFDTime_CH0, Timestamp_CH0, LeadingEdge_CH0,
                   CorrectedWaveform_CH1, AverageWaveform_CH1
        execute:
            input: 
        finalise:
            input: AverageWaveform_CH0
        trees:
            - TreeName1:
                event:
                    vector<int>: RawWaveform_CH0
                    vector<float>: CorrectedWaveform_CH0
                    float: 
                        - Baseline: Baseline_CH0
                        - {Charge: Charge_CH0, Skew: Skew_CH0}
                        - CFDTime_CH0, Timestamp_CH0,
                            LeadingEdge_CH0

            - TreeName2:
                event:
                    vector<float>: CorrectedWaveform: CorrectedWaveform_CH1
                single:
                    vector<float>: AverageWaveform: AverageWaveform_CH0

"""

import os
import sys
import ROOT as R
from array import array
import ctypes

from pyrate.core.Algorithm import Algorithm

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN
from pyrate.utils import enums

GB = 1e9
MB = 1e6

def maxint(t, signed=False):
    """ Calculates the max integer value for ctype integers
        Takes in a ctypes.c_<type>() e.g. ctypes.c_int()
    """
    if signed:
        return 2**(8*ctypes.sizeof(t)-1)-1
    return 2**(8*ctypes.sizeof(t))-1

_Type = {
    "int": {"python": "i", "root": "I", "vector": "int", 
            "invalid":-999},
    "uint": {"python": "I", "root": "i", "vector": "unsigned int", 
             "invalid":maxint(ctypes.c_uint())},
    "short": {"python": "h", "root": "S", "vector": "short",
              "invalid":-999},
    "ushort": {"python": "H", "root": "s", "vector": "unsigned short",
               "invalid":maxint(ctypes.c_ushort())},
    "long": {"python": "l", "root": "L", "vector": "long",
             "invalid":-999},
    "ulong": {"python": "L", "root": "l", "vector": "unsigned long",
              "invalid":maxint(ctypes.c_ulong())},
    "float": {"python": "d", "root": "D", "vector": "double",  # Python arrays don't have float32's
              "invalid": -999.0},
    "double": {"python": "d", "root": "D", "vector": "double",
               "invalid": -999.0,},
    "bool": {"python": "H", "root": "O", "vector": "bool",
             "invalid":0},
    "string": {"python": "u", "root": "C", "vector": "string",  # Strings should be stored in vectors
               "invalid": ""}
}


class Branch:
    """Class to store branch information
        Name will be the name of the branch in the TTree
        var_name is an optional string to store the name of the variable on the
        store. If it exists, it will be used instead of 'name' to get the
        variable from the store.
    """

    def __init__(
        self, name, var_name=None, datatype=None, event_based=True, create_now=False
    ):
        self.name = name
        if not self.name.replace("_", "").isalnum():
            print(
                f"Warning: Branch name contains non-alphanumeric characters '{self.name}'"
            )

        # self.var_name will be name unless var_name passed in
        self.var_name = self.name if var_name is None else var_name

        if datatype == None:
            sys.exit(f"ERROR: in branch {self.name} - datatype not provided.")
        
        self._set_datatype(datatype) # set the datatype and vector type
        self.event_based = event_based
        self.created = False
        self.linked = False
        if create_now:
            self.create()

    # def create(self, data, type_override=None):
    def create(self):
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
            self.invalid_value = array(_Type[self.datatype]["python"])
        else:
            self.data = array(_Type[self.datatype]["python"], [0])
            # self.data = np.zeros(1, dtype=self.nptype)
            self.invalid_value = _Type[self.datatype]["invalid"]
        self.created = True

    def fill_branch(self, data):
        if not self.created:
            # Need to create all the branch machinery
            self.create(data)

        isiter = FN.iterable(data)
        if not isiter and self.vector == True:
            print(
                f"Error: input data is not iterable, but this branch ({self.name}) expects an array"
            )
            print(
                f"Input data type: {type(data)}, branch datatype: {self.datatype}"
            )
            sys.exit(1)
        if isiter and not self.vector:
            print(
                f"Error: input data is iterable, but this branch ({self.name}) expects a single element"
            )
            print(
                f"Input data type: {type(data)}, branch datatype: {self.datatype}"
            )
            sys.exit(1)
        assert isiter == self.vector
        if self.vector:
            # Clear just in case
            try:
                self.data[0]  # Test if we can access it
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
        """Clears the vector of a branch. Only works if vector=True"""
        if not self.vector:
            return
        self.data.clear()
    
    def _set_datatype(self, datatype):
        """ Parses the datatype, breaks up into type and 
            vector mode
        """
        if datatype.startswith("vector"):
            # extract the datatype
            if datatype[-1].isalnum():
                self.datatype = datatype[7:]
            else:
                self.datatype = datatype[7:-1]
            self.vector = True
        else:
            self.datatype = datatype
            self.vector = False



class Tree:
    """Class to store tree information
    Build your Tree structure first, then call create() to make the
    TTree structure accordingly
    """

    def __init__(
        self, name, outfile, path=None, branch_list=[], event=False, create_now=False
    ):
        self.name = name
        self.outfile = outfile
        self.path = path if path != None else self.name
        self.TTree = None
        self.created = False
        self.event = event  # Type of TTree, to be updated with each event loop or not
        self.branches = {}
        if branch_list:
            for branch in branch_list:
                self.add_branch(branch)
        if create_now:
            self.create()

    def add_branch(self, branch):
        """Adds branch to the tree storage"""
        if branch.name in self.branches:
            # Uh oh, branch already in branch list
            sys.exit(
                f"Error: A branch with the name '{branch.name}' already exists in this Tree ({self.name}).\n"
                "Please rename the new incoming branch (or don't add the same branch twice?)"
            )
        self.branches[branch.name] = branch
        if self.created:
            # TTree already created, so we better link this new branch
            if branch.linked:
                # uh oh, branch already linked to a TTree
                sys.exit(f"Error: branch ({branch.name}) already linked to a TTree")
            self.link_branch(branch)

    def create(self):
        """Actually makes the trees structure in the structure and adds all the
        branches into the tree. Typically called by the detector class
        """
        # Make sure we're linked to the correct file
        self.outfile.cd()
        self.TTree = R.TTree(self.name, self.name)
        # self.TTree.SetMaxTreeSize((int(1 * MB)))
        self.created = True

    def link_all_branches(self):
        """Links all the branches. Requires that the branches all be created
        properly
        """
        for branch_name in self.branches:
            branch = self.branches[branch_name]
            if not branch.linked:
                self.link_branch(branch)

    def link_branch(self, branch):
        """Links branch to the TTree. Requires TTree to be created"""
        if not self.TTree:
            self.create()
        if branch.linked:
            sys.exit("Error: Branch already linked")
        if not branch.created:
            sys.exit(
                f"Error initialising Tree - branch '{branch.name}' hasn't been created yet. Fill it with some data or create it manually."
            )
        if branch.vector:
            branch_instance = self.TTree.Branch(
                branch.name, self.branches[branch.name].data
            )
        else:
            branch_instance = self.TTree.Branch(
                branch.name,
                self.branches[branch.name].data,
                branch.name + "/" + _Type[branch.datatype]["root"],
            )
        branch_instance.SetFile(self.outfile)
        branch.linked = True

    def fill_branch(self, branch_name, data):
        """Runs the fill branch comamnd, filling branch_name with data"""
        if branch_name not in self.branches:
            sys.exit(f"Error filling branch: '{branch_name}' not in Tree '{self.name}'")
        if not self.branches[branch_name].created:
            # Need to create the branch
            self.branches[branch_name].create(data)
        # Now we can check if the branch has been linked
        if not self.branches[branch_name].linked:
            self.link_branch(self.branches[branch_name])
        self.branches[branch_name].fill_branch(data)

    def fill(self):
        """Runs the Fill function on the TTree
        Clears the branch variables
        """
        self.TTree.Fill()
        # Now it's been filled we better clear the vectors
        for branch in self.branches:
            # Only do it if necessary
            if self.branches[branch].vector:
                self.branches[branch].clear_vector()

    def remove_branch(self, branch):
        """Removes branch to the tree storage
        Does not remove the TBranch from the TTree as this isnt possible.
        Won't be accessed anymore (hopefully)
        """
        del self.branches[branch.name]
    
    def set_branches(self, branch_names, status=1):
        """ Sets the branch status of a list of branches
        """
        for branch_name in branch_names:
            self.TTree.SetBranchStatus(branch_name, status)
    
    def enable_branches(self, branch_names):
        """ Enables all the branches in the input list
        """
        self.set_branches(branch_names, status=1)
    
    def disable_branches(self, branch_names):
        """ Disables all the branches in the input list
        """
        self.set_branches(branch_names, status=0)


class TreeMaker(Algorithm):
    __slots__ = ('file', 'trees')

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
    
    @property
    def input(self):
        """Getter method for input objects."""
        return self._input

    @input.setter
    def input(self, config_input):
        """ Sets the input approrpriately for TreeMaker
        """
        if self._input == {}:
            for dependency in FN.expand_nested_values(config_input):
                variables = set(ST.get_items(str(dependency)))
                if not None in self._input:
                    self._input[None] = variables
                else:
                    self._input[None].update(variables)

    def initialise(self, condition=None):
        """Defines a tree dictionary."""
        out_file = self.store.get(f"OUTPUT:{self.name}")
        self.file = out_file

        trees = {}
        # Get all trees
        for tree in [t for t in self.config["input"]["trees"]]:
            for t_path_name, t_variables in tree.items():
                t_path = os.path.dirname(t_path_name)  # If using a path, otherise empty
                t_name = os.path.basename(t_path_name)
                # create the instance of the new tree
                trees[t_name] = Tree(
                    t_name, out_file, path=t_path, event=True, create_now=True
                )
                # Now set up all the variables in the tree

                # Loop through whether it's event-based on single
                for fill_type in t_variables:
                    # Determines if it will be event-based or filled once per run
                    if "event" in fill_type.lower():
                        event_based = True
                    elif "single" in fill_type.lower() or "run" in fill_type.lower():
                        event_based = False
                    # # Loop through vector and scalar type branches
                    # for vec_scalar in t_variables[fill_type]:
                    # loop over datatypes
                    for datatype, variables in t_variables[fill_type].items():
                        # New check to handle lists of vars
                        variables_list = self._parse_tree_vars(variables)
                        for b_name, var_name in variables_list:
                            # loop over individual variables
                            new_branch = Branch(
                                b_name,
                                var_name=var_name,
                                datatype=datatype,
                                event_based=event_based,
                                create_now=True,
                            )
                            # Add the new branch to the TTree
                            trees[t_name].add_branch(new_branch)

        # Disable the non-event based branches
        for tree in trees:
            branches_to_disable = [bn for bn in trees[tree].branches if not trees[tree].branches[bn].event_based]
            trees[tree].disable_branches(branches_to_disable)
        
        # Save the trees for later
        self.trees = trees

    def execute(self, condition=None):
        """Fills in the ROOT tree dictionary with event data."""
        # Fill all the branches in the trees if they're event-based
        for tree in self.trees:
            for branch_name in self.trees[tree].branches:
                # Only want to fill the branches that are event-based
                if self.trees[tree].branches[branch_name].event_based:
                    value = self.store.get(self.trees[tree].branches[branch_name].var_name)

                    # Handle invalid values using internal Pyrate.NONE
                    if value is enums.Pyrate.NONE:
                        # No valid value to store, storing the closest invalid value
                        value = self.trees[tree].branches[branch_name].invalid_value

                    # Fill the branch with the value
                    self.trees[tree].branches[branch_name].fill_branch(value)

            # Save all the values into the Tree
            self.trees[tree].fill()

    def finalise(self, condition=None):
        """Fill in the single/run-based variables"""
        # First, disable all the event-based branches
        # and enable the single entry branches
        for tree in self.trees:
            branches_to_disable = [bn for bn in self.trees[tree].branches if self.trees[tree].branches[bn].event_based]
            branches_to_enable =  [bn for bn in self.trees[tree].branches if not self.trees[tree].branches[bn].event_based]
            self.trees[tree].enable_branches(branches_to_enable)
            self.trees[tree].disable_branches(branches_to_disable)

        # Fill all the branches in the trees if they're run-based
        for tree in self.trees:
            for branch_name in self.trees[tree].branches:
                # Only want to fill the branches that are run-based
                if not self.trees[tree].branches[branch_name].event_based:
                    value = self.store.collect(self.trees[tree].branches[branch_name].var_name)
                    
                    # Handle invalid values using internal Pyrate.NONE
                    if value is enums.Pyrate.NONE:
                        # No valid value to store, storing the closest invalid value
                        value = self.trees[tree].branches[branch_name].invalid_value

                    # Fill the branch with the value
                    self.trees[tree].branches[branch_name].fill_branch(value)
            # Save all the values into the Tree
            self.trees[tree].fill()
            
            # Finally we have to re-enable all the branches so they can be accessed
            all_branches = [bn for bn in self.trees[tree].branches]
            self.trees[tree].enable_branches(all_branches)

        # Write the objects to the file - this is the most important step
        self.file.Write("", R.TObject.kOverwrite)

        # Store itself on the store with SKIP_WRITE code to show we have nothing
        # to return.
        self.store.save(self.name, enums.Pyrate.SKIP_WRITE)

    def _parse_tree_vars(self, variables):
        """ Dedicated function to just parse the tree lists/dicts/strings
        """
        if type(variables) == dict:
            # Just a single dictionary here
            variables = [variables]
        if type(variables) == list:
            # Dealing with a list
            retlist = []
            for entry in variables:
                if type(entry) == str:
                    var_names = list(filter(None, ST.get_items(entry)))
                    retlist += list(zip(var_names, var_names))
                elif type(entry) == dict:
                    retlist += list(entry.items())
                else:
                    retlist += [entry]
            return retlist
        else:
            # old style
            var_names = list(filter(None, ST.get_items(variables)))
            return list(zip(var_names, var_names))

# EOF
