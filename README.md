# Python library to cache data and function results in temporary files

This library offers a simple way to cache data and function results using temporary files, including a mechanism for automatic expiration after a certain time.

Dy default, the package uses the `pickle` module to serialize data. Inputs are first serialized and then hashed to create unique cache file names.


> **Note**
For more advanced use cases you may want to look at the `Memory` class
in [joblib](https://github.com/joblib/joblib).


## Basic usage

An instance of the `TempCache` class be used as a decorator
to wrap a function and cache its results.

```python
from tempcache import TempCache

CACHE_MAX_AGE = 86_400  # one day
cache = TempCache("mycache", max_age=CACHE_MAX_AGE)

@cache
def long_running(...):
    ...

result = long_running(...)
```

## Caching results at the call site

You can also use a `TempCache` object to cache a function call directly 
at the call site with the `cache_result` method. 

```python
from tempcache import TempCache

CACHE_MAX_AGE = 86_400  # one day
cache = TempCache("mycache", max_age=CACHE_MAX_AGE)

def long_running(...):
    ...

result = cache.cache_result(long_running, ...)
```


## Custom serialization

In cases where the inputs or result cannot be serialized by `pickle`
you should use a pickler module like `cloupickle`.

```python
import cloudpickle

from tempcache import TempCache

CACHE_MAX_AGE = 86_400  # one day
cache = TempCache("mycache",
                    pickler=cloudpickle,
                    max_age=CACHE_MAX_AGE)
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
