# clean items that have a space in their ref
from django.db.models import Field
from django.core.management.base import BaseCommand
from shop.models import Item


class Command(BaseCommand):
    help = "Set null prices to 0 and minimum price to sale price if missing"

    def handle(self, *args, **options):
        Item.objects.filter(sale_price__isnull=True).update(sale_price=0)
        Item.objects.filter(cost_price__isnull=True).update(cost_price=0)
        Item.objects.filter(restoration_cost__isnull=True).update(restoration_cost=0)
        Item.objects.filter(minimum_price__isnull=True).update(minimum_price=0)
        for item in Item.objects.filter(sale_price__gt=0, minimum_price=0):
            item.minimum_price = item.sale_price
            item.save()
