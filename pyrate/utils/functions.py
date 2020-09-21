""" Logic functions.
"""
import os
from copy import copy

def modus_ponens(p,q):
    """ Implements the modus ponens logic table: p -> q
    """
    if p: return q
    else: return not p

def find_files(paths):
    """ Find all files under a list of paths. It also sorts the list.
    """
    files = []
    if not isinstance(paths,list): paths = [paths]
    for p in paths: files.extend(os.path.join(p,f) for f in os.listdir(p) if os.path.isfile(os.path.join(p,f)))
    files.sort()
    return files

def flatten(l):
    """ Flattens a list of lists.
    """
    return [item for sublist in l for item in sublist]

def nested(l):
    """ Returns a nested dictionary where keys are taken from a list.
    """
    d = tmp = {}
    for k in l:
        tmp[k] = {}
        tmp = tmp[k]
    return d

def get_copy(o,copy):
    """ Returns copy of object.
    """
    if copy:
        return copy(o)
    else:
        return o

def pretty(d, indent=0):
    """ Prints dictionary with pre-defined intentation.
    """
    for key, value in d.items():
       print('\t' * indent + str(key))
       if isinstance(value, dict):
          pretty(value, indent+1)
       else:
          print('\t' * (indent+1) + str(value))


"""
def merge(a, b, path=None):
    if path is None: path = []
    for key in b:
        if key in a and not (a[key]=={} or b[key]=={}):
                
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            
            elif a[key] == b[key]:
                pass # same leaf value
            
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        
        elif key in a and (a[key]=={} or b[key]=={}):
            a[key] = {}
        
        else:
            a[key] = b[key]
    return a 
"""
"""
def intersect(a, b, path=None):
    if path is None: path = []

    # check here if any of the values of b is null.

    #for k,v in b.items():
    #    if not v == {}:
    #        print("This is the value of b", b.values())

    print("******* Merging: ", a, b)
    for key in b:
        if key in a:
               
            if isinstance(a[key], dict) and isinstance(b[key], dict):
               print("******* Iterating: ", key, a[key], b[key])
               merge(a[key], b[key], path + [str(key)])
            
            elif a[key] == b[key]:
                print("******* Same leaf value: ", key, a[key], b[key])
                pass # same leaf value
            
            else:
                print(key, a[key], b[key])
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        
        else:
            a[key] = b[key]
    return a 
"""

def merge(target, probe, path=None):
    """ Merges probe into target.
    """
    if path is None: path = []

    for k in probe:
        if k in target:

            if isinstance(target[k], dict) and isinstance(probe[k], dict):
                merge(target[k], probe[k], path + [str(k)])

            elif target[k] == probe[k]:
                pass # same leaf value

            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(k)]))
        else:
            target[k] = probe[k]
    return target


def intersect(probe, target):
    """ Intersection of two nested dictionaries.
    """
    intersection = {}

    if probe=={}:
        intersection=target

    else: 
        for k in set(target).intersection(set(probe)):
        
            p = probe[k]
            t = target[k]
        
            if isinstance(t, dict) and isinstance(p, dict):
                if p=={}:
                    intersection[k] = t
                else:
                    intersection[k] = intersect(p, t)
            
            elif not isinstance(t, dict) and p=={}:
                intersection[k] = t
        
            elif t == p:
                intersection[k] = t
            else:
                raise ValueError("values for common keys don't match")
    return intersection

#EOF
