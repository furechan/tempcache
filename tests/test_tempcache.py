""" tempcache tests """

import os
import shutil
import base64
import pytest

from tempcache import TempCache


@pytest.fixture
def cache():
    cache = TempCache()

    assert cache.path.name == "tempcache"

    if cache.path.exists():
        shutil.rmtree(cache.path)

    return cache


def sample_data(prefix="sample", *, size=32):
    data = os.urandom(size)
    data = base64.b64encode(data)
    data = data.decode("utf-8")
    result = prefix + "-" + data
    return result


def test_cache_item(cache):
    key = ("some", "composite", "key")
    value = ("some", "composite", "value")

    item = cache.item_for_key(key)

    assert item is not None

    item.save(value)

    res = item.load()

    assert res == value

    count = cache.clear_items(all_items=True)

    assert count == 1


def test_cache_result(cache):
    res = cache.cache_result(sample_data)

    assert res == cache.cache_result(sample_data, "sample")
    assert res != cache.cache_result(sample_data, "other")

    count = cache.clear_items(all_items=True)

    assert count == 2


def test_cache_wrapper(cache):
    wrapper = cache(sample_data)

    res1 = wrapper("wrapper")
    res2 = wrapper("wrapper")

    assert res1 == res2

    count = cache.clear_items(all_items=True)

    assert count == 1
