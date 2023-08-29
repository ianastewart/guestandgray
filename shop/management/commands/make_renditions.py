import os

from django.conf import settings
from django.core.management.base import BaseCommand
from wagtail.models import Collection

from shop.models import CustomImage, CustomRendition, Item, Photo


class Command(BaseCommand):
    """
    Initial creation of Wagtail images from source images that have been uploaded to original_images
    This completely replaces all item images and nukes all custom images
    """

    help = "Create standard renditions for all items"

    def handle(self, *args, **options):
        image_ids = Item.objects.all().values_list("image_id", flat=True)
        count = 0
        batch = 0
        for id in image_ids:
            if id:
                image = CustomImage.objects.get(id=id)
                image.get_rendition("max-100x100")
                image.get_rendition("max-250x250")
                image.get_rendition("max-1000x1000")
                count += 1
                batch += 1
                if batch == 100:
                    print(f"{count} of {len(image_ids)}")
                    batch = 0
        print("done")
