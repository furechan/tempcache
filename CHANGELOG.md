# Changelog

## 0.0.14
- Added `wrap` method as explciit decorator

## 0.0.13
- Added `cache_upath` method to cache cloud paths

## 0.0.12
- Switched to `uv-build` backend
- Switched to `tox.toml` config
- Renamed first argument `name_or_path`
- Python minimal version now `3.10`

## 0.0.10
- Added `try_load` and `try_save` methods to `CacheItem`

## 0.0.9
- `modified_since` is deprecated. Use `newer_than` intead.

## 0.0.7
- Replaced `random.randbytes` with `os.urandom` in tests
- Added `tox.ini` configuration file

## 0.0.6
- Files are located in a sub-folder of the temp directory
- Tempcache accepts a `name` parameter as name of is sub-folder
- Added `source` argument to `TempCache` to further differentiate caches
- Using `inspect` module `BoundArguments` to create task digests

