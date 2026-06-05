# set_categories command
from django.core.management.base import BaseCommand, CommandError
from shop.models import Item, Category


class Command(BaseCommand):
    help = "Creates category images from objects"

    def handle(self, *args, **options):
        """
        Create fixed top level categories under root catalogue
        Process all objects assigning the category derived from the category_text field
        Create new categories under the top level categories according to simple matching rules
        :return: count of assigned objects and count of object without category
        """
        # Category.objects.all().delete()
        # get = lambda node_id: Category.objects.get(pk=node_id)
        # root = Category.add_root(name="Catalogue")
        # chinese = get(root.pk).add_child(name="Chinese")
        # japanese = get(root.pk).add_child(name="Japanese")
        # european = get(root.pk).add_child(name="European")
        # pottery = european.add_child(name="Pottery")
        # pottery.add_child(name="English Pottery")
        # pottery.add_child(name="Italian Pottery")
        # pottery.add_child(name="Spanish Pottery")
        # pottery.add_child(name="French/German Pottery")
        # other = get(root.pk).add_child(name="Other")
        # objects = Item.objects.all()

        # for item in objects:
        #     if item.category_text:
        #         parts = item.category_text.split("|")
        #         china = False
        #         japan = False
        #         europe = False
        #         key = parts[0]
        #         if "Chinese" in key:
        #             key = key[8:]
        #             china = True
        #         elif "Japanese" in key:
        #             key = key[9:]
        #             japan = True
        #         elif "European Pottery" in key:
        #             key = parts[1]
        #             p = key.find(" Page")
        #             if p > 0:
        #                 key = key[:p]
        #         elif "European" in key:
        #             key = key[9:]
        #             europe = True
        #         try:
        #             cat = Category.objects.get(name=key)
        #         except Category.DoesNotExist:
        #             if china:
        #                 cat = get(chinese.pk).add_child(name=key)
        #             elif japan:
        #                 cat = get(japanese.pk).add_child(name=key)
        #             elif europe:
        #                 cat = get(european.pk).add_child(name=key)
        #             elif "Dutch" in key:
        #                 cat = get(european.pk).add_child(name=key)
        #             else:
        #                 cat = get(other.pk).add_child(name=key)
        #         item.category_id = cat.id
        #         item.save()
        #         assigned += 1
        #     else:
        #         empty += 1

        # Assign category image
        assigned = 0
        empty = 0
        no_image = 0
        top_cats = Category.objects.get(name="Catalogue").get_children()
        for top_cat in top_cats:
            for cat in top_cat.get_children():
                objects = cat.item_set.filter(image__isnull=False)
                if objects:
                    cat.image = objects[0].image
                    cat.save()
                    if not top_cat.image:
                        top_cat.image = cat.image
                        top_cat.save()
                else:
                    for cat1 in cat.get_children():
                        objects = cat1.item_set.filter(image__isnull=False)
                        if objects:
                            cat1.image = objects[0].image
                            cat1.save()
                            if not cat.image:
                                cat.image = cat1.image
                                cat.save()
                            if not top_cat.image:
                                top_cat.image = cat.image
                                top_cat.save()
                        else:
                            self.stdout.write(f"No image for {cat.name}")
                            no_image += 1
        self.stdout.write(
            f"Assigned category to {assigned} objects. {empty} had no category."
        )
