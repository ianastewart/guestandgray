from django.core.management.base import BaseCommand, CommandError
import os
from shutil import copyfile
from pathlib import Path
from django.contrib.auth.models import User
from shop.models import Item
from PIL import Image


class Imagine():

    def __init__(self):
        self.used_count = 0
        self.source ="H:/Large Images/"
        self.target = "H:/Used Images/"
        self.name_dict = {}

    def load(self):
        self.images = os.listdir(self.source)
        self.images.sort()
        self.items = Item.objects.all().order_by("ref")

    def clean(self):
        i = 0
        for name in self.images:
            changed, new_name = self.sanitize(name)
            if changed:
                self.name_dict[new_name] = name
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

    def search_local(self, ref, index, copy=False):
        """ Search 10 before and 10 after image for variant """
        print(ref)
        for i in range(index - 10, index + 10):
            if ref in self.images[i]:
                if i == index:
                    print("Primary", self.images[i])
                    if copy:
                        self.copy(self.images[i])
                    self.used_count += 1
                else:
                    print("Variant", self.images[i])
                    if copy:
                        self.copy(self.images[i])
                    self.used_count += 1
        print("----")

    def copy(self, name):
        if name in self.name_dict:
            name = self.name_dict[name]
        copyfile(self.source + name, self.target + name)

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

def open_image(path=None):
    if not path:
        path = "H:\Large Images\W307c.JPG"
    im = Image.open(path)
    return im

def save_image(im):
    name = im.filename.replace("Large Images", "Test images")
    im.save(name + "-web_maximum.JPG", quality="web_maximum")
    im.save(name + "-web_very_high.JPG", quality="web_very_high")
    im.save(name + "-web_high.JPG", quality="web_high")
    im.save(name + "-web_medium.JPG", quality="web_medium")
    im.save(name + "-web_low.JPG", quality="web_low")
    im.save(name + "-high.JPG", quality="high")
    im.save(name + "-web_high.JPG", quality="maximum")

class Command(BaseCommand):
    help = "Analyse images"

    def handle(self, *args, **options):
        im = Imagine()
        im.load()
        im.clean()
        im.item_update()


