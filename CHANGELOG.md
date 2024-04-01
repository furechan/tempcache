# Changelog

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

