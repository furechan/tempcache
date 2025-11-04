# Python library to cache data and function results in temporary files

This library offers a simple way to cache data and function results using temporary files, including a mechanism for automatic expiration after a certain time.
This library is best used for long running or expensive functions as well as processes that return large datasets.
Each item is saved as a saparate file whose name is computed by serializing the inputs and hashing the result into a unique file name.



> **Note**
For advanced use cases you may want to look at the `Memory` class
in [joblib](https://github.com/joblib/joblib).


## Basic usage

Caching is done through a `TempCache` class instance that manages cache items in a dedicated caching folder.
The first parameter should be the name to use as temp sub-folder or alternatively the absolute path of the cache folder.
Note that the caching folder will be created if it does not already exists.

Any instance of the `TempCache` class can be used as a decorator to wrap a function and automatically cache its results.

```python
from tempcache import TempCache

cache = TempCache("mycache", max_age=86_400) # One day

@cache.wrap
def long_running(...):
    ...

result = long_running(...)
```

## Caching results at the call site

You can also use a `TempCache` instance to cache a function call directly 
at the call site with the `cache_result` method. 

```python
from tempcache import TempCache

cache = TempCache("mycache", max_age=86_400) # One day

def long_running(...):
    ...

result = cache.cache_result(long_running, ...)
```


## Custom serialization

In cases where the inputs or result cannot be serialized by `pickle`
you may want to use a custom pickler like the `cloupickle` module.

```python
import cloudpickle

from tempcache import TempCache

cache = TempCache("mycache",
                    pickler=cloudpickle,
                    max_age=86_400) # one day
```

## Examples

Examples notebooks are in the `extras` folder.

## Installation

You can install this package with `pip`.

```console
pip install tempcache
```

## Related projects

- [joblib](https://github.com/joblib/joblib)
Computing with Python functions
- [percache](https://pypi.org/project/percache/)
Persistently cache results of callables
- [disckcache](https://pypi.org/project/diskcache/)
Disk and file backed cache library compatible with Django
- [cloudpickle](https://github.com/cloudpipe/cloudpickle)
Extended pickling support for Python objects
- [cached_path](https://github.com/allenai/cached_path)
A file utility for accessing both local and remote files through a unified interface
