""" Logic functions.
"""

import os
import sys
import re
import json
import yaml
import pyrate


from itertools import product
from functools import reduce
from operator import mul
from copy import deepcopy

from pyrate.utils.ROOT_classes import _Type
import pyrate.utils.strings as ST

def modus_ponens(p, q):
    """Implements the modus ponens logic table: p -> q."""
    if p:
        return q
    else:
        return not p

def is_float(v):
    """Checks if value string is a number."""
    try:
        float(v)
        return True

    except ValueError:
        return False

def find_env(path, env="PYRATE"):
    """Checks existence of environment variable in path and eventually replaces it."""
    if env and env in path:
        env_path = os.environ.get(env)
        if not env_path:
            # env hasn't been set, let's get it internally
            env_path = os.path.abspath(os.path.join(pyrate.__file__ ,"../.."))
        path = path.replace(env, env_path)
    return path


def find_files(paths, env=None):
    """Find all files under a list of paths. It also sorts the list."""
    files = []

    if not isinstance(paths, list):
        paths = [paths]

    for p in paths:
        p = find_env(p, env)

        if not os.path.isfile(p):
            files.extend(
                os.path.join(p, f)
                for f in os.listdir(p)
                if os.path.isfile(os.path.join(p, f))
            )
        else:
            files.append(p)

    files.sort()

    return files


def get_nested_values(d):
    """Returns a generator over all values of a nested dictionary."""
    for v in d.values():
        if isinstance(v, dict):
            yield from get_nested_values(v)
        else:
            yield v

def expand_nested_values(d):
    """ Returns a generator like get_nested_values, but handles all iterables 
        instead of just dictionaries. Stops when the last interable contains
        not more iterables
    """
    if iterable(d) and not isinstance(d, str):
        # Ok still dealing with an indexable object (but not a string)
        if isinstance(d, dict):
            # Dictionary case
            for v in d.values():
                yield from expand_nested_values(v)

        else:
            # List, tuple, array case...
            for v in d:
                yield from expand_nested_values(v)
    else:
        # Not iterable / is a string
        yield d


def flatten(l):
    """Flattens a list of lists."""
    return [item for sublist in l for item in sublist]


def nested(l):
    """Returns a nested dictionary where keys are taken from a list."""
    d = tmp = {}
    for k in l:
        tmp[k] = {}
        tmp = tmp[k]
    return d


def get_copy(o, copy):
    """Returns copy of object."""
    if copy:
        return copy(o)
    else:
        return o


def pretty(d, indent=0):
    """Prints dictionary with pre-defined intentation."""
    for key, value in d.items():
        print("\t" * indent + str(key))
        if isinstance(value, dict):
            pretty(value, indent + 1)
        else:
            if isinstance(value, list):
                print("\t" * (indent + 1))
                for idx, l in enumerate(value):
                    print("\t" * (indent + 1) + str(idx) + " : " + str(l))
            else:
                print("\t" * (indent + 1) + str(value))


def merge(target, probe, path=None, merge_list=False):
    """Merges probe into target."""
    if path is None:
        path = []

    for k in probe:
        if k in target:

            if isinstance(target[k], dict) and isinstance(probe[k], dict):
                merge(target[k], probe[k], path + [str(k)])

            elif target[k] == probe[k]:
                # same leaf value
                pass

            elif merge_list:
                # if a conflict exist but values are lists merge them upon request
                if isinstance(target[k], list) and isinstance(probe[k], list):
                    target[k].extend(probe[k])

                    target[k] = list(dict.fromkeys(target[k]))

            else:
                raise Exception("Conflict at %s" % ".".join(path + [str(k)]))
        else:
            target[k] = probe[k]
    return target


def intersect(probe, target):
    """Intersection of two nested dictionaries."""
    intersection = {}

    if probe == {}:
        intersection = target

    else:
        for k in set(target).intersection(set(probe)):

            p = probe[k]
            t = target[k]

            if isinstance(t, dict) and isinstance(p, dict):
                if p == {}:
                    intersection[k] = t
                else:
                    intersection[k] = intersect(p, t)

            elif not isinstance(t, dict) and p == {}:
                intersection[k] = t

            elif t == p:
                intersection[k] = t
            else:
                raise ValueError("values for common keys don't match")
    return intersection


def find(key, dictionary):
    """Find value of key in nested dictionary and returns a generator over the found arguments.
    Thank you, internet!
    https://stackoverflow.com/questions/9807634/find-all-occurrences-of-a-key-in-nested-dictionaries-and-lists
    """
    if hasattr(dictionary, "items"):
        for k, v in dictionary.items():
            if k == key:
                yield v

            if isinstance(v, dict):
                for result in find(key, v):
                    yield result

            elif isinstance(v, list):
                for d in v:
                    for result in find(key, d):
                        yield result


def check(key, dictionary):
    """Uses the find function to just check the existence of the key without returning the generator."""
    return bool([i for i in find(key, dictionary)])


def grab(key, dictionary):
    """This is just a wrapper around the find function, getting a single item as opposed to the iterator."""
    return [i for i in find(key, dictionary)][0]


def check_dict_in_list(list, dictionary):
    """Checks if a dictionary is found in a list of dictionaries."""
    for d in list:

        counter = 0

        for k, v in dictionary.items():

            if k in d:
                if d[k] == v:

                    counter += 1

        if counter == len(dictionary):
            return True

    return False


def get_color(my_color):
    """Given a pixel string it prepares a pixel dictionary."""
    my_color = my_color.replace(" ", "")

    my_color = {c.split(":")[0]: float(c.split(":")[1]) for c in my_color.split("|")}

    return my_color


def add_colors(my_color_list):
    """Adds color pixels from a list. Avoids white."""
    added_color = {"R": 0.0, "G": 0.0, "B": 0.0}

    for idx, my_color in enumerate(my_color_list):

        added_color["R"] += my_color["R"]
        added_color["G"] += my_color["G"]
        added_color["B"] += my_color["B"]

        is_white = sum([added_color[pixel] for pixel in ["R", "G", "B"]]) >= 2.9

        if is_white:
            added_color[["R", "G", "B"][idx % 3]] = 0.0

    return added_color


def iterable(obj):
    """Determines if an object is iterable or not"""
    try:
        iter(obj)
    except Exception:
        return False
    else:
        return True

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
    for t in configs:
        if find_all_tags(t):
            # found a tag:
            stripped_t = strip_tag(t)
            if stripped_t in forbidden_tags:
                sys.exit(f"ERROR: tag {t} is a forbidden tag.")
            tags[stripped_t] = configs[t]

    # First we should deal with any $tag$ in the config
    config_str = json.dumps(configs["objects"])
    for tag in tags:
        config_str = ST.replace_clean(config_str, f"${tag}$", tags[tag])
    configs["objects"] = json.loads(config_str)

    # Deal with object duplication
    # Loop through all objects and find any that need duplicating
    # They must have a tag in their name, as object names must be unique.
    objects_to_dup = {}
    for obj_name, obj in configs["objects"].items():
        obj_name_tags = strip_all_tags(find_all_tags(obj_name))
        for tag in tags:
            if tag in obj_name_tags:
                objects_to_dup[obj_name] = obj
    # clear out the found objects
    for obj_name in objects_to_dup:
        del configs["objects"][obj_name]

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
            configs["objects"][new_name] = json.loads(new_obj)

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

def dump_objects_to_yaml(config, filepath):
    """ Dumps the objects config to a yaml file
        Typicall takes in the global objects config dictionary
    """
    with open(filepath, 'w') as f:
        yaml.dump(config, f, 
        default_flow_style=False, indent=4, explicit_start=True)

# EOF
