# TempCache Documentation

TempCache is a Python utility that provides temporary file-based caching functionality. It's designed to cache function results and arbitrary data using the system's temporary directory.

## Installation

```bash
pip install tempcache
```

## Basic Usage

### Simple Function Caching

```python
from tempcache import TempCache

# Create a cache instance
cache = TempCache("mycache")

# Use as a decorator
@cache
def expensive_function(x, y):
    # Some expensive computation
    return x + y
```

### Manual Cache Management

```python
# Create a cache instance
cache = TempCache("mycache")

# Cache some data
item = cache.item_for_key("my_key")
item.save({"data": "value"})

# Retrieve cached data
if item.exists():
    data = item.load()
```

## Features

- File-based caching using system's temp directory
- Automatic cache expiration
- Custom pickle support
- Function caching through decorators
- Key-based caching for arbitrary data

## API Reference

### TempCache Class

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

### CacheItem Class

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

## Examples

### Caching Function Results

```python
from tempcache import TempCache

# Create cache with custom expiration (1 hour)
cache = TempCache("mycache", max_age=3600)

@cache
def fetch_data(url):
    # Expensive network operation
    return requests.get(url).json()

# First call will fetch and cache
data = fetch_data("https://api.example.com/data")

# Subsequent calls will use cached data if not expired
data = fetch_data("https://api.example.com/data")
```

### Using Custom Pickler

```python
import cloudpickle
from tempcache import TempCache

# Create cache with custom pickler
cache = TempCache("mycache", pickler=cloudpickle)

# Now you can cache more complex objects
item = cache.item_for_key("complex_data")
item.save({"lambda": lambda x: x*2})
```

### Manual Cache Management

```python
from tempcache import TempCache

cache = TempCache("mycache")

# Save data
item = cache.item_for_key(("user", 123))
item.save({"name": "John", "age": 30})

# Check expiration
if item.newer_than(some_timestamp):
    data = item.load()

# Clear expired items
cache.clear_items()

# Clear all items
cache.clear_items(all_items=True)
```

## Best Practices

1. Use meaningful cache names to avoid conflicts
2. Set appropriate max_age for your use case
3. Handle cache loading exceptions in production code
4. Use the source parameter when caching across different contexts
5. Clear expired items periodically in long-running applications

## Limitations

- Cache items are stored in the system's temp directory
- File-based storage might not be suitable for high-frequency operations
- No built-in cache size limiting
- No atomic operations guarantee

