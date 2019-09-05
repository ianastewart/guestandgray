import logging

from keyvaluestore.utils import get_value_for_key, set_key_value
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from shop.models import Object, OldCategory, CustomImage
from shop.import_helper import (
    import_objects,
    process_objects,
    process_images,
    set_status,
)

logger = logging.getLogger(__name__)


@login_required
def import_objects_view(request):
    template_name = "shop/import.html"

    if request.method == "GET":
        set_status("Waiting")

    if request.method == "POST":
        excel_file = request.FILES["myfile"]
        if import_objects(excel_file):
            process_objects(request.user)

    return render(request, template_name, context={})


@login_required
def import_process_view(request):
    template_name = "shop/import_process.html"

    if request.method == "POST":
        process_objects(request.user, link_images=False)
    return render(request, template_name, context={"title": "Process objects"})


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
    cats = OldCategory.objects.all()
    for cat in cats:
        objects = cat.object_set.filter(image__isnull=False)
        if objects:
            cat.image = objects[0].image
            cat.save()
    return redirect("public_catalogue")
