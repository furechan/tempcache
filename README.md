# Python library to cache data and function results in temporary files

This library offers a simple way to cache data and function results using temporary files, including a mechanism for automatic expiration after a certain time.

Dy default, the package uses the `pickle` module to serialize data and hash key values.


> **Note**
For more advanced use cases you may want to look at the `Memory` class
in [joblib](https://github.com/joblib/joblib).


## Basic Usage

An instance of the `TempCache` class be used as a decorator
to automatically cache the results of a function.

```python
from tempcache import TempCache

CACHE_MAX_AGE = 24 * 60 * 60 * 2    # two days
cache = TempCache("mycache", max_age=CACHE_MAX_AGE)

@cache
def long_running(...):
    ...

result = long_running(...)
```

## Caching results at the call site

You can also use a `TempCache` object to cache a result
at the call site with the `cache_result` method. 

```python
from tempcache import TempCache

CACHE_MAX_AGE = 24 * 60 * 60 * 2    # two days
cache = TempCache("mycache", max_age=CACHE_MAX_AGE)

def long_running(...):
    ...

result = cache.cache_result(long_running, ...)
```

## Advanced usage

In cases where the function or some of its arguments
are defined in the `__main__` namespace or in a jupyter notebook
and cannot be pickled by `pickle` you can use a different pickle module
like `cloupickle`.


```python
import cloudpickle

from tempcache import TempCache

CACHE_MAX_AGE = 24 * 60 * 60 * 2    # two days
cache = TempCache("mycache",
                    pickler=cloudpickle,
                    max_age=CACHE_MAX_AGE)

key = ...
# key object can be complex as long as it is pickle-able

item = cache.item_for_key(key)
# cache item for the given key whether it exists or not

# load item if it exists
if item.exists():
    value = item.load()

# save item
item.save(value)
```


## Examples

Examples notebooks are in the `extras` folder.

## Installation

You can install this package with `pip`.

```console
pip install tempcache
```

## Related Projects

- [joblib](https://github.com/joblib/joblib)
Computing with Python functions
- [percache](https://pypi.org/project/percache/)
Persistently cache results of callables
- [disckcache](https://pypi.org/project/diskcache/)
Disk and file backed cache library compatible with Django
- [cloudpickle](https://github.com/cloudpipe/cloudpickle)
Extended pickling support for Python objects
