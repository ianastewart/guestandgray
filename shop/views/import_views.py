import logging
import os.path

from keyvaluestore.utils import get_value_for_key, set_key_value
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from shop.models import Item, Category, CustomImage
from shop.import_helper import import_objects, process_images, set_status

logger = logging.getLogger(__name__)


@login_required
def upload_view(request):
    template_name = "shop/upload.html"

    if request.method == "POST" and request.FILES["myfile"]:
        myfile = request.FILES["myfile"]
        full_path = os.path.join(settings.MEDIA_ROOT, "excel", myfile.name)
        if os.path.exists(full_path):
            os.remove(full_path)
        path = default_storage.save(full_path, myfile)
        return render(request, template_name, {"uploaded_file_url": path})
    return render(request, template_name)


@login_required
def import_progress_view(request):
    progress = get_value_for_key("PROGRESS")
    if progress:
        return JsonResponse(progress, safe=False)
    return JsonResponse({"error": "No progress key found"})


@login_required
def import_images_view(request):
    """ Attach images to objects """
    template_name = "shop/import_process.html"
    context = {"title": "Process images"}
    if request.method == "POST":
        process_images(request.user)
    return render(request, template_name, context)


#
# @login_required
# def import_images_progress_view(request):
#     progress = get_value_for_key("IMAGES")
#     if progress:
#         return JsonResponse(progress, safe=True)
#     return JsonResponse({"error": "No  key found"})


@login_required
def set_category_images_view(request):
    """ set default category image to be first associated object that has an image"""
    cats = Category.objects.all()
    for cat in cats:
        objects = cat.object_set.filter(image__isnull=False)
        if objects:
            cat.image = objects[0].image
            cat.save()
    return redirect("public_catalogue_root")
