import pytest
from shop.cat_tree import *
from shop.models import Item


def test_tree(fix_tree):
    t = tree()
    print_tree()


@pytest.fixture()
def fix_tree(db):
    alphabet = "ABCDEFGHIJKLMNOP"
    a = 0
    root = Category.add_root(name="Catalogue")
    for i in range(5):
        node = root.add_child(name=alphabet[a], sequence=i + 1)
        a += 1
        if i in [1, 3]:
            for j in range(3):
                node.add_child(name=alphabet[a])
                a += 1


class Move:
    def test_tree_move(self):
        assert False
