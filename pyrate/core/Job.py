""" This class will handle a set of configurations and launch several 
instances of a Run homogeneous in purpose and structure.
"""

import os
import re
import sys
import yaml
import json
import logging

from itertools import groupby, product
from functools import reduce
from operator import mul
from copy import deepcopy
import pprint

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN
from pyrate.utils.ROOT_classes import _Type

from pyrate.core.Run import Run


class Job:
    def __init__(self, name, config, log_level):
        self.name = name
        self.config = config
        self.log_level = log_level
        self.runs = []

    def setup(self):
        """Instantiate Run objects."""
        for run_name, run_config in self.config["runs"].items():
            self.runs.append(Run(run_name, run_config))

    def launch(self):
        """Launch Run objects. """
        for r in self.runs:
            r.setup()
            r.launch()

    def print_objects(self):
        """Prints out all objects"""
        pp = pprint.PrettyPrinter()
        pp.pprint(self.job["configs"]["global"]["objects"])


def expand_tags(configs):
    """Searches all configs, finds all valid <tags> and replaces and expands
    based on the following tag rules

    <tag> = [x1, x2, x3, ...]

    For an object to be duplicated it must contain at least one <tag> type tag
    in the object name

    --- Single object name tags ---
    Single <tag> in the object name will create len(<tag>) objects, where
    each instance of the <tag> key will be replaced with a single element
    in the <tag> list. All instances of the <tag> key will be replaced, in both
    the object name, and the object config

    E.g.
    MyObj_<tag>:
        key1: Variable_<tag>

    Will create n objects like the following
    MyObj_x1:
        key1: Varialbe_x1
    ...
    MyObj_xn:
        key1: Varialbe_xn

    Other tags can be used in the object config itsefl, so long as they are
    at least as long as <tag>. They will be iterated over in parallel

    MyObj_<tag>:
        key1: Variable_<tag>
        key1: Varialbe_<tag2>

    --- Multiple object name tags ---
    With mulitple tags <a>, <b> in the object name, len(<a>) * len(<b>) objects
    will be created, where the <a> and <b> tags follow a generic outer product
    of all combinations of the pairings.

    <tag1>: [1,2]
    <tag2>: [3,4]

    MyObj_<tag1><tag2>:
        key1: Variable_<tag1>
        key2: Variable_<tag2>

    will generate 4 objects like the where the tags are equal to:
    [ (1,3), (1, 4), (2, 3), (2, 4) ]

    MyObj_13:
        key1: Variable_1
        key2: Variable_3
    ...
    MyObj_24:
        key1: Variable_2
        key2: Variable_4

    Lastly, other tags can be used in parallel with the product tags. These
    tags can be added with the following syntax <<tag>>, and will be ignored
    when generating the product. Their index will follow the first listed
    tag in the product, i.e. they will follow the index of <tag1> in the
    example. <tag3> must be at least as long as <tag1>

    <tag3>: [8, 9]

    MyObj_<tag1><tag2><<tag3>>:
        key1: Variable_<tag1>
        key2: Variable_<tag2>
        key3: Variable_<<tag3>>

    becomes

    MyObj_138:
        key1: Variable_1
        key2: Variable_3
        key3: Variable_8

    MyObj_148:
        key1: Variable_1
        key2: Variable_4
        key3: Variable_8

    MyObj_239:
        key1: Variable_2
        key2: Variable_3
        key3: Variable_9

    MyObj_249:
        key1: Variable_2
        key2: Variable_4
        key3: Variable_9

    """
    configs = deepcopy(configs)
    # Search all the configs and find all the valid tags
    tags = {}
    forbidden_tags = [f"{t}" for t in _Type]
    for config in configs:
        if config == "global":
            # Want to ignore the global configs
            continue
        for t in configs[config]:
            if find_all_tags(t):
                # found a tag:
                stripped_t = strip_tag(t)
                if stripped_t in forbidden_tags:
                    sys.exit(f"ERROR: tag {t} is a forbidden tag.")
                tags[stripped_t] = configs[config][t]

    # First we should deal with any $tag$ in the config
    config_str = json.dumps(configs["global"]["objects"])
    for tag in tags:
        config_str = ST.replace_clean(config_str, f"${tag}$", tags[tag])
    configs["global"]["objects"] = json.loads(config_str)

    # Deal with object duplication
    # Loop through all objects and find any that need duplicating
    # They must have a tag in their name, as object names must be unique.
    objects_to_dup = {}
    for obj_name, obj in configs["global"]["objects"].items():
        obj_name_tags = strip_all_tags(find_all_tags(obj_name))
        for tag in tags:
            if tag in obj_name_tags:
                objects_to_dup[obj_name] = obj
    # clear out the found objects
    for obj_name in objects_to_dup:
        del configs["global"]["objects"][obj_name]

    # Duplicate the object
    # should only be left with the <tag> types
    for obj_name, obj in objects_to_dup.items():
        # First find all the relevant tags
        obj_str = json.dumps(obj)
        obj_name_tags = [t for t in find_all_tags(obj_name) if strip_tag(t) in tags]
        stripped_obj_name_tags = strip_all_tags(obj_name_tags)
        # The name *must* be updated, if there is no tag in the name we exit
        if not obj_name_tags:
            sys.exit(
                f"No valid tag found in object {obj_name}. Must contain a <tag> style tag."
            )

        obj_tags = [t for t in find_all_tags(obj_str) if strip_tag(t) in tags]
        stripped_obj_tags = strip_all_tags(obj_tags)

        # Separate out the parallel tags in the object and name
        # parallel tags can contain << >>
        parallel_tags = {}
        for tag in obj_name_tags + obj_tags:
            if "<<" in tag or ">>" in tag:
                parallel_tags[tag] = []
        # parallel tags are also any obj_tag not in the obj_name_tags
        parallel_tags.update({t: [] for t in obj_tags if t not in obj_name_tags})

        # Finally, let's separate our parallel_tags from our non-parallel tags
        product_tags = [t for t in obj_name_tags if t not in parallel_tags]
        stripped_product_tags = strip_all_tags(product_tags)
        # Ok, we have all the tags, build the product values and the following
        # parallel tag values
        product_tag_values = product(*[tags[t] for t in stripped_product_tags])

        # Check all the parallel tags can actually follow the first product tag
        for tag in strip_all_tags(parallel_tags):
            if len(tags[tag]) < len(tags[stripped_product_tags[0]]):
                sys.exit(
                    f"ERROR: in object {obj_name} - parallel tag {tag} shorter than the first object name tag {obj_name_tags[0]}"
                    "\nAll parallel tags must be at least as long as the primary name tag"
                )
        # Calculate the length required for each parallel tag
        # i.e. the number required to keep it paralell with the first object name tag
        parallel_tag_len = (
            reduce(mul, [len(tags[t]) for t in stripped_product_tags[1:]])
            if len(product_tags) > 1
            else 1
        )
        for t in parallel_tags:
            for v in tags[strip_tag(t)]:
                # Store n * tag[t] in the appropriate parallel tag
                parallel_tags[t] += [v] * parallel_tag_len

        # Loop over each product
        for i, values in enumerate(product_tag_values):
            new_name = obj_name
            new_obj = obj_str

            # Fix all the parallel tags
            for t in parallel_tags:
                new_name = ST.replace_clean(new_name, t, parallel_tags[t][i])
                new_obj = ST.replace_clean(new_obj, t, parallel_tags[t][i])

            # Loop over each tag in the product
            for j in range(len(values)):
                new_name = ST.replace_clean(new_name, obj_name_tags[j], values[j])
                new_obj = ST.replace_clean(new_obj, obj_name_tags[j], values[j])

            # Insert the new object back into the global config
            configs["global"]["objects"][new_name] = json.loads(new_obj)

    # Return the expanded configs
    return configs


def find_all_tags(s):
    """Finds all valid tags in the <> <<>> and $$ forms"""
    return re.findall("<.*?>(?!>)", s) + re.findall("\$.*?\$", s)


def strip_tag(tag):
    """strips a tag of its tag chars < > and $"""
    return tag.replace("<", "").replace(">", "").replace("$", "")


def strip_all_tags(tags):
    """strips all tags in a list"""
    return [strip_tag(t) for t in tags]


# EOF
