""" Store class.
"""
import sys
from copy import copy
import traceback

from pyrate.utils import functions as FN


class Store:
    def __init__(self, run):
        self._run = run
        self.name = self._run.name
        self._objects = {"PERM": {}, "TRAN": {}, "READY": {}}
        # ------------------------------------------------------------------------------------
        # PERM:
        #     objects which are persistent throughout the run.
        # TRAN:
        #     objects which are volatile and removed after each input/event loop.
        # READY:
        #     map holding the boolean status of objects which are ready for the finalise step.
        # ------------------------------------------------------------------------------------

    def put(self, name, obj, opt="TRAN", replace=False):
        """Objects should be put on the store only once!"""
        if self.check(name, opt) and not replace:
            self._run.logger.warning(f"object {name} is already on the {opt} store.")
            return

        self._objects[opt][name] = obj

    def get(self, name, opt="TRAN"):
        """try/except among objects."""
        try:
            return self._objects[opt][name]

        except KeyError:
            pass

        try:
            self._run.update(name, self)
            return self._objects[opt][name]

        except KeyError:
            msg = f"object {name} has not been found on the {opt} store after updating."
            print("\n***** Full stack trace *****")
            stack_trace = ''.join(traceback.format_list(traceback.extract_stack()[:-1]))
            sys.stdout.write(stack_trace)
            print("\n***** See full stack trace above *****")
            self._run.logger.error(msg)
            self._run.logger.error(stack_trace)

            self._run.logger.error(msg)

            FN.pretty(self._objects["PERM"]["history"])

            sys.exit(f"ERROR: {msg}")

    def copy(self, name, opt="TRAN"):
        """Returns a copy of the object."""
        return copy(self.get(name, opt))

    def check(self, name="any", opt="TRAN"):
        """Checks if object is in the store."""
        if name != "any":
            return name in self._objects[opt]
        else:
            return self._objects[opt]

    def clear(self, opt="TRAN"):
        """Clears the store or portions of it."""
        if opt != "all":
            self._objects[opt].clear()
        else:
            for opt in self._objects:
                self._objects[opt].clear()


# EOF
