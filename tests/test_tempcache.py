""" tempcache tests """

import pytest
import shutil
import base64

from random import Random

from tempcache import TempCache


@pytest.fixture
def cache():
    cache = TempCache()

    assert cache.path.name == "tempcache"

    if cache.path.exists():
        shutil.rmtree(cache.path)

    return cache


def sample_data(seed=0, size=32):
    data = Random(seed).randbytes(size)
    data = base64.b64encode(data)
    data = data.decode("utf-8")
    return data


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
    assert res == cache.cache_result(sample_data, 0)
    assert res == cache.cache_result(sample_data, 0, 32)

    count = cache.clear_items(all_items=True)

    assert count == 1
