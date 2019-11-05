import logging
import os.path

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DetailView
from wagtail.core.models import Collection

from shop.forms import ItemForm, ArchiveItemForm
from shop.models import Item, CustomImage
from shop.tables import ItemTable
from shop.views.generic_views import FilteredTableView, AjaxCrudView
from shop.filters import ItemFilter

logger = logging.getLogger(__name__)


class ItemListView(LoginRequiredMixin, FilteredTableView):
    model = Item
    template_name = "generic_table.html"
    table_class = ItemTable
    filter_class = ItemFilter
    heading = "Items"
    modal_class = "modal-xl"
    allow_create = False
    allow_update = True
    filter_left = True

    def get_queryset(self):
        return Item.objects.all().order_by("ref")

    def get_actions(self):
        return [("Export to Excel", "export")]

    def get_buttons(self):
        return [("Export to Excel", "export")]


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "shop/item_form.html"


class ItemCreateAjax(LoginRequiredMixin, AjaxCrudView):
    model = Item
    form_class = ItemForm
    template_name = "shop/includes/partial_item_form.html"


class ItemPostMixin:
    """
    Common post actions used in both regular and json item update views
    Returns True if a command has been actioned ""
    """

    def post_action(self, request, object):
        category = object.category
        if "assign_category" in request.POST:
            category.image = object.image
            category.save()
            return True
        elif "assign_archive" in request.POST:
            category.archive_image = object.image
            category.save()
            return True
        return False


class ItemUpdateView(LoginRequiredMixin, UpdateView, ItemPostMixin):
    model = Item
    template_name = "shop/item_form.html"

    def get_form(self, form_class=None):
        if self.object.archive:
            return ArchiveItemForm(**self.get_form_kwargs())
        else:
            return ItemForm(**self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["photos"] = CustomImage.objects.filter(item_id=self.object.id)
        context["allow_delete"] = True
        return context

    def get_success_url(self):
        return reverse("item_detail", kwargs={"pk": self.object.pk})

    def post(self, request, *args, **kwargs):
        object = self.get_object()
        if self.post_action(request, object):
            return redirect("item_update", object.pk)
        if "delete" in request.POST:
            object.delete()
            messages.add_message(
                request, messages.INFO, f"Item ref: {object.ref} has been deleted"
            )
            return redirect("item_list")
        return super().post(request, *args, **kwargs)


class ItemUpdateAjax(LoginRequiredMixin, AjaxCrudView, ItemPostMixin):
    model = Item
    template_name = "shop/includes/partial_item_form.html"
    update = True
    allow_delete = True

    def get_form_class(self):
        return ArchiveItemForm if self.object.archive else ItemForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["object"] = self.object.image
        context["photos"] = CustomImage.objects.filter(item_id=self.object.id)
        return context

    def post(self, request, *args, **kwargs):
        object = self.get_object(**kwargs)
        if self.post_action(request, object):
            return redirect("item_update_ajax", object.pk)
        return super().post(request, *args, **kwargs)


class ItemImagesView(LoginRequiredMixin, DetailView):
    model = Item
    template_name = "shop/item_images.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # primary image always first in list
        images = []
        exclude = 0
        if self.object.image:
            images.append(self.object.image)
            exclude = self.object.image.id
        for image in CustomImage.objects.filter(item_id=self.object.id).order_by(
            "title"
        ):
            if image.id != exclude:
                images.append(image)
        context["images"] = images
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        result = {"error": "Bad command"}
        if "action" in request.POST:
            action = request.POST["action"]
            id = request.POST["id"]
            try:
                image = CustomImage.objects.get(id=id)
            except CustomImage.DoesNotExist:
                result = {"error": "Bad image id"}
                return JsonResponse(result)

            if action == "delete":
                primary = self.object.image_id == image.id
                # Just remove the reference to the item, leaving image in the database
                image.item = None
                image.save()
                if primary:
                    # if we delete the primary, try to make first remaining image primary
                    images = CustomImage.objects.filter(item_id=self.object.id)
                    if images:
                        self.object.image = images[0]
                    else:
                        self.object.image = None
                    self.object.save()
                result = {"success": "deleted"}

            elif action == "primary":
                self.object.image = image
                self.object.save()
                result = {"success": "Made primary"}

        elif request.FILES["myfile"]:
            myfile = request.FILES["myfile"]
            names = myfile.name.split(".")
            error = ""
            if names[len(names) - 1] == "jpg":
                short_path = os.path.join("original_images", myfile.name)
                full_path = os.path.join(settings.MEDIA_ROOT, short_path)
                if os.path.exists(full_path):

                    try:
                        existing_set = CustomImage.objects.filter(file=short_path)
                        if len(existing_set) > 1:
                            error = "Multiple copies already in database."
                        elif len(existing_set) == 1:
                            existing = existing_set[0]
                            if existing.item:
                                error = "Image already in the database. "
                                if existing.item.id == self.object.id:
                                    error += "It is linked to this item."
                                else:
                                    error += f"It is linked to Ref: {existing.item.ref }, {existing.title}."
                        else:

                            os.remove(full_path)
                    except CustomImage.DoesNotExist:
                        # if file exists but is not used by a CustomImage, overwrite it
                        os.remove(full_path)
            else:
                error = "File is not an image. Please select a .jpg"
            if error:
                result = {"error": error}
            else:
                collection_id = Collection.objects.get(name="Root").id
                path = default_storage.save(full_path, myfile)
                new_image = CustomImage.objects.create(
                    file=short_path,
                    title=self.object.name,
                    collection_id=collection_id,
                    uploaded_by_user=request.user,
                    item=self.object,
                )
                result = {"success": new_image.title}
        return JsonResponse(result)


class ItemDetailView(DetailView):
    model = Item
    template_name = "shop/item_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["images"] = self.object.images.all().exclude(id=self.object.image_id)
        return context
