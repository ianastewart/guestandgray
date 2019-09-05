# set_categories command
from django.core.management.base import BaseCommand, CommandError
from shop.models import Object, Category


class Command(BaseCommand):
    help = "Creates category structure from objects"

    def handle(self, *args, **options):
        """
        Create fixed top level categories under root catalogue
        Process all objects assigning the category derived from the category_text field
        Create new categories under the top level categories according to simple matching rules
        :return: count of assigned objects and count of object without category
        """
        Category.objects.all().delete()
        get = lambda node_id: Category.objects.get(pk=node_id)
        # top level categories
        root = Category.add_root(name="Catalogue")
        chinese = get(root.pk).add_child(name="Chinese")
        japanese = get(root.pk).add_child(name="Japanese")
        european = get(root.pk).add_child(name="European")
        other = get(root.pk).add_child(name="Other")
        objects = Object.objects.all()
        assigned = 0
        empty = 0
        created = {}
        for item in objects:
            if item.category_text:
                sep = item.category_text.find("|")
                if sep > 0:
                    key = item.category_text[0:sep]
                else:
                    key = item.category_text
                cat_id = created.get(key, None)
                if not cat_id:
                    self.stdout.write(f"Creating category: {key}")
                    if "Chinese" in key:
                        cat = get(chinese.pk).add_child(name=key[8:])
                    elif "Japanese" in key:
                        cat = get(japanese.pk).add_child(name=key[9:])
                    elif "European" in key:
                        cat = get(european.pk).add_child(name=key[9:])
                    elif "Dutch" in key:
                        cat = get(european.pk).add_child(name=key)
                    else:
                        cat = get(other.pk).add_child(name=key)
                    created[key] = cat.id
                    cat_id = cat.id
                item.new_category_id = cat_id
                item.save()
                assigned += 1
            else:
                empty += 1
        # Assign category image
        no_image = 0
        top_cats = Category.objects.get(name="Catalogue").get_children()
        for top_cat in top_cats:
            for cat in top_cat.get_children():
                objects = cat.object_set.filter(image__isnull=False)
                if objects:
                    cat.image = objects[0].image
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
