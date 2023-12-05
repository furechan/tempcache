"""Caching Utilitites using Temporary files"""

import re
import time
import pickle
import inspect
import logging
import hashlib
import tempfile
import functools

import datetime as dt

from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_PREFIX = "tempcache"
DEFAULT_MAX_AGE = 24 * 60 * 60 * 7


class CacheItem:
    """Cache Item"""

    def __init__(self, path, pickler=None):
        """Cache Item.

        Args:
            path : path of the item
            pickler (optional) : curtom pickler module
        """
        if isinstance(path, str):
            path = Path(path).resolve()
        if pickler is None:
            pickler = pickle

        self.path = path
        self.pickler = pickler

    def __str__(self):
        return self.path.name

    def exists(self):
        """whether item exists"""
        return self.path.exists()

    def older_then(self, whence):
        """whether item is older than specific time"""
        if isinstance(whence, dt.datetime):
            when = whence.timestamp()

        try:
            mtime = self.path.stat().st_mtime
            return mtime < whence
        except FileNotFoundError:
            return False

    def modified_since(self, whence):
        """whether item has been modified since specific time"""
        if isinstance(whence, dt.datetime):
            when = whence.timestamp()

        try:
            mtime = self.path.stat().st_mtime
            return mtime > whence
        except FileNotFoundError:
            return False

    def current(self, max_age=None):
        """whether item is current"""
        if max_age is None:
            return self.exists()

        if max_age >= 0:
            return self.modified_since(time.time() - max_age)

        raise ValueError(f"Invalid max_age {max_age}")

    def delete(self):
        """delete item"""
        logger.debug(f"deleting {self}")

        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
        except PermissionError:
            pass

    def load(self):
        """load item contents"""
        logger.debug(f"loading {self}")

        with self.path.open("rb") as file:
            return self.pickler.load(file)

    def save(self, data):
        """save item contents"""
        logger.debug(f"saving {self}")

        with self.path.open("wb") as file:
            self.pickler.dump(data, file)


class TempCache:
    """Temporary File Cache Utility"""

    def __init__(self, prefix=DEFAULT_PREFIX, *,
                 source: str = None,
                 max_age: int = None,
                 pickler=None,
                 ):
        """Temporary File Cache Utility.

        Args:
            prefix : prefix to uniquely identify cache items like a package name
            source (optional) : extra source information like __file__
                used to further differentiate key hashes
            pickler (optional) : custom pickler module like cloudpickle
            max_age (optional) : maximum age in seconds
        """

        if max_age is None:
            max_age = DEFAULT_MAX_AGE

        if not max_age or max_age <= 0:
            raise ValueError(f"Invalid max_age {max_age!r}")

        if pickler is None:
            pickler = pickle

        folder = Path(tempfile.gettempdir())
        pattern = self.make_pattern(prefix=prefix)

        self.folder = folder
        self.prefix = prefix
        self.source = source
        self.pickler = pickler
        self.max_age = max_age
        self.pattern = pattern

    @staticmethod
    def make_pattern(prefix=DEFAULT_PREFIX):
        """create filename pattern from prefix"""

        if not isinstance(prefix, str):
            raise ValueError(f"Invalid prefix {prefix!r}")

        if re.search(r"\s|[/\\]", prefix):
            raise ValueError(f"Invalid prefix {prefix!r}")

        pattern = prefix + "-{digest}.tmp"

        return pattern

    def cache_item(self, path):
        """cache item factory"""
        return CacheItem(path, pickler=self.pickler)

    def get_expiry(self):
        """default expiry time"""

        expiry = time.time() - self.max_age
        return expiry

    def items(self):
        """iterate over items"""

        pattern = self.pattern.format(digest="*")

        for file in self.folder.glob(pattern):
            yield self.cache_item(file)

    def clear_items(self, all_items=False):
        """clear expired items"""

        count = 0
        expiry = self.get_expiry()
        for item in self.items():
            if all_items or item.older_then(expiry):
                item.delete()
                count += 1

        return count

    def item_for_digest(self, digest):
        """cache item for digest"""

        fname = self.pattern.format(digest=digest)
        path = self.folder.joinpath(fname)
        item = self.cache_item(path)

        # delete expired item to enforce expiry
        expiry = self.get_expiry()
        if item.older_then(expiry):
            item.delete()

        return item

    def item_for_key(self, key):
        """cache item for key"""

        hash = hashlib.md5()

        if self.source is not None:
            data = self.source.encode("utf-8")
            hash.update(data)

        data = self.pickler.dumps(key)
        hash.update(data)

        digest = hash.hexdigest()

        return self.item_for_digest(digest)

    def item_for_task(self, func, args, kwargs):
        """cache item for task"""

        funcname = f"{func.__module__}.{func.__qualname__}"

        signature = inspect.signature(func)
        params = signature.bind(*args, **kwargs)
        params.apply_defaults()

        key = (funcname, params)

        return self.item_for_key(key)

    def cache_result(self, func, *args, **kwargs):
        """return cached result if found or else invoke function"""

        item = self.item_for_task(func, args, kwargs)

        if item.exists():
            return item.load()

        result = func(*args, **kwargs)

        item.save(result)

        return result

    def __call__(self, func):
        """use instance as decorator to create a cached function wrapper"""

        @functools.wraps(func)
        def cached_func(*args, **kwargs):
            return self.cache_result(func, *args, **kwargs)

        return cached_func()
