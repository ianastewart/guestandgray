import getpass
import logging
import os

from PIL import Image
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, reverse
from django.views.generic import DetailView, View
from django.views.generic.edit import FormMixin
from django_htmx.http import HttpResponseClientRedirect
from resizeimage import resizeimage
from wagtail.models import Collection

from notes.models import Note
from shop.forms import ImageForm, PhotoForm
from shop.models import CustomImage, Item, Photo

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
    action = None
    image = None

    def dispatch(self, request, *args, **kwargs):
        self.item = self.get_object()
        if request.htmx:
            if request.htmx.trigger_name:
                bits = request.htmx.trigger_name.split("-")
                self.action = bits[0]
                if len(bits) == 2:
                    self.image = CustomImage.objects.get(id=bits[1])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.htmx:
            if self.action == "reassign":
                return image_assign_view(request, image_pk=self.image.pk)
            if self.action == "view_unlinked":
                request.session["view_unlinked"] = True
            elif self.action == "hide_unlinked":
                request.session["view_unlinked"] = False
            context = {}
            self.add_unlinked_context(context)
            return render(request, "shop/item_images__unlinked.html", context)
        return super().get(request, *args, **kwargs)

    def add_linked_context(self, context):
        context["images"], context["bad_images"] = self.item.visible_images()
        context["image"] = (
            self.item.image if self.item.image in context["images"] else None
        )

    def add_unlinked_context(self, context):
        context["unlinked_images"] = self.item.hidden_images()
        context["view_unlinked"] = self.request.session.get("view_unlinked", False)

    def get_initial(self):
        initial = super().get_initial()
        initial["crop"] = True
        initial["limit"] = 3000
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["note"] = Note.objects.filter(item=self.object).first()
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
            context = {"item": self.item}
            if request.htmx.trigger == "group":
                image_ids = request.POST.getlist("image")
                pos = 0
                for image_id in image_ids:
                    image = CustomImage.objects.get(id=image_id)
                    image.position = pos
                    image.save()
                    if pos == 0:
                        self.item.image = image
                        self.item.save()
                    pos += 1

            if self.action == "wagtail":
                return HttpResponseClientRedirect(f"/admin/images/{self.image.id}")

            elif self.action == "delete":
                self.image.delete()

            elif self.action == "unhide":
                self.image.show = True
                self.image.item = self.item
                self.image.position = self.item.last_position()
                self.image.save()
                if not self.item.image:
                    self.item.image = self.image
                    self.item.save()

            elif self.action == "hide":
                self.image.show = False
                self.image.save()
                if self.item.image_id == self.image.id:
                    self.item.image = None
                    self.item.save()
                    images, _ = self.item.visible_images()
                    if images:
                        self.item.image = images[0]
                        self.item.save()

            elif self.action == "delete_missing":
                images, bad_images = self.item.visible_images()
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

    def process_photos(self, crop: bool, limit: int):
        user = getpass.getuser()
        collection = Collection.objects.filter(name="Shop images").first()
        photos = Photo.objects.all()
        try:
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
            return True
        except PermissionError as e:
            messages.error(self.request, f"Permission error User:{user}, {full_path}")


def image_assign_view(request, **kwargs):
    """Modal to reassign an image to another item"""
    image = CustomImage.objects.get(pk=kwargs["image_pk"])
    context = {"image": image}
    if request.method == "GET":
        if "reference" in request.GET:
            new_item = Item.objects.filter(ref=request.GET["reference"].upper()).first()
            context["new_item"] = new_item
            return render(request, "shop/image_assign_modal__result.html", context)
        return render(request, "shop/image_assign_modal.html", context)
    else:
        new_item = Item.objects.get(pk=request.POST["new_item"])
        old_item = image.item
        image.item = new_item
        image.title = f"{new_item.ref} {new_item.name}"
        image.position = new_item.last_position()
        image.show = False if "hidden" in request.POST else True
        image.save()
        context = {
            "image": image,
            "old_item": old_item,
            "new_item": new_item,
            "old_path": reverse("item_images", kwargs={"pk": old_item.pk}),
            "new_path": reverse("item_images", kwargs={"pk": new_item.pk}),
        }
        return render(request, "shop/image_assign_modal__redirect.html", context)


def resize(im, crop, limit):
    """
    Resize image to limit if limit > 0
    if crop_square, and height and width are within 9 % crop to smaller dimension
    """
    width = im.width
    height = im.height

    if width == height:
        size = width
        if 0 < limit < width:
            size = limit
            im = resizeimage.resize_width(im, size)

    elif width > height:
        size = height
        if 0 < limit < height:
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
