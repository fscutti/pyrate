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
        self._objects = {"PERM": {}, "TRAN": {}, "READY": {}, "WRITTEN": {}}
        self._default = {"initialise": "PERM", "execute": "TRAN", "finalise": "PERM"}

        # ----------------------------------------------------------------------------------------
        # PERM:
        #     objects which are persistent throughout the run.
        # TRAN:
        #     objects which are volatile and removed after each input/event loop.
        # READY:
        #     map holding the boolean status of objects which are ready for the finalise step.
        # WRITTEN:
        #     map holding the boolean status of objects which have already been written to output.
        # ----------------------------------------------------------------------------------------

    def put(self, name, obj, opt=None, replace=False):
        """Objects should be put on the store only once!"""
          
        if not opt:
            opt = self._default[self._run.state]

        if self.check(name, opt) and not replace:
            self._run.logger.warning(
                f"object {name} is already on the {opt} store."
            )
            return

        self._objects[opt][name] = obj


    def get(self, name, opt=None):
        """try/except among objects."""

        if opt:

            try:
                return self._objects[opt][name]

            except KeyError:
                pass

            try:
                self._run.update_store(name, self)
                return self._objects[opt][name]

            except KeyError:
                pass

        else:

            opts = ["TRAN", "PERM", "READY", "WRITTEN"]

            while opts:

                try:
                    return self._objects[opts[0]][name]

                except KeyError:
                    pass

                try:
                    self._run.update_store(name, self)
                    return self._objects[opts[0]][name]

                except KeyError:
                    opts = opts[1:]

        msg = f"object {name} has not been found on the store after updating."

        stack_trace = "".join(traceback.format_list(traceback.extract_stack()[:-1]))

        msg2 = "\n".join(
            [
                "******* Stack trace below *******",
                stack_trace,
                "******* Stack trace above *******",
            ]
        )

        sys.stdout.write(stack_trace)

        self._run.logger.error(msg)
        self._run.logger.error(msg2)
        # self._run.logger.error(stack_trace)

        # FN.pretty(self._objects["PERM"]["history"])

        sys.exit(f"ERROR: {msg}\n{msg2}")

    def copy(self, name, opt=None):
        """Returns a copy of the object."""
        return copy(self.get(name, opt))

    def check(self, name, opt=None):
        """Checks if object is in the store."""
        if name != "any":

            if opt:

                return name in self._objects[opt]

            else:

                return any(
                    [
                        name in self._objects[opt]
                        for opt in ["TRAN", "PERM", "READY", "WRITTEN"]
                    ]
                )

        else:
            assert (
                opt
            ), "ERROR: specify option for the store if the check function uses name = any!"
            return self._objects[opt]

    def clear(self, opt):
        """Clears the store or portions of it."""
        if opt != "all":
            self._objects[opt].clear()
        else:
            for opt in self._objects:
                self._objects[opt].clear()


# EOF
