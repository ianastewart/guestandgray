from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
from django.contrib.auth.models import User
from shop.models import Item

class Command(BaseCommand):
    help = "Anayse duplicate images"

    def handle(self, *args, **options):
        numbers = list("0123456789")
        letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        normal = letters+numbers
        entries = Path("H:\Large Images")
        found = 0
        missing = 0
        for entry in entries.iterdir():
            bits = entry.name.split(".")
            name = bits[0]
            j = 0
            for i in list(name):
                if i in normal:
                    j+=1
                else:
                    root=name[:j]
                    suffix = name[j:]
                    break
            item = Item.objects.filter(ref=root).first()
            if item:
                found += 1
                #print(root, "found")
            else:
                missing += 1
                print(name, "missing")
        print(f"Found {found} Missing {missing}")

