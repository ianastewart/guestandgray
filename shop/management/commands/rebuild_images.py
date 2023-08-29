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

    help = "Creates wagtail custom images for all items"

    def handle(self, *args, **options):
        originals_path = os.path.join(settings.MEDIA_ROOT, "original_images")
        originals_list = os.listdir(originals_path)
        collection = Collection.objects.filter(name="Shop images").first()
        if not collection:
            print("Please create the 'Shop images' collection")
            return 1
        Photo.objects.all().delete()
        for image in originals_list:
            Photo.objects.create(title=image)
        print(Photo.objects.count(), " photos to process")

        Item.objects.all().update(image_id=None)
        CustomImage.objects.all().delete()
        CustomRendition.objects.all().delete()
        count = 0
        not_found = 0
        created = 0
        for item in Item.objects.all():
            count += 1
            name = item.ref
            name_jpg = item.ref + ".jpg"
            name_crop = item.ref + "-Crop.jpg"
            photos = Photo.objects.filter(title__istartswith=name).order_by("title")
            if len(photos) == 0:
                print(name, "not found")
                not_found += 1
            else:
                # Identify the primary image
                # Priority is name.jpg or name-Crop.jpg or shortest image name
                primary = None
                for photo in photos:
                    if photo.title == name_jpg:
                        primary = photo
                        break
                    elif photo.title == name_crop and primary is None:
                        primary = photo
                if not primary:
                    min = 100
                    for photo in photos:
                        if not photo.title[len(name)].isdigit():
                            if len(photo.title) < min:
                                min = len(photo.title)
                                primary = photo
                # Create all images linked to item and link primary image
                for photo in photos:
                    if not photo.title[len(name)].isdigit():
                        path = os.path.join("original_images", photo.title)
                        new_image = CustomImage.objects.create(
                            file=path,
                            title=item.ref + " " + item.name,
                            collection_id=collection.id,
                            uploaded_by_user=None,
                            item=item,
                        )
                        created += 1
                        if photo == primary:
                            item.image = new_image
                            item.save()
        print(f"Created {created} images from {count} items, {not_found} not found")
