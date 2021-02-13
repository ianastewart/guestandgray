from django.core.management.base import BaseCommand, CommandError
import os
from pathlib import Path
from django.contrib.auth.models import User
from shop.models import Item


class Imagine():

    def __init__(self):
        self.used_count = 0

    def load(self):
        self.images = os.listdir("H:\Large Images")
        self.images.sort()
        self.items = Item.objects.all().order_by("ref")

    def clean(self):
        i = 0
        for name in self.images:
            changed, new_name = self.sanitize(name)
            if changed:
                self.images[i] = new_name
            i += 1

    @staticmethod
    def sanitize(name):
        changed = False
        bits = name.split(".")
        if len(bits) == 2:
            if bits[1] != "JPG":
                bits[1] = "JPG"
                changed = True
            if " (" in bits[0]:
                parts = bits[0].split(" (")
                bits[0] = parts[0] + "-" + parts[1][0]
                changed = True
            return changed, bits[0] + "." + bits[1]
        print(f"{name} IS BAD)")
        return False, name

    def search_local(self, ref, index):
        """ Search 10 before and 10 after image for variant """
        print(ref)
        for i in range(index - 10, index + 10):
            if ref in self.images[i]:
                if i == index:
                    print("Primary", self.images[i])
                    self.used_count += 1
                else:
                    print("Variant", self.images[i])
                    self.used_count += 1
        print("----")

    def item_update(self):
        self.used_count = 0
        found_count = 0
        missing_count = 0
        for item in self.items:
            # if item.image:
            #     if item.image.filename[:2] == "XX":
            #         file = item.image.filename[2:]
            #         #print (file, file in large_images)
            #     else:
            #         print("item.image.filename")
            # else:
            try:
                index = self.images.index(f"{item.ref}.JPG")
                found_count += 1
                self.search_local(item.ref, index)
            except ValueError:
                missing_count += 1
                print("Missing", item.ref)

        print(f"{len(self.items)} items processed, {found_count} images found, {missing_count} images missing")
        print(f"{self.used_count} of {len(self.images)} large images used")

    # numbers = list("0123456789")
    # letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    # normal = letters+numbers
    # entries = Path("H:\Large Images")
    # found = 0
    # missing = 0
    # for entry in entries.iterdir():
    #     bits = entry.name.split(".")
    #     name = bits[0]
    #     j = 0
    #     for i in list(name):
    #         if i in normal:
    #             j+=1
    #         else:
    #             root=name[:j]
    #             suffix = name[j:]
    #             break
    #     item = Item.objects.filter(ref=root).first()
    #     if item:
    #         found += 1
    #         #print(root, "found")
    #     else:
    #         missing += 1
    #         print(name, "missing")
    # print(f"Found {found} Missing {missing}")


class Command(BaseCommand):
    help = "Analyse images"

    def handle(self, *args, **options):
        im = Imagine()
        im.load()
        im.clean()
        im.item_update()


