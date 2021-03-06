from django.core.management.base import BaseCommand, CommandError
from shop.import_helper import load_image, delete_all
from shop.models import Item, CustomImage
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Adds images to objects"

    def handle(self, *args, **options):
        user = User.objects.all().first()
        delete_all(CustomImage)  # deletes original_images too!
        items = Item.objects.all()
        count = 0
        max = len(items)
        image_count = 0
        not_found = 0
        threshold = 10
        i = 0
        try:
            for item in items:
                loaded = load_image(item, user)
                count += 1
                if loaded:
                    image_count += 1
                else:
                    not_found += 1
                i += 1
                if i >= threshold:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{count} of {max}, Images: {image_count}, Not Found: {not_found}"
                        )
                    )
                    i = 0

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Import images error: {str(e)} item = {item.name}")
            )
            return False
