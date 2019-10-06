# set_item_names command
from django.core.management.base import BaseCommand
from shop.models import Item
from shop.truncater import truncate


class Command(BaseCommand):
    help = "Creates item names using smart truncation of descriptions"

    def handle(self, *args, **options):
        items = Item.objects.all()
        count = 0
        try:
            for item in items:
                item.name = truncate(item.description)
                count += 1
                item.save()
        except Exception as e:
            self.stdout.write(f"Exception: {e}")
        self.stdout.write(f"Names were set for {count} of {len(items)} items")
