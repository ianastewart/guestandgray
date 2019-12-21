import logging
import os.path
from decimal import *
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DetailView
from wagtail.core.models import Collection
from django_tables2 import Column, TemplateColumn, Table
from django_tables2_column_shifter.tables import ColumnShiftTable
from shop.tables import ImageColumn

from shop.forms import ItemForm, ArchiveItemForm
from shop.models import Item, CustomImage

# from shop.tables import ItemTable
from table_manager.views import FilteredTableView, AjaxCrudView
from shop.filters import ItemFilter
from shop.session import cart_add_item, cart_get_item

logger = logging.getLogger(__name__)


class ItemTable(ColumnShiftTable):
    class Meta:
        model = Item
        fields = (
            "selection",
            "name",
            "ref",
            "category",
            "cost_price",
            "sale_price",
            "archive",
        )
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row "}

    category = Column(accessor="category__name", verbose_name="Category")
    image = ImageColumn(accessor="image")
    selection = TemplateColumn(
        accessor="pk",
        template_name="table_manager/custom_checkbox.html",
        verbose_name="",
    )

    def get_column_default_show(self):
        self.column_default_show = ["selection", "name", "ref"]
        return super().get_column_default_show()

    def render_sale_price(self, value):
        return int(value)


class ItemTableView(LoginRequiredMixin, FilteredTableView):
    model = Item
    table_class = ItemTable
    filter_class = ItemFilter
    heading = "Items"
    allow_create = False
    allow_update = True
    filter_left = True
    auto_filter = True

    def get_initial_data(self):
        initial = super().get_initial_data()
        initial["archive"] = "0"
        return initial

    def get_queryset(self):
        return Item.objects.all().select_related("category").order_by("ref")

    def get_actions(self):
        return [("Export to Excel", "export")]


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "shop/item_form.html"


class ItemCreateAjax(LoginRequiredMixin, AjaxCrudView):
    model = Item
    form_class = ItemForm
    modal_class = "modal-xl"
    template_name = "shop/includes/partial_item_form.html"


class ItemPostMixin:
    """
    Common post actions used in both regular and json item update views
    Returns True if a command has been actioned ""
    """

    def post_action(self, request, item):
        category = item.category
        if "assign_category" in request.POST:
            category.image = item.image
            category.save()
            return True
        elif "assign_archive" in request.POST:
            category.archive_image = item.image
            category.save()
            return True
        elif "add" in request.POST:
            cart_add_item(request, item)
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
        context["allow_delete"] = not self.object.lot
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
    form_class = ItemForm
    template_name = "shop/includes/partial_item_form.html"
    modal_class = "modal-xl"
    update = True
    allow_delete = True

    def get_form_class(self):
        return ArchiveItemForm if self.object.archive else ItemForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = self.object
        margin = Decimal(0)
        min_margin = Decimal(0)
        profit = Decimal(0)
        min_profit = Decimal(0)
        if item.cost_price:
            cost = item.cost_price + item.restoration_cost
            profit = item.sale_price - cost
            if item.minimum_price:
                min_profit = item.minimum_price - cost
            else:
                item.minimum_price = Decimal(0)
                min_profit = Decimal(0)
            if item.sale_price > 0 and profit > 0:
                margin = profit / item.sale_price * 100
            if item.minimum_price > 0 and min_profit > 0:
                min_margin = min_profit / item.minimum_price * 100
        else:
            cost = Decimal(0)
        context["item"] = item
        context["total_cost"] = cost
        context["margin"] = margin
        context["min_margin"] = min_margin
        context["profit"] = profit
        context["min_profit"] = min_profit
        if item.lot:
            context["purchase"] = item.lot.purchase
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
        context["in_cart"] = cart_get_item(self.request, self.object.pk)
        return context

    def post(self, request, **kwargs):
        item = get_object_or_404(Item, pk=kwargs.get("pk"))
        cart_add_item(request, item)
        messages.add_message(
            request, messages.INFO, f"Item ref: {item.ref} has been added to the cart"
        )
        return redirect("item_detail", item.pk)
