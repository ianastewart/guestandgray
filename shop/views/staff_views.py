import logging
import os.path
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage
from django.views.generic import (
    View,
    TemplateView,
    CreateView,
    UpdateView,
    ListView,
    DetailView,
)
from django_tables2 import SingleTableView
from wagtail.core.models import Collection
from shop.models import Item, Category, CustomImage
from shop.forms import ItemForm, CategoryForm
from shop.tables import ItemTable

logger = logging.getLogger(__name__)


class StaffHomeView(LoginRequiredMixin, TemplateView):
    template_name = "shop/staff_home.html"


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "shop/item_update.html"

    def post(self, request, *args, **kwargs):
        result = super().post(request, *args, **kwargs)
        if "load" in request.POST:
            pass
        return result

    def get_success_url(self):
        return reverse("item_detail", kwargs={"pk": self.object.pk})


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    form_class = ItemForm
    template_name = "shop/item_update.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["photos"] = CustomImage.objects.filter(item_id=self.object.id)
        return context

    def get_success_url(self):
        return reverse("item_detail", kwargs={"pk": self.object.pk})


class ItemImagesView(LoginRequiredMixin, DetailView):
    model = Item
    template_name = "shop/item_images.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # primary image always first in list
        images = [self.object.image]
        for image in CustomImage.objects.filter(item_id=self.object.id):
            if image.id != self.object.image_id:
                images.append(image)
        context["images"] = images
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_item()
        result = {"error": "Bad command"}
        if "action" in request.POST:
            action = request.POST["action"]
            id = request.POST["id"]
            try:
                image = CustomImage.object.get(id=id)
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
                        self.object = None
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
                        existing = CustomImage.objects.get(file=short_path)
                        error = "Image already in the database. "
                        if existing.item:
                            if existing.item.id == self.object.id:
                                error += "It is linked to this item."
                            else:
                                error += f"It is linked to Ref: {existing.item.ref }, {existing.title}."
                        else:
                            error += (
                                "It is not linked to an item but may be used elsewhere."
                            )
                    except CustomImage.DoesNotExist:
                        # if file exists but is not used vy a CustomImage, overwrite it
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
        context["price"] = int(self.object.price / 100)
        context["photos"] = CustomImage.objects.filter(item_id=self.object.id)
        return context


class ItemListView(LoginRequiredMixin, SingleTableView):
    model = Item
    template_name = "shop/item_list.html"
    table_class = ItemTable

    # def get_queryset(self):
    #     return Item.objects.all().order_by("name")


class CategoryClearView(LoginRequiredMixin, View):
    """ Clears all objects from the database """

    def get(self, request):
        Category.objects.all().delete()
        messages.add_message(request, messages.INFO, "All categories cleared")
        return redirect("staff_home")


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "shop/category_form.html"
    success_url = reverse_lazy("category_list")
    title = "Create category"


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "shop/category_form.html"
    success_url = reverse_lazy("category_list")
    title = "Update category"

    def get_initial(self):
        initial = super().get_initial()
        cat = self.object.get_parent()
        initial["parent_category"] = cat.pk
        return initial

    def form_valid(self, form):
        old_parent = self.object.get_parent()
        new_parent = form.cleaned_data["parent_category"]
        response = super().form_valid(form)
        if old_parent.id != new_parent.id:
            self.object.move(new_parent, "sorted-child")
        return response


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "shop/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        root = Category.objects.get(name="Catalogue")
        return root.get_children().order_by("name")


class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = "shop/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item_list"] = self.object.item_set.all().order_by("name")
        return context
