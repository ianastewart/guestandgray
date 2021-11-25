import os

from django.conf import settings
from django.core.management.base import BaseCommand
from wagtail.core.models import Collection

from shop.models import CustomImage, CustomRendition, Item, Photo


class Command(BaseCommand):
    """
    Scan every item, and identify any where the image is in error
    """

    help = "Check items for image errors"

    def handle(self, *args, **options):
        image_ids = (
            Item.objects.all().order_by("ref").values_list("image_id", flat=True)
        )
        count = 0
        batch = 0
        for id in image_ids:
            if id:
                image = CustomImage.objects.get(id=id)
                try:
                    l = len(image.file)
                except Exception as e:
                    print("Image", image.item.id, image.item.ref, str(e))
                try:
                    image.get_rendition("max-250x250")
                except Exception as e:
                    print("Rendition", image.item.id, image.item.ref, str(e))
                # count += 1
                # batch += 1
                # if batch == 100:
                #     print(f"{count} of {len(image_ids)}")
                #     batch = 0
        print("done")
