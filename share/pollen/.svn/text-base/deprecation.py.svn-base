"""
Deprecation helpers.
"""

import warnings, sys


def deprecateModuleAttributes(moduleName, deprecations):
    """
    Deprecate module attributes.

    This function uses magic to mark module-scope attributes as deprecated. When
    a deprecated attribute is touched for the first time a descriptive message
    is emmitted using Python's standard warnings module.

    Parameters:

        moduleName:
            The full module name. Hint: try __name__.

        deprecations:
            A map of deprecated attributes to messages. The message should
            ideally make sense as a sentence and include the version when the
            deprecation occurred.

    Example module:

        oldName = None
        newName = None

        from pollen import deprecation
        deprecation.deprecateModuleAttributes(
            __name__,
            {'oldName': '[0.1] Use newName instead.'}
            )
    """
    module = sys.modules[moduleName]
    sys.modules[moduleName] = ModuleMagic(module, moduleName, deprecations)


class ModuleMagic(object):
    """
    A magic module wrapper, not be be used directly.
    """

    def __init__(self, module, moduleName, deprecations):
        # Record the module info and the mapping of deprecations.
        self.__module = module
        self.__moduleName = moduleName
        self.__deprecations = deprecations
        # Copy non-deprecated attributes across to avoid __getattr__ unnecessary
        # calls.
        for name, value in vars(module).iteritems():
            if name in deprecations:
                continue
            setattr(self, name, value)

    def __getattr__(self, name):
        try:
            message = self.__deprecations[name]
        except KeyError:
            pass
        else:
            warnings.warn('%s.%s is deprecated.  %s' % (self.__moduleName, name,
                message), DeprecationWarning, stacklevel=2)
        return getattr(self.__module, name)

