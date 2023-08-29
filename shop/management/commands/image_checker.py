import os

from django.conf import settings
from django.core.management.base import BaseCommand
from wagtail.models import Collection

from shop.models import CustomImage, CustomRendition, Item, Photo


class Command(BaseCommand):
    """
    Scan every item, and identify any where the image is in error
    """

    help = "Check items for image errors"

    def handle(self, *args, **options):
        no_primary = (
            Item.objects.filter(image_id__isnull=True, state=1)
            .order_by("ref")
            .values_list("ref", flat=True)
        )
        for ref in no_primary:
            print(ref, "no image")

        image_ids = (
            Item.objects.filter(image_id__isnull=False)
            .order_by("ref")
            .values_list("image_id", flat=True)
        )
        count = 0
        batch = 0
        for id in image_ids:
            image = CustomImage.objects.get(id=id)
            thumb = image.get_rendition("max-100x100")
            path = "media/" + thumb.file.name
            count += 1
            if not os.path.exists(path):
                print(image.item.ref, "Cannot create thumbnail")
                # try:
                #     l = len(image.file)
                # except Exception as e:
                #     print("Image", image.item.id, image.item.ref, str(e))
                # try:
                #     image.get_rendition("max-250x250")
                # except Exception as e:
                #     print("Rendition", image.item.id, image.item.ref, str(e))
                # count += 1
                # batch += 1
                # if batch == 100:
                #     print(f"{count} of {len(image_ids)}")
                #     batch = 0
        print(count, "items checked")
