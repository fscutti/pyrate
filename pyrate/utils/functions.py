""" Logic functions.
"""
import os
from copy import copy

def modus_ponens(p,q):
    """ Implements the modus ponens logic table: p -> q
    """
    if p: return q
    else: return not p

#def has_key(k,d):
#    """ Checks if dictionary has key.
#    """
#    return k in d

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

def merge(a, b, path=None):
    """ Merges dictionary b into dictionary a.
    """
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



def intersect(a, b, path=None):
    """ Merges dictionary b into dictionary a.
    """
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
def intersect(a, b, path=None):
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass # same leaf value
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a
"""

#EOF
