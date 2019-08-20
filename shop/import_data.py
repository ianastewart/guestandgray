import requests
import shutil
from keyvaluestore.utils import get_value_for_key, set_key_value
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from import_export import resources
from import_export.fields import Field
from tablib import Dataset
from .models import Object, Category


class ObjectResource(resources.ModelResource):
    class Meta:
        model = Object
        fields = ("id", "name", "description", "ref", "price", "image_file", "category_text")

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
        set_status('Waiting')

    if request.method == "POST":
        Object.objects.all().delete()
        Category.objects.all().delete()
        set_status('Reading file')
        object_resource = ObjectResource()
        dataset = Dataset()
        excel= request.FILES["myfile"]
        dataset.load(excel.read())
        set_status('Checking file', max=dataset.height)
        result = object_resource.import_data(dataset, dry_run=True)  # Test the data import
        if result.has_errors():
            set_status('Errors', done=True)
        else:
            set_status('Loading database', max=dataset.height)
            object_resource.import_data(dataset, dry_run=False)  # Actually import now
            index_objects()
    return render(request, template_name, context={})

def index_objects():
        objects = Object.objects.all()
        max = len(objects)
        count = 0
        empty = 0
        categories = 0
        update_threshold = 50
        set_status('Indexing', max, count, empty, categories)
        i = 0
        for item in objects:
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
            i += 1
            if i >= update_threshold:
                set_status('Indexing', max, count, empty, categories)
                i = 0
        set_status('Done', max, count, empty, categories, done=True)

def set_status(text, max=0, count=0, empty=0, categories=0, done=False):
    if max > 0:
        percent =  int(count/max*100)
    else:
        percent = 0
    set_key_value('PROGRESS', {
        'text': text,
        'percent': percent,
        'max': max,
        'count': count,
        'empty': empty,
        'categories': categories,
        'done': done
    })

def import_progress_view(request):
    progress = get_value_for_key('progress')
    if progress:
        return JsonResponse(progress)
    return JsonResponse({'error': 'No  key found'})

### Images ####

def import_images_view(request):
    template_name = "shop/import_images.html"
    if request.method == 'POST':
        objects = Object.objects.all()
        count = 0
        max = len(objects)
        not_found = 0
        threshold = 10
        i = 0
        for obj in objects:
            loaded = load_image(obj)
            count += 1
            if not loaded:
                not_found += 1
            i += 1
            if i >= threshold:
                set_image_status(max, count, not_found)
                i = 0
            print (f'{obj.name} {loaded}')
    return render(request, template_name)

def import_images_progress_view(request):
    progress = get_value_for_key('IMAGES')
    if progress:
        return JsonResponse(progress)
    return JsonResponse({'error': 'No  key found'})

def load_image(obj):
    """ Load the image for an object. Return True if it is found """
    if obj.image_file:
        base_url = 'https://chinese-porcelain-art.com/acatalog/'
        name = obj.image_file.split("\\")
        url = base_url + name[1]
        local_name = 'images/' + name[1].split('.')[0] + '.jpg'
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(local_name, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            obj.has_image = True
            obj.save()
            del response
            return True
    obj.has_image = False
    obj.save()
    return False

def set_image_status(max=0, count=0, not_found=0, done=False):
    if max > 0:
        percent =  int(count/max*100)
    else:
        percent = 0
    set_key_value('IMAGES', {
        'percent': percent,
        'max': max,
        'count': count,
        'not_found': not_found,
        'done': done
    })


