""" tempcache  tests """

from tempcache import TempCache


def test_tempcache():
    cache = TempCache()

    cache.clear_items(all_items=True)

    key = ("some", "composite", "key")
    value = ("some", "composite", "value")

    item = cache.item_for_key(key)

    assert item is not None

    item.save(value)

    res = item.load()

    assert res == value

    count = cache.clear_items(all_items=True)

    assert count == 1
