import logging
import requests
import shutil
from keyvaluestore.utils import get_value_for_key, set_key_value
from django.shortcuts import render, redirect
from import_export import resources
from import_export.fields import Field
from treebeard.mp_tree import MP_Node
from tablib import Dataset
from .models import Item, Category, CustomImage

logger = logging.getLogger(__name__)


class ObjectResource(resources.ModelResource):
    class Meta:
        model = Item
        fields = (
            "id",
            "name",
            "description",
            "ref",
            "price",
            "image_file",
            "category_text",
        )

    name = Field(attribute="name", column_name="Short Description")
    description = Field(attribute="description", column_name="Full Description")
    ref = Field(attribute="ref", column_name="Product reference")
    price = Field(attribute="price", column_name="Price")
    image_file = Field(attribute="image_file", column_name="Detail URL")
    category_text = Field(attribute="category_text", column_name="Section Text")


def import_objects(excel_file):

    delete_all(Item)
    delete_all(Category)
    delete_all(CustomImage)
    set_status("Reading Excel file")
    object_resource = ObjectResource()
    dataset = Dataset()
    dataset.load(excel_file.read())
    set_status("Checking file", max=dataset.height)
    result = object_resource.import_data(dataset, dry_run=True)
    if result.has_errors():
        try:
            error = result.rows[0].errors[0].error
        except:
            error = "Not known"
        set_status(f"Error: {error}", done=True)
        return False
    else:
        set_status("Loading database", max=dataset.height)
        object_resource.import_data(dataset, dry_run=False)  # Actually import now
        set_status("Objects loaded", max=dataset.height, done=True)
    return True


def set_status(text, max=0, count=0, empty=0, categories=0, image_count=0, done=False):
    if max > 0:
        percent = int(count / max * 100)
    else:
        percent = 0
    set_key_value(
        "PROGRESS",
        {
            "text": text,
            "percent": percent,
            "max": max,
            "count": count,
            "empty": empty,
            "categories": categories,
            "image_count": image_count,
            "done": done,
        },
    )


def process_images(user):

    # delete all using workaround for sqlite limit
    set_status("Clearing images")
    delete_all(CustomImage)  # deletes original_images too!
    items = Item.objects.all()
    count = 0
    max = len(items)
    image_count = 0
    not_found = 0
    threshold = 10
    i = 0
    set_status("Processing images", max)
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
                set_status(
                    "Processing images",
                    max,
                    count,
                    empty=not_found,
                    image_count=image_count,
                )
                i = 0
        set_status(
            "Done", max, count, empty=not_found, image_count=image_count, done=True
        )
        return True
    except Exception as e:
        logger.error(f"Import images error: {str(e)} object = {item.name}")
        return False


def load_image(item, user, collection=None):
    """
    Try to load the image for an object.
    Check if file already in /images first
    if it exists, copy to original_images, create a CustomImage cross linked to the object and return True
    else return False
    """
    collection_id = collection.id if collection else 1
    if item.image_file:
        if "http" not in item.image_file:
            # from excel file
            base_url = "https://chinese-porcelain-art.com/acatalog/"
            name = item.image_file.split("\\")
            url = base_url + name[1]
            file_name = name[1].split(".")[0] + ".jpg"
        else:
            # called by scrape process
            parts = item.image_file.split("/")
            file_name = parts[len(parts) - 1]
            url = item.image_file
        images_path = "images/" + file_name
        media_path = "media/original_images/" + file_name
        loaded = False
        try:
            shutil.copy(images_path, media_path)
            loaded = True
        except FileNotFoundError:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(media_path, "wb") as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                loaded = True
            del response
        if loaded:
            new_image = CustomImage.objects.create(
                file="original_images/" + file_name,
                title=item.name,
                collection_id=collection_id,
                uploaded_by_user=user,
                item=item,
            )
            item.image = new_image
            item.save()
            return True
    item.image = None
    item.save()
    return False


def set_image_status(max=0, count=0, not_found=0, done=False):
    if max > 0:
        percent = int(count / max * 100)
    else:
        percent = 0
    set_key_value(
        "IMAGES",
        {
            "percent": percent,
            "max": max,
            "count": count,
            "not_found": not_found,
            "done": done,
        },
    )


def delete_all(cls):
    """ For sqlite that cannot handle 1000 parameters """
    while cls.objects.count():
        ids = cls.objects.values_list("pk", flat=True)[:500]
        cls.objects.filter(pk__in=ids).delete()
