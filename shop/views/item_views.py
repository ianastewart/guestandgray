import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, UpdateView
from django_htmx.http import HttpResponseClientRefresh, HttpResponseClientRedirect
from notes.models import Note
from shop.filters import ItemFilter
from shop.forms import ItemCategoriseForm, ItemForm
from shop.models import Item
from shop.session import cart_add_item, cart_get_item
from shop.tables import ItemTable
from shop.templatetags.shop_tags import unmarkdown
from shop.truncater import truncate
from table_manager.buttons import BsButton
from table_manager.mixins import StackMixin
from table_manager.views import AjaxCrudView, FilteredTableView
from tables_plus.views import TablesPlusView
from tables_plus.buttons import Button

logger = logging.getLogger(__name__)


class ItemTableView(LoginRequiredMixin, StackMixin, TablesPlusView):
    model = Item
    table_class = ItemTable
    filterset_class = ItemFilter
    filter_style = TablesPlusView.FilterStyle.HEADER
    filter_button = False

    template_name = "shop/table.html"
    title = "Items"
    infinite_scroll = True

    def get(self, request, *args, **kwargs):
        self.request.session.pop("referrer", None)
        return super().get(request, *args, **kwargs)

    def get_initial_data(self):
        initial = super().get_initial_data()
        initial["archive"] = "0"
        return initial

    def get_queryset(self):
        return Item.objects.all().order_by("ref")

    def get_actions(self):
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

    def handle_action(self, request):
        if "show_price" in request.POST:
            self.selected_objects.update(show_price=True)
        elif "hide_price" in request.POST:
            self.selected_objects.update(show_price=False)
        elif "visible_on" in request.POST:
            self.selected_objects.update(visible=True)
        elif "visible_off" in request.POST:
            self.selected_objects.update(visible=False)
        elif "feature_on" in request.POST:
            self.selected_objects.update(featured=True)
        elif "feature_off" in request.POST:
            self.selected_objects.update(featured=False)
        elif "archive_on" in request.POST:
            self.selected_objects.update(archive=True)
        elif "archive_off" in request.POST:
            self.selected_objects.update(archive=False)
        elif "change_category" in request.POST:
            self.selected_objects.update(category_id=request.POST["new_category"])
        elif "delete" in request.POST:
            for item in self.selected_objects:
                if item.image:
                    item.image.delete()
                item.delete()
        elif "export-all-columns" in request.POST:
            return self.export(request, query_set=self.get_queryset(), all_columns=True)

    def row_clicked(self, pk, target, url):
        path = reverse("item_detail", kwargs={"pk": pk})
        prefix = "&" if "?" in url else "?"
        return HttpResponseClientRedirect(path + prefix + "return_url=" + url)

    def get_buttons(self):
        return [
            Button("New item", href=reverse("item_create")),
            Button("Export all columns", typ="submit")
        ]



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

    def get(self, request, *args, **kwargs):
        if request.htmx:
            item = self.get_object()
            item.archive = request.htmx.trigger_name == "archive"
            item.save()
            template = "shop/item_form__pricing.html"
            context = {"item": item}
            return render(request, template, context)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item"] = self.object
        context["images"], context["bad_images"] = self.object.visible_images()
        context["image"] = self.object.image if self.object.image in context["images"] else None
        # context["photos"] = CustomImage.objects.filter(item_id=self.object.id)
        context["allow_delete"] = not self.object.lot
        context["note"] = Note.objects.filter(item=self.object).first()
        return context

    def post(self, request, *args, **kwargs):
        item = self.get_object()
        item.archive = request.POST["archive"] == "true"
        item.save()
        if request.htmx:
            return HttpResponse("")
        if "delete" in request.POST:
            item.delete()
            messages.add_message(request, messages.INFO, f"Item ref: {item.ref} has been deleted")
            return redirect("item_list")
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        if "preview" in self.request.POST:
            return reverse("item_detail", kwargs={"pk": self.object.pk})
        referrer = self.request.session.pop("referrer", None)
        return referrer if referrer else reverse("staff_home")


class ItemDetailView(LoginRequiredMixin, StackMixin, DetailView):
    model = Item
    template_name = "shop/item_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if reverse("item_list") in self.request.META["HTTP_REFERER"]:
            self.request.session["referrer"] = self.request.META["HTTP_REFERER"]
        context["images"], context["bad_images"] = self.object.visible_images()
        context["image"] = self.object.image if self.object.image in context["images"] else None
        context["in_cart"] = cart_get_item(self.request, self.object.pk)
        clean_description = unmarkdown(self.object.description).replace("\n", " ")
        context["seo"] = truncate(clean_description, 200)
        context["note"] = Note.objects.filter(item=self.object).first()
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


class ItemCategoriseAjax(LoginRequiredMixin, AjaxCrudView):
    """get the new category for selected items"""

    template_name = "shop/includes/partial_categorise_form.html"
    form_class = ItemCategoriseForm
    target_id = "#modal-form"
    title = "Change category"
