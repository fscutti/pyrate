"""Some utilities for working with root"""

from pyrate.utils import ROOT_classes as CL
import ctypes

def get_ROOT_colors(my_color):
    """Get ROOT color."""
    if type(my_color) == str:
        # dealing with hex
        rgb = hex_to_rgb(my_color)
    elif type(my_color) == dict:
        rgb = (my_color["R"], my_color["G"], my_color["B"])
    return CL.ColorFinder(rgb[0], rgb[1], rgb[2]).match()

def hex_to_rgb(value):
    """ Converts a hex colour to rgb
    """
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def write(outFile, path, obj):
    """Write an object to file in a particular path.  Creates the path if need be """
    if not outFile.GetDirectory(path):
        outFile.mkdir(path)
    outFile.GetDirectory(path).WriteObject(obj, obj.GetName())

def maxint(t, signed=False):
    """Calculates the max integer value for ctype integers
    Takes in a ctypes.c_<type>() e.g. ctypes.c_int()
    """
    if signed:
        return 2 ** (8 * ctypes.sizeof(t) - 1) - 1
    return 2 ** (8 * ctypes.sizeof(t)) - 1

_Type = {
    "int": {"python": "i", "root": "I", "vector": "int", "invalid": -999},
    "uint": {
        "python": "I",
        "root": "i",
        "vector": "unsigned int",
        "invalid": maxint(ctypes.c_uint()),
    },
    "short": {"python": "h", "root": "S", "vector": "short", "invalid": -999},
    "ushort": {
        "python": "H",
        "root": "s",
        "vector": "unsigned short",
        "invalid": maxint(ctypes.c_ushort()),
    },
    "long": {"python": "l", "root": "L", "vector": "long", "invalid": -999},
    "ulong": {
        "python": "L",
        "root": "l",
        "vector": "unsigned long",
        "invalid": maxint(ctypes.c_ulong()),
    },
    "float": {
        "python": "d",
        "root": "D",
        "vector": "double",  # Python arrays don't have float32's
        "invalid": -999.0,
    },
    "double": {
        "python": "d",
        "root": "D",
        "vector": "double",
        "invalid": -999.0,
    },
    "bool": {"python": "H", "root": "O", "vector": "bool", "invalid": 0},
    "string": {
        "python": "u",
        "root": "C",
        "vector": "string",  # Strings should be stored in vectors
        "invalid": "",
    },
}