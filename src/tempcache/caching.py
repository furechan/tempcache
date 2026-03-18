"""Caching Utilities using Temporary files"""

import os
import time
import pickle
import inspect
import logging
import hashlib
import tempfile
import functools

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


    def __call__(self, func):
        """Decorator to wrap a function. See wrap()."""
        return self.wrap(func)


    def items(self):
        """Iterate over all cache file paths.

        Yields:
            Path: Each cache file found
        """
        pattern = FILE_PATTERN.format(digest="*")
        yield from self.path.glob(pattern)

    def clear_items(self, all_items=False):
        """Clear expired or all cache items.

        Args:
            all_items: If True, clear all items regardless of expiration

        Returns:
            int: Number of items cleared
        """
        count = 0
        expiry = time.time() - self.max_age

        for path in self.items():
            try:
                if all_items or path.stat().st_mtime < expiry:
                    path.unlink(missing_ok=True)
                    count += 1
            except FileNotFoundError:
                pass

        return count


    def key_digest(self, key: Any) -> str:
        """Compute hash digest for a cache key.

        Args:
            key: Cache key to hash. Must be pickle-able

        Returns:
            str: Hex digest string
        """
        hasher = hashlib.md5()

        if self.source is not None:
            hasher.update(self.source.encode("utf-8"))

        hasher.update(self.pickler.dumps(key))

        return hasher.hexdigest()

    def task_digest(self, func, args, kwargs) -> str:
        """Compute hash digest for a function call.

        The key is based on the function's module and qualified name,
        together with the bound arguments.

        Args:
            func: Function to cache
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            str: Hex digest string
        """
        funcname = f"{func.__module__}.{func.__qualname__}"

        signature = inspect.signature(func)
        params = signature.bind(*args, **kwargs)
        params.apply_defaults()

        return self.key_digest((funcname, params))


    def digest_path(self, digest: str) -> Path:
        return self.path / FILE_PATTERN.format(digest=digest)


    def try_load(self, digest: str, fallback=None):
        """Load cached data for a digest, returning fallback on miss, expiry, or error.

        Args:
            digest: Hash digest string from key_digest()
            fallback: Value to return on cache miss or error (default None)

        Returns:
            Cached object or fallback
        """
        path = self.digest_path(digest)
        expiry = time.time() - self.max_age

        try:
            if path.stat().st_mtime < expiry:
                path.unlink(missing_ok=True)
                return fallback
        except FileNotFoundError:
            return fallback

        try:
            logger.debug("Loading %s", path)
            with path.open("rb") as file:
                return self.pickler.load(file)
        except Exception as ex:
            logger.warning("Error loading %s: %s", path, ex)
            return fallback

    def try_save(self, digest: str, data):
        """Pickle and save data for a digest, ignoring errors.

        Args:
            digest: Hash digest string from key_digest()
            data: Object to pickle and save
        """
        path = self.digest_path(digest)

        try:
            logger.debug("Saving %s", path)
            with path.open("wb") as file:
                self.pickler.dump(data, file)
        except Exception as ex:
            logger.warning("Error saving %s: %s", path, ex)

    def cache_result(self, func, *args, **kwargs):
        """Get cached result or compute and cache new result.

        The cache key is based on the function's module and qualified name, together with the bound arguments.

        Args:
            func: Function to call
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            The function result (cached or fresh)
        """
        MISSING = object()
        digest = self.task_digest(func, args, kwargs)
        result = self.try_load(digest, fallback=MISSING)

        if result is MISSING:
            result = func(*args, **kwargs)
            self.try_save(digest, result)

        return result


    def wrap(self, func):
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
