# Python library to cache data and function results in temporary files

This library offers a simple way to
cache data and function results using temporary files.
By default it will use the `pickle` module
to hash key values and serialize output data.
This is meant to be used with long running functions
that have repeatable results. The hashing of keys is dependent
on the pickle algorithm and so it may work accross different
python environments, as long as they have a compatible pickling algorithm.

To avoid possible collisions make sure to use
a unique name when instantiating `TempCache`.
You can also add a `source` argument as any opaque string
to further differentiate cache keys from other caches.


> **Note**
For more advanced use cases you may want to look at the `Memory` class
in [joblib](https://github.com/joblib/joblib).


## Basic Usage

An instance of the `TempCache` class be used as a decorator
to automatically cache the results of a function.

```python
from tempcache import TempCache

CACHE_MAX_AGE = 24 * 60 * 60 * 2    # two days
temp_cache = TempCache(__name__, max_age=CACHE_MAX_AGE)

@temp_cache
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
temp_cache = TempCache(__name__, max_age=CACHE_MAX_AGE)

def long_running(...):
    ...

result = temp_cache.cache_result(long_running, ...)
```

## Advanced usage

In cases where the function or some of its arguments
are defined in the `__main__` namespace or in a jupyter notebook
and cannot be pickled by `pickle` you may want
to use a different pickle module like `cloupickle`.


```python
import cloudpickle

from tempcache import TempCache

CACHE_MAX_AGE = 24 * 60 * 60 * 2    # two days
temp_cache = TempCache("tempcache-foo",
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

## Related Projects

- [joblib](https://github.com/joblib/joblib)
Computing with Python functions
- [cloudpickle](https://github.com/cloudpipe/cloudpickle)
Extended pickling support for Python objects

