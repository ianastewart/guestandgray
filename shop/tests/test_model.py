import pytest
from shop.models import ItemRef


def test_itemref_generation(db):
    # default on empty database = Z1
    assert ItemRef.get_next(increment=False) == "Z1"
    assert ItemRef.get_next() == "Z1"
    assert ItemRef.get_next() == "Z2"
    ItemRef.reset()
    assert ItemRef.get_next() == "Z1"
    ItemRef.reset(prefix="Q", number=999)
    assert ItemRef.get_next() == "Q999"
    assert ItemRef.increment("Q999") == "Q1000"
