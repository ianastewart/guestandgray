# clean items that have a space in their ref
from django.core.management.base import BaseCommand
from shop.models import Item


class Command(BaseCommand):
    help = "Clean items that have a space in their ref"

    def handle(self, *args, **options):
        items = Item.objects.filter(ref__icontains=" ")
        count = 0
        try:
            for item in items:
                ind = item.ref.index(" ")
                item.ref = item.ref[:ind]
                item.save()
        except Exception as e:
            self.stdout.write(f"Exception: {e}")
        self.stdout.write(f"Processed {count} of {len(items)} items")
