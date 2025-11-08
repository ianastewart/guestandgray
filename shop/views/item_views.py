import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, FormView
from django_htmx.http import HttpResponseClientRefresh, HttpResponseClientRedirect
from notes.models import Note
from shop.filters import ItemFilter
from shop.forms import ItemCategoriseForm, ItemForm
from shop.models import Item
from shop.session import cart_add_item, cart_get_item
from shop.tables import ItemTable
from shop.templatetags.shop_tags import unmarkdown
from shop.truncater import truncate
from table_manager.mixins import StackMixin

# from tables_plus.views import TablesPlusView, ModalMixin
from django_tableaux.buttons import Button
from django_tableaux.views import TableauxView

logger = logging.getLogger(__name__)


class ItemTableView(LoginRequiredMixin, StackMixin, TableauxView):
    model = Item
    table_class = ItemTable
    filterset_class = ItemFilter
    filter_style = TableauxView.FilterStyle.TOOLBAR
    click_url_name = "item_detail"
    click_action = TableauxView.ClickAction.GET
    column_settings = True
    row_settings = True
    infinite_scroll = False
    sticky_header = True

    template_name = "shop/table_wide.html"
    title = "Items"

    def get(self, request, *args, **kwargs):
        self.request.session.pop("referrer", None)
        return super().get(request, *args, **kwargs)

    def get_initial_data(self):
        initial = super().get_initial_data()
        initial["archive"] = "0"
        return initial

    def get_queryset(self):
        return Item.objects.all().order_by("ref")

    def get_bulk_actions(self):
        return [
            ("show_price", "Show price"),
            ("hide_price", "Hide price"),
            ("visible_on", " Visible on"),
            ("visible_off", "Visible off"),
            ("feature_on", "Featured on"),
            ("feature_off", "Featured off"),
            ("archive_on", "Move to archive"),
            ("archive_off", "Remove from archive"),
            ("change_category", "Change category", reverse("item_categorise")),
            ("delete", "Delete"),
            ("export", "Export to Excel"),
        ]

    def get_buttons(self):
        return [
            Button("New item", href=reverse("item_create")),
        ]

    def handle_action(self, request, action):
        if "show_price" in action:
            self.selected_objects.update(show_price=True)
        elif "hide_price" in action:
            self.selected_objects.update(show_price=False)
        elif "visible_on" in action:
            self.selected_objects.update(visible=True)
        elif "visible_off" in action:
            self.selected_objects.update(visible=False)
        elif "feature_on" in action:
            self.selected_objects.update(featured=True)
        elif "feature_off" in action:
            self.selected_objects.update(featured=False)
        elif "archive_on" in action:
            self.selected_objects.update(archive=True)
        elif "archive_off" in action:
            self.selected_objects.update(archive=False)
        elif "change_category" in action:
            request.session["selected_objects"] = self.selected_objects
            # simulate return redirect("item_categorise")
            request.method = "GET"
            return ItemCategoriseModalView.as_view()(request)
        elif "delete" in action:
            for item in self.selected_objects:
                if item.image:
                    item.image.delete()
                item.delete()


class ItemCategoriseModalView(FormView):
    """Get the new category for selected items"""

    template_name = "shop/category_modal.html"
    form_class = ItemCategoriseForm
    title = "Change category"

    def form_valid(self, form):
        self.request.session["selected_objects"].update(
            category=form.cleaned_data["new_category"]
        )
        return HttpResponseClientRefresh()


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "shop/item_form.html"

    def get_initial(self):
        initial = super().get_initial()
        initial["library"] = Item.Library.STOCK.value
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["STOCK"] = Item.Library.STOCK.value
        context["ARCHIVE"] = Item.Library.ARCHIVE.value
        context["RESEARCH"] = Item.Library.RESEARCH.value
        return context


class ItemUpdateView(LoginRequiredMixin, StackMixin, UpdateView):
    model = Item
    template_name = "shop/item_form.html"
    form_class = ItemForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item"] = self.object
        context["STOCK"] = Item.Library.STOCK.value
        context["ARCHIVE"] = Item.Library.ARCHIVE.value
        context["RESEARCH"] = Item.Library.RESEARCH.value
        context["images"], context["bad_images"] = self.object.visible_images()
        context["image"] = (
            self.object.image if self.object.image in context["images"] else None
        )
        context["allow_delete"] = not self.object.lot
        context["note"] = Note.objects.filter(item=self.object).first()
        return context

    def post(self, request, *args, **kwargs):
        item = self.get_object()
        if "delete" in request.POST:
            item.delete()
            messages.add_message(
                request, messages.INFO, f"Item ref: {item.ref} has been deleted"
            )
            return redirect("item_list")

        # save_state = False
        # save_featured = False
        # if request.POST["library"] == Item.Library.RESEARCH.value:
        #     # missing fields when RESEARCH are retained
        #     save_state = True
        #     state = item.state
        #     location = item.location
        #     rank = item.rank
        # if request.POST["library"] != Item.Library.STOCK.value:
        #     # missing when RESEARCH or ARCHIVE are retained
        #     save_featured = True
        #     featured = item.featured
        #     show_price = item.show_price
        #     done = item.done
        result = super().post(request, *args, **kwargs)
        # item = self.object
        # if save_state:
        #     item.state = state
        #     item.location = location
        #     item.rank = rank
        # if save_featured:
        #     item.featured = featured
        #     item.show_price = show_price
        #     item.done = done
        # item.save()
        return result
        #     return HttpResponseClientRedirect(self.get_success_url())
        # else:
        #     return self.form_invalid(form)
        # return super().post(request, *args, **kwargs)

    def get_success_url(self):
        if "preview" in self.request.POST:
            return reverse("item_detail", kwargs={"pk": self.object.pk})
        referrer = self.request.session.get("referrer", None)
        return referrer if referrer else reverse("staff_home")


class ItemDetailView(LoginRequiredMixin, StackMixin, DetailView):
    model = Item
    modal_size = "modal-lg"
    modal_template_name = "shop/item_detail_modal.html"
    template_name = "shop/item_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if reverse("item_list") in self.request.META["HTTP_REFERER"]:
            self.request.session["referrer"] = self.request.META["HTTP_REFERER"]
        context["images"], context["bad_images"] = self.object.visible_images()
        context["images"] = list(context["images"]) + list(self.object.hidden_images())
        context["image"] = (
            self.object.image if self.object.image in context["images"] else None
        )
        context["in_cart"] = cart_get_item(self.request, self.object.pk)
        clean_description = unmarkdown(self.object.description).replace("\n", " ")
        context["seo"] = truncate(clean_description, 200)
        context["note"] = Note.objects.filter(item=self.object).first()
        context["STOCK"] = Item.Library.STOCK.value
        context["ARCHIVE"] = Item.Library.ARCHIVE.value
        context["RESEARCH"] = Item.Library.RESEARCH.value
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
        referrer = self.request.session.pop("referrer", None)
        return redirect(referrer if referrer else "staff_home")
