""" Logic functions.
"""
import os
from copy import copy


def modus_ponens(p, q):
    """Implements the modus ponens logic table: p -> q"""
    if p:
        return q
    else:
        return not p


def find_env(path, env):
    """Checks existence of environment variable in path and eventually replaces it."""
    if env in path:
        path = path.replace(env, os.environ.get(env))
    return path


def find_files(paths, env=None):
    """Find all files under a list of paths. It also sorts the list."""
    files = []

    if not isinstance(paths, list):
        paths = [paths]

    for p in paths:

        if env and env in p:
            p = p.replace(env, os.environ.get(env))
        
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
    print("\n\n\n")
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
    print("\n\n\n")


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
    """Find value of key in nested dictionary. Thank you, internet!
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


def grab(key, dictionary):
    """This is just a wrapper around the find function, getting a single item as opposed to the iterator."""
    return [i for i in find(key, dictionary)][0]


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


# EOF
