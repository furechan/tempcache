# TempCache Documentation

TempCache is a Python utility that provides temporary file-based caching functionality. It's designed to cache function results and arbitrary data using the system's temporary directory.


## Installation

```bash
pip install tempcache
```

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

## API Reference

### `TempCache` Class

```python
TempCache(name='tempcache', *, source=None, max_age=None, pickler=None)
```

Main cache utility class.

Parameters:
- `name` (str): Name of caching folder under tempdir (default: 'tempcache')
- `source` (str, optional): Extra source information to differentiate key hashes
- `max_age` (int, optional): Maximum age in seconds (default: 7 days)
- `pickler` (module, optional): Custom pickler module (default: pickle)

Methods:
- `clear_items(all_items=False)`: Clear expired or all items
- `item_for_key(key)`: Get cache item for a specific key
- `cache_result(func, *args, **kwargs)`: Cache function results
- `__call__(func)`: Decorator interface for function caching

### `CacheItem` Class

```python
CacheItem(path, *, pickler=None)
```

Represents a single cached item.

Methods:
- `exists()`: Check if item exists
- `older_than(whence)`: Check if item is older than given timestamp
- `newer_than(whence)`: Check if item is newer than given timestamp
- `delete()`: Delete the cached item
- `load()`: Load item contents
- `save(data)`: Save item contents
- `try_load()`: Load item contents, ignoring errors
- `try_save(data)`: Save item contents, ignoring errors


## Features

- File-based caching using system's temp directory
- Automatic cache expiration
- Custom pickle support
- Function caching through decorators
- Key-based caching for arbitrary data


## Best Practices

- Use meaningful cache names to avoid conflicts
- Set appropriate max_age for your use case
- Handle cache loading exceptions in production code
- Use the source parameter when caching across different contexts
- Clear expired items periodically in long-running applications

## Limitations

- Cache items are stored in the system's temp directory
- File-based storage might not be suitable for high-frequency operations
- No built-in cache size limiting
- No atomic operations guarantee

