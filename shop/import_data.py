import os.path
import requests
import shutil
from keyvaluestore.utils import get_value_for_key, set_key_value
from django.shortcuts import render, redirect
from django.http import JsonResponse
from import_export import resources
from import_export.fields import Field
from tablib import Dataset
from .models import Object, Category, CustomImage


class ObjectResource(resources.ModelResource):
    class Meta:
        model = Object
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


class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category
        fields = ("id", "name")


def import_objects_view(request):
    template_name = "shop/import.html"

    if request.method == "GET":
        set_status("Waiting")

    if request.method == "POST":
        delete_all(Object)
        delete_all(Category)
        delete_all(CustomImage)
        set_status("Reading file")
        object_resource = ObjectResource()
        dataset = Dataset()
        excel = request.FILES["myfile"]
        dataset.load(excel.read())
        set_status("Checking file", max=dataset.height)
        result = object_resource.import_data(
            dataset, dry_run=True
        )  # Test the data import
        if result.has_errors():
            try:
                error = result.rows[0].errors[0].error
            except:
                error = "Not known"
            set_status(f"Error: {error}", done=True)
        else:
            set_status("Loading database", max=dataset.height)
            object_resource.import_data(dataset, dry_run=False)  # Actually import now
            index_objects(request)
    return render(request, template_name, context={})


def index_objects(request):
    """
    Process imported objects
    Create or link to the associated category
    Dowload the associated image and cross link it
    """
    objects = Object.objects.all()
    max = len(objects)
    count = 0
    empty = 0
    categories = 0
    image_count = 0
    update_threshold = 50
    set_status("Processing objects", max, count, empty, categories)
    i = 0
    for item in objects:
        # Link category
        if item.category_text:
            sep = item.category_text.find("|")
            if sep > 0:
                key = item.category_text[0:sep]
            else:
                key = item.category_text
            try:
                category = Category.objects.get(name=key)
            except Category.DoesNotExist:
                categories += 1
                category = Category(name=key)
                category.save()
            item.category_id = category.id
            item.save()
        else:
            empty += 1
        count += 1
        # link image
        if load_image(item, request.user):
            image_count += 1
        i += 1
        if i >= update_threshold:
            set_status("Indexing", max, count, empty, categories, image_count)
            i = 0
    set_status("Done", max, count, empty, categories, image_count, done=True)


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
            "images": image_count,
            "done": done,
        },
    )


def import_progress_view(request):
    progress = get_value_for_key("progress")
    if progress:
        return JsonResponse(progress)
    return JsonResponse({"error": "No  key found"})


### Images ####


def import_images_view(request):
    """ Attach images to objects """
    template_name = "shop/import_images.html"
    if request.method == "POST":
        # delete all using workaround for sqlite limit
        while CustomImage.objects.count():
            ids = CustomImage.objects.values_list("pk", flat=True)[:500]
            CustomImage.objects.filter(pk__in=ids).delete()
        objects = Object.objects.all()
        count = 0
        max = len(objects)
        not_found = 0
        threshold = 10
        i = 0
        for obj in objects:
            loaded = load_image(obj, request.user)
            count += 1
            if not loaded:
                not_found += 1
            i += 1
            if i >= threshold:
                set_image_status(max, count, not_found)
                i = 0
            print(f"{obj.name} {loaded}")
    return render(request, template_name)


def import_images_progress_view(request):
    progress = get_value_for_key("IMAGES")
    if progress:
        return JsonResponse(progress)
    return JsonResponse({"error": "No  key found"})


def load_image(obj, user, collection=None):
    """
    Try to load the image for an object.
    Check if file already im media/originalimages first
    if it exists, create a CustomImage cross linked to the object and return True
    else return False
    """
    collection_id = collection.id if collection else 1
    if obj.image_file:
        base_url = "https://chinese-porcelain-art.com/acatalog/"
        name = obj.image_file.split("\\")
        url = base_url + name[1]
        file_name = name[1].split(".")[0] + ".jpg"
        local_path = "media/original_images/" + file_name
        loaded = False
        try:
            f = open(local_path, "r")
            f.close()
            loaded = True
        except FileNotFoundError:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(local_path, "wb") as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                loaded = True
            del response
        if loaded:
            new_image = CustomImage.objects.create(
                file="original_images/" + file_name,
                title=obj.name,
                collection_id=collection_id,
                uploaded_by_user=user,
                object=obj,
            )
            obj.image = new_image
            obj.save()
            return True
    obj.image = None
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


def set_category_images_view(request):
    cats = Category.objects.all()
    for cat in cats:
        objects = cat.object_set.filter(image__isnull=False)
        if objects:
            cat.image = objects[0].image
            cat.save()
    return redirect("public_catalogue")
