"""Caching Utilities using Temporary files"""

import os
import time
import pickle
import inspect
import logging
import hashlib
import tempfile
import functools

import datetime as dt

from pathlib import Path

from typing import Any, Optional


logger = logging.getLogger(__name__)


DEFAULT_NAME = "tempcache"
FILE_PATTERN = "{digest}.tmp"
DEFAULT_MAX_AGE = 24 * 60 * 60 * 7  # one week



class TempCache:
    """Temporary File Cache Utility.

    Objects are stored in temporary files under a cache folder in the tempdir.
    The cache folder is automatically created if it does not already exist.
    Objects are stored as pickled data with a hash of the key for filename.
    """

    ONEDAY = 24 * 60 * 60
    ONEHOUR = 60 * 60


    def __init__(
        self,
        name_or_path: str = DEFAULT_NAME,
        *,
        source: Optional[str] = None,
        max_age: Optional[int] = None,
        pickler: Any = None,
    ):
        """
        Temporary File Cache Utility.

        Args:
            name_or_path: name or path of cache folder (default 'tempcache')
                if a simple name use as subfolder of tempdir
            source: optional, extra source information that can be
                used to differentiate key hashes from other caches
            pickler: optional, custom pickler module like cloudpickle
            max_age: optional, maximum age in seconds
        """

        if max_age is None:
            max_age = DEFAULT_MAX_AGE

        if max_age <= 0:
            raise ValueError(f"Invalid max_age {max_age}")

        if pickler is None:
            pickler = pickle

        name_or_path = os.path.expanduser(name_or_path)

        if os.path.isabs(name_or_path):
            path = Path(name_or_path)
        else:
            path = Path(tempfile.gettempdir(), name_or_path)

        # create folder if needed
        path.mkdir(exist_ok=True)

        self.path = path
        self.source = source
        self.pickler = pickler
        self.max_age = max_age


    def cache_item(self, path):
        """Create a cache item instance.

        Args:
            path: Path for the cache item

        Returns:
            CacheItem: New cache item instance
        """
        return CacheItem(path, pickler=self.pickler)

    def get_expiry(self):
        """Calculate the expiry timestamp.

        Returns:
            float: Timestamp before which items are considered expired
        """
        expiry = time.time() - self.max_age
        return expiry

    def items(self):
        """Iterate over all cache items.

        Yields:
            CacheItem: Each cache item found
        """
        pattern = FILE_PATTERN.format(digest="*")

        for file in self.path.glob(pattern):
            yield self.cache_item(file)


    def clear_items(self, all_items=False):
        """Clear expired or all cache items.

        Args:
            all_items: If True, clear all items regardless of expiration

        Returns:
            int: Number of items cleared
        """
        count = 0
        expiry = self.get_expiry()
        for item in self.items():
            if all_items or item.older_than(expiry):
                item.delete()
                count += 1

        return count


    def item_for_digest(self, digest):
        """Get cache item for a hash digest.

        Args:
            digest: Hash digest string

        Returns:
            CacheItem: Cache item (may not exist)
        """
        fname = FILE_PATTERN.format(digest=digest)
        path = self.path.joinpath(fname)
        item = self.cache_item(path)

        # delete expired item to enforce expiry
        expiry = self.get_expiry()
        if item.older_than(expiry):
            item.delete()

        return item

    def item_for_key(self, key):
        """Get cache item for a cache key.

        Args:
            key: Cache key to hash. Must be pickle-able

        Returns:
            CacheItem: Cache item (may not exist)
        """
        hash = hashlib.md5()

        if self.source is not None:
            data = self.source.encode("utf-8")
            hash.update(data)

        data = self.pickler.dumps(key)
        hash.update(data)

        digest = hash.hexdigest()

        return self.item_for_digest(digest)

    def item_for_task(self, func, args, kwargs):
        """Get cache item corresponding to a function call.

        Args:
            func: Function to cache
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            CacheItem: Cache item (may not exist)
        """
        funcname = f"{func.__module__}.{func.__qualname__}"

        signature = inspect.signature(func)
        params = signature.bind(*args, **kwargs)
        params.apply_defaults()

        key = (funcname, params)

        return self.item_for_key(key)

    def cache_result(self, func, *args, **kwargs):
        """Get cached result or compute and cache new result.

        Args:
            func: Function to call
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            The function result (cached or fresh)
        """
        item = self.item_for_task(func, args, kwargs)

        try:
            if item.exists():
                return item.load()
        except Exception as ex:
            logger.warning("Failed to load %s: %s", item.path, ex)

        result = func(*args, **kwargs)

        try:
            item.save(result)
        except Exception as ex:
            logger.warning("Failed to save %s: %s", item.path, ex)

        return result


    def cache_upath(self, path, *, refresh=0):
        """
        Create local file cache from a universal path
        The local copy is updated when the remote has changed.
        This is done by checking the modified time of the remote path.

        Args:
            path (Upath | Path): remote path
            refresh (seconds): how often to check if the remote has changed

        Returns:
            path to local copy of the data
        """

        PATH_METHODS = ("exists", "stat", "read_bytes")

        # Check path supports required methods (Cloudpath, UPath, Path)
        if any(getattr(path, attr, None) is None for attr in PATH_METHODS):
            raise TypeError(f"Invalid path type {type(path).__name__}")

        key = (str(path),)
        item = self.item_for_key(key)

        # cache exists and is recent enough 
        if refresh > 0 and item.newer_than(time.time() - refresh):
            return item.path
        
        # path does not exist. remove cache and raise
        if not path.exists():
            item.delete()
            raise ValueError(f"Path {path} does not exist!")

        mtime = path.stat().st_mtime

        # cache is up to date
        if item.newer_than(mtime):
            return item.path

        # copy data to local cache
        data = path.read_bytes()
        item.path.write_bytes(data)

        return item.path


    def __call__(self, func):
        """Decorator to cache function results.

        Args:
            func: Function to wrap

        Returns:
            callable: Wrapped function that caches results
        """

        @functools.wraps(func)
        def cached_func(*args, **kwargs):
            return self.cache_result(func, *args, **kwargs)

        return cached_func


class CacheItem:
    """A cache item representing a single data file on disk.
    
    A new cache item may not already exist, or may have just been deleted if it expired.
    """

    def __init__(self, path, *, pickler=None):
        """Initialize a cache item.

        Args:
            path: Path of the cached item
            pickler: Custom pickler module (defaults to pickle)
        """
        if isinstance(path, str):
            path = Path(path).resolve()

        if pickler is None:
            pickler = pickle

        self.path = path
        self.pickler = pickler

    def exists(self):
        """Check whether item exists on disk.

        Returns:
            bool: True if the file exists, False otherwise
        """
        return self.path.exists()

    def older_than(self, whence):
        """Check whether item is older than given timestamp.

        Args:
            whence: Timestamp or datetime to compare against

        Returns:
            bool: True if file exists and is older than whence, False otherwise
        """
        if isinstance(whence, dt.datetime):
            whence = whence.timestamp()

        try:
            mtime = self.path.stat().st_mtime
            return mtime < whence
        except FileNotFoundError:
            return False

    def newer_than(self, whence):
        """Check whether item is newer than given timestamp.

        Args:
            whence: Timestamp or datetime to compare against

        Returns:
            bool: True if file exists and is newer than whence, False otherwise
        """
        if isinstance(whence, dt.datetime):
            whence = whence.timestamp()

        try:
            mtime = self.path.stat().st_mtime
            return mtime > whence
        except FileNotFoundError:
            return False

    def delete(self):
        """Delete the cache item from disk. Ignoring errors."""
        logger.debug("Deleting %s", self.path)

        try:
            self.path.unlink(missing_ok=True)
        except (FileNotFoundError, PermissionError) as ex:
            logger.warning("Error deleting %s: %s", self.path, ex)

    def load(self):
        """Load and unpickle the cached item contents.

        Returns:
            The unpickled object
        """
        logger.debug("Loading %s", self.path)

        with self.path.open("rb") as file:
            return self.pickler.load(file)

    def try_load(self):
        """Load and unpickle the cached item contents, ignoring errors.

        Returns:
            The unpickled object or None if there was an error
        """
        try:
            return self.load()
        except Exception as ex:
            logger.warning("Error loading %s: %s", self.path, ex)

    def save(self, data):
        """Pickle and save data to the cache item.

        Args:
            data: Object to pickle and save
        """
        logger.debug("saving %s", self.path)


        with self.path.open("wb") as file:
            self.pickler.dump(data, file)

    def try_save(self, data):
        """Pickle and save data to the cache item, ignoring errors.

        Args:
            data: Object to pickle and save
        """
        try:
            self.save(data)
        except Exception as ex:
            logger.warning("Error saving %s: %s", self.path, ex)
