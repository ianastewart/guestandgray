# set_item_names command
from django.core.management.base import BaseCommand
from shop.models import Item
from decimal import *


class Command(BaseCommand):
    help = "Convert integer price to decimal price"

    def handle(self, *args, **options):
        items = Item.objects.all()
        count = 0
        try:
            for item in items:
                item.sale_price = Decimal(item.price) / 100
                count += 1
                item.save()
        except Exception as e:
            self.stdout.write(f"Exception: {e}")
        self.stdout.write(f"Processed {count} of {len(items)} items")
