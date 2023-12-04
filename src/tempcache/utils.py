""" key digest routines """

import inspect


def args_with_defaults(func, args, kwargs):
    """ apply function defaults  """

    signature = inspect.signature(func)

    binding = signature.bind(*args, **kwargs)
    binding.apply_defaults()

    return binding.args, binding.kwargs
