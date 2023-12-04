""" Temp file caching utilities """

import re
import time
import pickle
import logging
import hashlib
import tempfile
import functools

import datetime as dt

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from .utils import args_with_defaults

logger = logging.getLogger(__name__)

DEFAULT_PREFIX = "tempcache"
DEFAULT_MAX_AGE = 24 * 60 * 60 * 7

class CacheItem:
    """ Cache Item """

    def __init__(self, path, pickler=None):
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

    def older_then(self, when):
        """ whether item is older than specific time """
        if isinstance(when, dt.datetime):
            when = when.timestamp()

        try:
            mtime = self.path.stat().st_mtime
            return mtime < when
        except FileNotFoundError:
            return False

    def modified_since(self, when):
        """ whether item has been modified since specific time """
        if isinstance(when, dt.datetime):
            when = when.timestamp()

        try:
            mtime = self.path.stat().st_mtime
            return mtime > when
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
        logger.debug(f"deleting {self} ...")

        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
        except PermissionError:
            pass

    def load(self):
        """ load item contents """
        logger.debug(f"loading {self} ...")

        with self.path.open("rb") as file:
            return self.pickler.load(file)

    def save(self, data):
        """ save item contents """
        logger.debug(f"saving {self} ...")

        with self.path.open("wb") as file:
            self.pickler.dump(data, file)


class TempCache:
    """ facility to cache data under the temp folder """

    def __init__(self, prefix=DEFAULT_PREFIX, *,
                 factory=CacheItem,
                 pickler=None,
                 max_age=None,
                 clear_items=False,
                 ):

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
        self.pickler = pickler
        self.max_age = max_age
        self.factory = factory
        self.pattern = pattern

        if clear_items:
            with ThreadPoolExecutor() as worker:
                worker.submit(self.clear_items)

    @staticmethod
    def make_pattern(prefix=DEFAULT_PREFIX):
        """ create pattern from prefix """

        if not isinstance(prefix, str):
            raise ValueError(f"Invalid prefix {prefix!r}")

        if re.search(r"\s|[/\\]", prefix):
            raise ValueError(f"Invalid prefix {prefix!r}")

        pattern = prefix + "-{digest}.tmp"

        return pattern

    def get_expiry(self):
        """ expiry time """

        expiry = time.time() - self.max_age
        return expiry

    def items(self):
        """ items with same prefix """

        pattern = self.pattern.format(digest="*")

        for file in self.folder.glob(pattern):
            yield self.factory(file)

    def clear_items(self, all_items=False):
        """ clear expired items with same prefix """

        count = 0
        expiry = self.get_expiry()
        for item in self.items():
            if all_items or item.older_then(expiry):
                item.delete()
                count += 1

        return count

    def item_for_digest(self, digest):
        """ cache item for digest """

        fname = self.pattern.format(digest=digest)
        path = self.folder.joinpath(fname)
        item = self.factory(path, pickler=self.pickler)

        # delete expired item to enforce expiry
        expiry = self.get_expiry()
        if item.older_then(expiry):
            item.delete()

        return item

    def item_for_key(self, key):
        """ cache item for key """

        data = self.pickler.dumps(key)
        digest = hashlib.md5(data).hexdigest()

        return self.item_for_digest(digest)

    def item_for_task(self, func, args, kwargs):
        """ cache item for task """

        args, kwargs = args_with_defaults(func, args, kwargs)

        key = (func.__name__, args, kwargs)
        print("key", key)
        data = self.pickler.dumps(key)
        digest = hashlib.md5(data).hexdigest()

        return self.item_for_digest(digest)

    def cache_result(self, func, *args, **kwargs):
        """ returns cached result if found or else invokes function """

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
