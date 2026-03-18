# Python library to cache data and function results in temporary files

This library offers a simple way to cache data and function results using temporary files, including a mechanism for automatic expiration after a certain time.
This library is best suited for slow or expensive functions that return large or complex results.
Each item is saved as a separate file whose name is computed by serializing the inputs and hashing the result into a unique file name.

> **Note**
> For advanced use cases you may want to look at the `Memory` class
> in [joblib](https://github.com/joblib/joblib).


## Basic usage

Caching is done through a `TempCache` class instance that manages cache items in a dedicated caching folder.
The first parameter should be the name to use as temp sub-folder or alternatively the absolute path of the cache folder.
The caching folder will be created if it does not already exist.

A `TempCache` instance can be used as a decorator to wrap a function and automatically cache its results.
Optional parameters include `max_age` (expiry in seconds) and `pickler` (custom pickler like `cloudpickle` for non-picklable objects).

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


## Manual caching

For fine-grained control you can manage cache entries directly. Any pickle-able value can be used as a key — it gets hashed into a digest string that identifies the cache entry.

```python
cache = TempCache("mycache", max_age=86_400)

digest = cache.key_digest(my_key)

result = cache.try_load(digest)

if result is None:
    result = compute(my_key)
    cache.try_save(digest, result)
```



## Clearing the cache

Expired items are removed automatically on read, but you can also trigger cleanup explicitly.

```python
cache.clear_items()                # remove expired items
cache.clear_items(all_items=True)  # remove everything
```

## Isolating caches with `source`

If two caches share the same folder, identical keys will collide. Use `source` to namespace them:

```python
cache_a = TempCache("mycache", source="feed-a")
cache_b = TempCache("mycache", source="feed-b")
```

The same key will produce different digests in each cache.


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
- [cachier](https://github.com/python-cachier/cachier)
  Persistent function caching with TTL, supports pickle and MongoDB backends
- [cachetools](https://github.com/tkem/cachetools)
  In-memory caching with LRU, TTL and other eviction strategies
- [klepto](https://github.com/uqfoundation/klepto)
  Scientific caching library supporting file, memory and database backends
