from django.core.management.base import BaseCommand

from shop.models import Item


class Command(BaseCommand):
    help = "Remove duip refs with #"

    def handle(self, *args, **options):
        items = Item.objects.filter(ref__startswith="#")
        for item in items:
            ref1 = item.ref[1:]
            dup = Item.objects.filter(ref=ref1).first()
            if dup:
                dup.delete()
