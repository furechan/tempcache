# Changelog

## 0.0.14
- Added `wrap` method as explciit decorator
- Replaced tox with nox for the python version test matrix (`noxfile.py`)

## 0.0.12
- Switched to `uv-build` backend
- Switched to `tox.toml` config
- Renamed first argument `name_or_path`
- Python minimal version now `3.10`

## 0.0.7
- Replaced `random.randbytes` with `os.urandom` in tests
- Added `tox.ini` configuration file

## 0.0.6
- Files are located in a sub-folder of the temp directory
- Tempcache accepts a `name` parameter as name of is sub-folder
- Added `source` argument to `TempCache` to further differentiate caches
- Using `inspect` module `BoundArguments` to create task digests

