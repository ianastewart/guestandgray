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

# from shop.tables import ItemTable
from table_manager.views import AjaxCrudView, FilteredTableView
from table_manager.mixins import StackMixin

logger = logging.getLogger(__name__)


class ItemTableView(LoginRequiredMixin, StackMixin, FilteredTableView):
    model = Item
    table_class = ItemTable
    filter_class = ItemFilter
    template_name = "shop/filtered_table.html"
    heading = "Items"
    allow_create = True
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
            next_url = reverse("item_list")
            data = {"next_url": "", "target_id": request.POST["x_target_id"]}
            return JsonResponse(data)


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


class ItemUpdateView(LoginRequiredMixin, StackMixin, UpdateView, ItemPostMixin):
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


class ItemDetailView(LoginRequiredMixin, StackMixin, DetailView):
    model = Item
    template_name = "shop/item_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["images"] = (
            self.object.images.all().exclude(id=self.object.image_id).order_by("-show")
        )
        context["in_cart"] = cart_get_item(self.request, self.object.pk)
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


class ItemDetailAjax(LoginRequiredMixin, StackMixin, AjaxCrudView):
    model = Item
    template_name = "shop/item_detail_modal.html"
    modal_class = "modal-xl"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["images"] = self.object.images.all().exclude(id=self.object.image_id)
        context["in_cart"] = cart_get_item(self.request, self.object.pk)
        return context


class ItemCategoriseAjax(LoginRequiredMixin, AjaxCrudView):
    """ get the new category for selected items """

    template_name = "shop/includes/partial_categorise_form.html"
    form_class = ItemCategoriseForm
    target_id = "#modal-action-form"
    title = "Change category"
