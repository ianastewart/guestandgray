import logging
import os
import shutil
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.views.generic import DetailView, View
from django.views.generic.edit import FormMixin
from shop.forms import ImageForm, PhotoForm
from shop.models import CustomImage, Item, Photo
from wagtail.core.models import Collection
from django.core.files.storage import default_storage
from PIL import Image
from resizeimage import resizeimage

# from shop.tables import ItemTable

logger = logging.getLogger(__name__)


class BasicUploadView(View):
    template_name = "shop/basic_upload.html"

    def get(self, request):
        photos_list = Photo.objects.all()
        return render(self.request, self.template_name, {"photos": photos_list})

    def post(self, request):
        """
        Handle a post request from the image uploader
        Create a temporary Photo object
        """
        form = PhotoForm(self.request.POST, self.request.FILES)
        if form.is_valid():
            photo = form.save()
            photo.title = os.path.split(form.cleaned_data["file"].name)[1]
            photo.save()
            data = {"is_valid": True, "name": photo.title, "url": photo.file.url}
        else:
            data = {"is_valid": False}
        return JsonResponse(data)


class ItemImagesView(LoginRequiredMixin, FormMixin, DetailView):
    model = Item
    template_name = "shop/item_images.html"
    form_class = ImageForm
    item = None

    def get(self, request, *args, **kwargs):
        self.item = self.get_object()
        if request.htmx:
            if request.htmx.trigger_name == "view_unlinked":
                request.session["view_unlinked"] = True
            elif request.htmx.trigger_name == "hide_unlinked":
                request.session["view_unlinked"] = False
            context = {}
            self.add_unlinked_context(context)
            return render(request, "shop/item_images__unlinked.html", context)
        return super().get(request, *args, **kwargs)

    def add_linked_context(self, context):
        context["images"], context["bad_images"] = self.item.associated_images()
        context["image"] = (
            self.item.image if self.item.image in context["images"] else None
        )

    def add_unlinked_context(self, context):
        context["unlinked_images"] = CustomImage.objects.filter(
            item=None, title__startswith=self.item.ref + " "
        ).order_by("file")
        context["view_unlinked"] = self.request.session.get("view_unlinked", False)

    def get_initial(self):
        initial = super().get_initial()
        initial["crop"] = True
        initial["limit"] = 3000
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.add_linked_context(context)
        self.add_unlinked_context(context)
        # Clear photos and associated files
        Photo.objects.all().delete()
        folder = os.path.join(settings.MEDIA_ROOT, "photos")
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            os.unlink(file_path)
        return context

    def post(self, request, *args, **kwargs):
        self.item = self.get_object()
        if request.htmx:
            bits = request.htmx.trigger_name.split("-")
            action = bits[0]
            if len(bits) == 2:
                image = CustomImage.objects.get(id=bits[1])
            context = {"item": self.item}

            if action == "unlink":
                # Just remove the reference to the item, leaving image in the database
                image.item = None
                image.show = True
                image.save()
                self.check_primary(image)

            elif action == "delete":
                self.check_primary(image)
                image.delete()
                self.check_primary(image)

            if action == "primary":
                image.show = True
                image.save()
                self.item.image = image
                self.item.save()

            elif action == "unhide":
                image.show = True
                image.save()

            elif action == "hide":
                image.show = False
                image.save()

            elif action == "link":
                image.item = self.item
                image.save()

            elif action == "delete_missing":
                images, bad_images = self.item.associated_images()
                for image in bad_images:
                    image.delete()
                return HttpResponse(
                    f"<h5>Missing images have been deleted</h5>",
                    content_type="text/plain",
                )
            if request.htmx.target == "images":
                self.add_linked_context(context)
                self.add_unlinked_context(context)
                template = "shop/item_images__all.html"
            elif request.htmx.target == "linked_images":
                self.add_linked_context(context)
                template = "shop/item_images__linked.html"
            elif request.htmx.target == "unlinked_images":
                self.add_unlinked_context(context)
                template = "shop/item_images__unlinked.html"
            return render(request, template, context)

        if "process" in request.POST:
            crop = "crop" in request.POST
            limit = int(request.POST["limit"])
            self.process_photos(crop, limit)
        return self.get(request, *args, **kwargs)

    def check_primary(self, image):
        # if we delete or unlink primary make first item in list the primary item
        if self.item.image_id == image.id:
            self.item.image = (
                CustomImage.objects.filter(item_id=self.item.id, show=True)
                .order_by("file")
                .first()
            )
            self.item.save()

    def process_photos(self, crop: bool, limit: int):
        collection = Collection.objects.filter(name="Shop images").first()
        photos = Photo.objects.all()
        for photo in photos:
            source = os.path.join(settings.MEDIA_ROOT, photo.file.name)
            with open(source, "r+b") as f:
                with Image.open(f) as image:
                    im = resize(image, crop, limit)
                    dest = os.path.join("original_images", photo.title)
                    full_path = os.path.join(settings.MEDIA_ROOT, dest)
                    im.save(full_path, optimize=True, quality=70)
            CustomImage.objects.create(
                file=dest,
                title=self.item.ref + " " + self.item.name,
                collection_id=collection.id,
                uploaded_by_user=self.request.user,
                item=self.item,
            )


def resize(im, crop, limit):
    """
    Resize image to limit if limit > 0
    if crop_square, and height and width are within 9 % crop to smaller dimension
    """
    width = im.width
    height = im.height

    if width == height:
        size = width
        if limit > 0 and width > limit:
            size = limit
            im = resizeimage.resize_width(im, size)

    elif width > height:
        size = height
        if limit > 0 and height > limit:
            size = limit
        if crop and (width - height) / width < 0.09:
            im = resizeimage.resize_crop(im, [size, size])
        else:
            im = resizeimage.resize_width(im, size)

    elif height > width:
        size = width
        if limit and width > limit:
            size = limit
        if crop and (height - width) / height < 0.09:
            im = resizeimage.resize_crop(im, [size, size])
        else:
            im = resizeimage.resize_height(im, size)
    return im
