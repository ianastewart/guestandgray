import logging
from decimal import *

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, UpdateView
from django.http import JsonResponse
from shop.filters import ItemFilter
from shop.forms import ArchiveItemForm, ItemForm, ItemCategoriseForm
from shop.models import CustomImage, Item
from shop.session import cart_add_item, cart_get_item
from shop.tables import ItemTable
from shop.truncater import truncate
from shop.templatetags.shop_tags import unmarkdown

# from shop.tables import ItemTable
from table_manager.views import AjaxCrudView, FilteredTableView
from table_manager.mixins import StackMixin
from table_manager.buttons import BsButton
from wagtail.images.models import SourceImageIOError

logger = logging.getLogger(__name__)


class ItemTableView(LoginRequiredMixin, StackMixin, FilteredTableView):
    model = Item
    table_class = ItemTable
    filter_class = ItemFilter
    template_name = "shop/filtered_table.html"
    heading = "Items"
    allow_create = False
    allow_url = True
    auto_filter = True
    filter_right = True

    def get(self, request, *args, **kwargs):
        self.clear_stack(request)
        return super().get(request, *args, **kwargs)

    def get_initial_data(self):
        initial = super().get_initial_data()
        initial["archive"] = "0"
        return initial

    def get_queryset(self):
        return (
            Item.objects.all()
            .select_related("category")
            .prefetch_related("book")
            .order_by("featured", "rank", "-sale_price")
        )

    def get_actions(self):
        return [
            ("show_price", "Show price"),
            ("hide_price", "Hide price"),
            ("visible", " Visible on"),
            ("invisible", "Visible off"),
            ("feature", "Featured on"),
            ("unfeature", "Featured off"),
            ("archive", "Move to archive"),
            ("unarchive", "Remove from archive"),
            ("category", "Change category", reverse("item_categorise")),
            ("delete", "Delete"),
            ("export", "Export to Excel"),
        ]

    def handle_action(self, request):
        if "show_price" in request.POST:
            self.selected_objects.update(show_price=True)
        elif "hide_price" in request.POST:
            self.selected_objects.update(show_price=False)
        elif "visible" in request.POST:
            self.selected_objects.update(visible=True)
        elif "invisible" in request.POST:
            self.selected_objects.update(visible=False)
        elif "feature" in request.POST:
            self.selected_objects.update(featured=True)
        elif "unfeature" in request.POST:
            self.selected_objects.update(featured=False)
        elif "archive" in request.POST:
            self.selected_objects.update(archive=True)
        elif "unarchive" in request.POST:
            self.selected_objects.update(archive=False)
        elif "category" in request.POST:
            self.selected_objects.update(category_id=request.POST["new_category"])

        elif "delete" in request.POST:
            for item in self.selected_objects:
                if item.image:
                    item.image.delete()
                item.delete()

    def get_buttons(self):
        return [BsButton("New item", href=reverse("item_create"))]


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "shop/item_form.html"


class ItemCreateAjax(LoginRequiredMixin, AjaxCrudView):
    model = Item
    form_class = ItemForm
    modal_class = "modal-xl"
    template_name = "shop/includes/partial_item_form.html"


class ItemUpdateView(LoginRequiredMixin, StackMixin, UpdateView):
    model = Item
    template_name = "shop/item_form.html"
    form_class = ItemForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["images"], context["bad_images"] = self.object.visible_images()
        context["image"] = (
            self.object.image if self.object.image in context["images"] else None
        )
        # context["photos"] = CustomImage.objects.filter(item_id=self.object.id)
        context["allow_delete"] = not self.object.lot
        return context

    def post(self, request, *args, **kwargs):
        if "delete" in request.POST:
            item = self.get_object()
            item.delete()
            messages.add_message(
                request, messages.INFO, f"Item ref: {item.ref} has been deleted"
            )
            return redirect("item_list")
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        if "preview" in self.request.POST:
            return reverse("item_detail", kwargs={"pk": self.object.pk})
        return super().get_success_url()


class ItemDetailView(LoginRequiredMixin, StackMixin, DetailView):
    model = Item
    template_name = "shop/item_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["images"], context["bad_images"] = self.object.visible_images()
        context["image"] = (
            self.object.image if self.object.image in context["images"] else None
        )
        context["in_cart"] = cart_get_item(self.request, self.object.pk)
        clean_description = unmarkdown(self.object.description).replace("\n", " ")
        context["seo"] = truncate(clean_description, 200)
        return context

    def post(self, request, **kwargs):
        if "add" in request.POST:
            item = get_object_or_404(Item, pk=kwargs.get("pk"))
            cart_add_item(request, item)
            messages.add_message(
                request,
                messages.INFO,
                f"Item ref: {item.ref} has been added to the cart",
            )
        return redirect(self.get_success_url())


class ItemCategoriseAjax(LoginRequiredMixin, AjaxCrudView):
    """ get the new category for selected items """

    template_name = "shop/includes/partial_categorise_form.html"
    form_class = ItemCategoriseForm
    target_id = "#modal-form"
    title = "Change category"
