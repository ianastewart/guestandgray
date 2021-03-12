"""
All Code for managaging the tree of Categories
A category is an instance of MPnode
See https://django-treebeard.readthedocs.io/en/latest/api.html
"""
import json
from shop.models import Category
from django.shortcuts import reverse
from django.db import transaction


@transaction.atomic
def tree_move(node_id, target_id, previous_id, inside):
    """
    Action a jqTree move in the database

    """
    node = Category.objects.get(id=node_id)
    target = Category.objects.get(id=target_id)
    if inside:
        # If inside, add as first node of the target
        # Renumber target's children from 2 and insert node in pos 1
        seq = 2
        for child in target.get_children():
            if child.id != node.id:
                child.sequence = seq
                child.save()
                seq += 1
        node.sequence = 1
        node.save()
        node = Category.objects.get(id=node.id)
        node.move(target, "sorted-child")
        # if moved from a different parent, renumber old parent's children
        if previous_id != target_id:
            seq = 1
            for child in Category.objects.get(id=previous_id).get_children():
                child.sequence = seq
                child.save()
                seq += 1
    else:
        # Add as sibling of target after target
        # Renumber nodes after new position
        if target.get_parent() == node.get_parent():
            next = 1
            for child in target.get_siblings().order_by("sequence"):
                if child.id != node.id:
                    if child.id == target.id:
                        child.sequence = next
                        next += 1
                        node.sequence = next
                        node.save()
                    else:
                        child.sequence = next
                    next += 1
                    child.save()
            target = Category.objects.get(id=target.id)
            node.move(target, "sorted-sibling")


def tree(admin=False):
    """
    Create a dictionary representation of the Category tree
    """
    node = Category.objects.get(name="Catalogue")
    if node.sequence == 0:
        sequence_tree()
    dict = node_dict(node, admin)
    kids = descend(node, admin)
    if kids:
        dict["children"] = kids
    return dict


def tree_json():
    """ Tree in jqTree format """
    return "[" + json.dumps(tree(admin=True)) + "]"


def node_dict(node, admin):
    """ Define content of a tree node in the dictionary """
    dict = {"id": node.id}
    if admin:
        link = reverse("category_detail", kwargs={"pk": node.pk})
    else:
        link = "/"
        # link = reverse("public_catalogue", kwargs={"slugs": node.slug})
    dict["link"] = link
    dict["text"] = f"node.name {node.item_set.count()}"
    dict["leaf"] = node.is_leaf()
    shop = node.shop_count()
    archive = node.archive_count()
    items = shop + archive
    dict["items"] = items
    count_text = (
        f'<span class="small">(Shop: {shop}, Archive: {archive})</span>'
        if items > 0
        else f""
    )
    if not node.is_leaf() and items > 0:
        count_text = f'<span class="text-danger">{count_text}</span>'
    dict[
        "name"
    ] = f'<b>{node.name}</b> <i>{count_text}</i> <a class="btn btn-outline-info btn-sm py-0" href="{link}">View</a>'
    return dict


def descend(parent, admin):
    """ Recursively expand the tree """
    children = parent.get_children().order_by("sequence", "name")
    if children:
        kids = []
        for node in children:
            dict = node_dict(node, admin)
            next_gen = descend(node, admin)
            if next_gen:
                dict["children"] = next_gen
            kids.append(dict)
        return kids
    return None


def sequence_tree():
    """ Initial traversal of the tree to add sequence numbers """
    node = Category.objects.get(name="Catalogue")
    node.sequence = 1
    node.save()
    sequence_kids(node)


def sequence_kids(node):
    """ Recursive function to add sequence numbers """
    kids = node.get_children().order_by("sequence", "name")
    if kids:
        seq = 1
        for kid in kids:
            kid.sequence = seq
            kid.save()
            seq += 1
            sequence_kids(kid)


def print_tree():
    node = Category.objects.get(name="Catalogue")
    print_kids(node, 1)


def print_kids(node, level):
    sp = ""
    for i in range(level):
        sp += "  "
    print(sp, node.name, node.sequence)
    for kid in node.get_children().order_by("sequence"):
        print_kids(kid, level + 1)


class Counter:
    """ Traverse a hierarchical category tree and append the total count of items under each node """

    def __init__(
        self, root, archive=False, exclude_no_image=True, exclude_not_visible=True
    ):
        self.total = 0
        self.root = root
        self.archive = archive
        self.no_image = exclude_no_image
        self.not_visible = exclude_not_visible

    def count(self):
        print("-------------------------", self.archive)
        return self._count(self.root)

    def _count(self, cat):
        # recursive count function
        items = cat.item_set.filter(archive=self.archive)
        if self.no_image:
            items = items.filter(image__isnull=False)
        if self.not_visible:
            items = items.filter(visible=True)
        total = items.count()
        child_cats = cat.get_children()
        # if self.no_image:
        #     child_cats = child_cats.filter(image__isnull=False)
        # if self.not_visible:
        #     child_cats = child_cats.filter(visible=True)
        if child_cats:
            for cat1 in child_cats:
                total += self._count(cat1)
        cat.count = total
        cat.save()
        print(f"{cat.name} {cat.count}")
        return total
