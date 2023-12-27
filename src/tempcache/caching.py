""" Caching Utilitites using Temporary files """

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

DEFAULT_NAME = "tempcache"
DEFAULT_MAX_AGE = 24 * 60 * 60 * 7

FILE_PATTERN = "{digest}.tmp"
NAME_PATTERN = r"(^[A-Za-z_][A-Za-z0-9_]*)(\.[A-Za-z_][A-Za-z0-9_]*)*$"


# MAYBE create a try_load and try_save that catch exceptions ?

def check_name(name):
    if name is None:
        raise ValueError("Name must be a string!")

    if not re.fullmatch(NAME_PATTERN, name):
        raise ValueError(f"Invalid name {name!r}")


class CacheItem:
    """ Cache Item """

    def __init__(self, path, *, pickler=None):
        """
        Cache Item.

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
        """ whether item exists """
        return self.path.exists()

    def older_than(self, whence):
        """ whether item is older than specific time """
        if isinstance(whence, dt.datetime):
            whence = whence.timestamp()

        try:
            mtime = self.path.stat().st_mtime
            return mtime < whence
        except FileNotFoundError:
            return False

    def modified_since(self, whence):
        """ whether item has been modified since specific time """
        if isinstance(whence, dt.datetime):
            whence = whence.timestamp()

        try:
            mtime = self.path.stat().st_mtime
            return mtime > whence
        except FileNotFoundError:
            return False

    def current(self, max_age=None):
        """ whether item is current """
        if max_age is None:
            return self.exists()

        if max_age >= 0:
            return self.modified_since(time.time() - max_age)

        raise ValueError(f"Invalid max_age {max_age}")

    def delete(self):
        """ delete item """
        logger.debug(f"deleting {self}")

        try:
            self.path.unlink()
        except (FileNotFoundError, PermissionError):
            pass

    def load(self):
        """ load item contents """
        logger.debug(f"loading {self}")

        with self.path.open("rb") as file:
            return self.pickler.load(file)

    def save(self, data):
        """ save item contents """
        logger.debug(f"saving {self}")

        # (re)create parent folder if needed
        self.path.parent.mkdir(exist_ok=True)

        with self.path.open("wb") as file:
            self.pickler.dump(data, file)


class TempCache:
    """ Temporary File Cache Utility """

    def __init__(self,
                 name: str = DEFAULT_NAME, *,
                 source: str = None,
                 max_age: int = None,
                 pickler=None,
                 ):
        """
        Temporary File Cache Utility.

        Args:
            name : name of cachig folder under tempdir (default 'tempcache')
            source (optional) : extra source information like __file__
                used to further differentiate key hashes
            pickler (optional) : custom pickler module like cloudpickle
            max_age (optional) : maximum age in seconds
        """

        check_name(name)

        if max_age is None:
            max_age = DEFAULT_MAX_AGE

        if not max_age or max_age <= 0:
            raise ValueError(f"Invalid max_age {max_age!r}")

        if pickler is None:
            pickler = pickle

        tempdir = Path(tempfile.gettempdir())
        path = tempdir.joinpath(name)

        self.name = name
        self.path = path
        self.source = source
        self.pickler = pickler
        self.max_age = max_age

    def __repr__(self):
        return f"TempCache({self.name!r})"

    def cache_item(self, path):
        """ cache item factory """
        return CacheItem(path, pickler=self.pickler)

    def get_expiry(self):
        """ default expiry time """

        expiry = time.time() - self.max_age
        return expiry

    def items(self):
        """ iterate over items """

        pattern = FILE_PATTERN.format(digest="*")

        for file in self.path.glob(pattern):
            yield self.cache_item(file)

    def clear_items(self, all_items=False):
        """ clear expired items """

        count = 0
        expiry = self.get_expiry()
        for item in self.items():
            if all_items or item.older_than(expiry):
                item.delete()
                count += 1

        return count

    def item_for_digest(self, digest):
        """ cache item for digest. deletes item if expired """

        fname = FILE_PATTERN.format(digest=digest)
        path = self.path.joinpath(fname)
        item = self.cache_item(path)

        # delete expired item to enforce expiry
        expiry = self.get_expiry()
        if item.older_than(expiry):
            item.delete()

        return item

    def item_for_key(self, key):
        """ cache item for key. deletes item if expired """

        hash = hashlib.md5()

        if self.source is not None:
            data = self.source.encode("utf-8")
            hash.update(data)

        data = self.pickler.dumps(key)
        hash.update(data)

        digest = hash.hexdigest()

        return self.item_for_digest(digest)

    def item_for_task(self, func, args, kwargs):
        """ cache item for task. deletes item if expired """

        funcname = f"{func.__module__}.{func.__qualname__}"

        signature = inspect.signature(func)
        params = signature.bind(*args, **kwargs)
        params.apply_defaults()

        key = (funcname, params)

        return self.item_for_key(key)

    def cache_result(self, func, *args, **kwargs):
        """ return cached result if found or else invoke function """

        item = self.item_for_task(func, args, kwargs)

        if item.exists():
            return item.load()

        result = func(*args, **kwargs)

        item.save(result)

        return result

    def __call__(self, func):
        """ use instance as decorator to create a cached function wrapper """

        @functools.wraps(func)
        def cached_func(*args, **kwargs):
            return self.cache_result(func, *args, **kwargs)

        return cached_func()
