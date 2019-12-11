from decimal import *
import logging
from datetime import date
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, TemplateView, CreateView, FormView
from django.urls import reverse
from django.shortcuts import redirect
from shop.forms import (
    NewVendorForm,
    PurchaseVendorForm,
    PurchaseDataForm,
    UpdateItemForm,
    PurchaseLotForm,
)
from shop.models import Contact, Purchase, Item, ItemRef, Lot
from shop.tables import PurchaseTable
from shop.filters import PurchaseFilter
from table_manager.views import FilteredTableView, AjaxCrudView
import shop.session as session

logger = logging.getLogger(__name__)


class DispatchMixin:
    """ Mixin to add session variables to class """

    def dispatch(self, request, *args, **kwargs):
        self.index = int(kwargs["index"])
        posted = session.get_data(self.index, request)
        self.initial = posted if posted else {}
        return super().dispatch(request, *args, **kwargs)


class PurchaseStartView(View):
    """ Starts a new purchase wizard """

    def get(self, request):
        session.clear_data(request)
        request.session["ref"] = ItemRef.get_next(request)
        return redirect("purchase_vendor", 0)


class PurchaseVendorView(LoginRequiredMixin, DispatchMixin, FormView):
    """ Capture details of the vendor"""

    form_class = PurchaseVendorForm
    template_name = "shop/purchase_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor_id = self.initial.get("vendor_id", None)
        try:
            vendor = Contact.objects.get(id=vendor_id)
            name = vendor.name
        except Contact.DoesNotExist:
            name = ""
        context["vendor"] = name
        return context

    def post(self, request, **kwargs):
        if "cancel" in request.POST:
            return redirect("staff_home")
        return super().post(request, **kwargs)

    def form_valid(self, form):
        session.update_data(0, self.request, form)
        return redirect("purchase_data_create", 1)


class PurchaseVendorCreateView(LoginRequiredMixin, AjaxCrudView):
    """ Create a new vendor in modal within the PurchaseCreateView """

    model = Contact
    form_class = NewVendorForm
    template_name = "shop/includes/partial_contact_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["hide_controls"] = True
        return context


class PurchaseDataCreateView(LoginRequiredMixin, DispatchMixin, FormView):
    """ Capture purchase date, invoice etc """

    form_class = PurchaseDataForm
    template_name = "shop/purchase_data.html"

    def post(self, request, **kwargs):
        if "back" in request.POST:
            return redirect(session.back(self.index, request))
        return super().post(request)

    def form_valid(self, form):
        session.update_data(self.index, self.request, form)
        index = session.next_index(self.index, self.request)
        return redirect("purchase_lot_create", index)


class PurchaseLotCreateView(LoginRequiredMixin, DispatchMixin, FormView):
    """ Capture lot and its items on a dynamically generated form """

    form_class = PurchaseLotForm
    template_name = "shop/purchase_lot.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # The form only contains lot number & cost so need to add items
        items = self.initial.get("items", None)  # posted data exists
        if not items:
            if hasattr(self, "items"):  # after invalid POST that contains item data
                items = self.items
            else:
                items = [Item(name="")]  # first time through
        context["items"] = items
        return context

    def post(self, request, **kwargs):
        if "back" in request.POST:
            return redirect(session.back(self.index, request))
        # save any items on self for use when form is invalid because form does not handle them
        self.items = []
        for key in self.request.POST:
            if "item" in key:
                if self.request.POST[key]:
                    self.items.append(Item(name=self.request.POST[key]))
        form = self.get_form()

        if form.is_valid():
            if len(self.items) == 0:
                form.add_error(None, "At least one item must be specified")
                return self.form_invalid(form)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        # allocate cost and ref to items in the lot
        cost = form.cleaned_data["cost"]
        unit_cost = (cost / len(self.items)).quantize(
            Decimal("0.01"), rounding=ROUND_FLOOR
        )
        diff = cost - (unit_cost * len(self.items))
        for item in self.items:
            item.cost_price = unit_cost
        self.items[-1].cost_price += diff
        form.cleaned_data["items"] = self.items
        session.update_data(self.index, self.request, form)
        # reallocate all references
        PurchaseSummaryCreateView.allocate_refs(self.request, permanent=False)
        index = session.next_index(self.index, self.request)
        return redirect("purchase_summary", index)


class PurchaseSummaryCreateView(LoginRequiredMixin, DispatchMixin, TemplateView):
    """ Final stage of wizard. Allows costs to be updated"""

    template_name = "shop/purchase_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        i = 0
        posted = session.get_data(i, self.request)
        context["vendor"] = Contact.objects.get(id=posted["vendor_id"])
        i += 1
        posted = session.get_data(i, self.request)
        context["purchase"] = posted
        invoice_total = posted["invoice_total"]

        lots = []
        lots_total = Decimal(0)
        while True:
            i += 1
            lot = session.get_data(i, self.request)
            if lot:
                lots.append(lot)
                lots_total += lot["cost"]
                lot["total"] = Decimal(0)
                for item in lot["items"]:
                    lot["total"] += item.cost_price
            else:
                break
        context["lots"] = lots
        context["lots_total"] = lots_total
        remaining = invoice_total - lots_total
        context["remaining"] = remaining
        PurchaseSummaryCreateView.set_message(self.request, remaining)
        # index part of change_path gets updated by javascript to include the item ref
        context["change_path"] = reverse("purchase_summary_ajax", kwargs={"ref": 0})
        context["creating"] = True
        return context

    def post(self, request, **kwargs):
        if "back" in request.POST:
            return redirect(session.back(self.index, request))
        elif "lot" in request.POST:
            return redirect("purchase_lot_create", self.index)
        elif "save" in request.POST:
            vendor_id = session.get_data(0, request)["vendor_id"]
            data = session.get_data(1, request)
            with transaction.atomic():
                purchase = Purchase.objects.create(
                    date=data["date"],
                    invoice_number=data["invoice_number"],
                    invoice_total=data["invoice_total"],
                    buyers_premium=data["buyers_premium"],
                    vendor_id=vendor_id,
                    margin_scheme=data["margin_scheme"],
                    vat=data["vat"],
                )
                # Reallocate references just in case they have been used in another session
                PurchaseSummaryCreateView.allocate_refs(request, permanent=True)
                i = 2
                while i <= session.last_index(request):
                    data = session.get_data(i, request)
                    lot = Lot.objects.create(
                        number=data["number"], cost=data["cost"], purchase=purchase
                    )
                    for item in data["items"]:
                        item.lot = lot
                        item.save()
                    lot.save()
                    i += 1
                purchase.save()
            session.clear_data(request)
            return redirect("purchase_list")
        return redirect("purchase_summary", self.index)

    @classmethod
    def allocate_refs(cls, request, permanent=False):
        # allocate references across all lots stored in the session
        ref = ItemRef.get_next(increment=False) if permanent else request.session["ref"]
        i = 2
        while i <= session.last_index(request):
            data = session.get_data(i, request)
            for item in data["items"]:
                item.ref = ref
                ref = (
                    ItemRef.get_next(increment=True)
                    if permanent
                    else ItemRef.increment(ref)
                )
            i += 1

    @classmethod
    def set_message(cls, request, remaining):
        """ defines message to put at top of screen, used also outside creation """
        if remaining > 0:
            level = messages.WARNING
            message = f"There is still £{remaining} unallocated"
        elif remaining < 0:
            level = messages.ERROR
            message = (
                f"The allocated lot costs exceed the invoice total by £{-remaining}."
            )
        else:
            level = messages.SUCCESS
            message = "Invoice total matches allocated item costs"
        messages.add_message(request, level, message)


class PurchaseSummaryAjaxView(LoginRequiredMixin, AjaxCrudView):
    """
    Handle changes to item costs.
    Can be called by wizard during creation when purchase summary is non modal
    or by detail view when the purchase summary is a modal
    """

    form_class = UpdateItemForm
    template_name = "shop/includes/partial_purchase_item.html"

    def get_object(self, **kwargs):
        self.object, _ = self.get_item(**kwargs)
        return self.object

    def get_item(self, **kwargs):
        """ fetch object data from session"""
        ref = kwargs.get("ref", None)
        if ref:
            i = 2
            while True:
                data = session.get_data(i, self.request)
                if data:
                    if data["form_class"] == "PurchaseLotForm":
                        for item in data["items"]:
                            if item.ref == ref:
                                return item, True
                    i += 1
                break
            item = Item.objects.get(ref=ref)
            return item, False
        return None, False

    def get_form(self, **kwargs):
        item, _ = self.get_item(**kwargs)
        data = {"name": item.name, "cost_price": item.cost_price}
        self.form = self.form_class(data)

    def save_object(self, **kwargs):
        item, _session = self.get_item(**kwargs)
        if item and session:
            item.cost_price = self.form.cleaned_data["cost_price"]
            item.name = self.form.cleaned_data["name"]
            self.request.session.modified = True
            self.object = None
        else:
            super().save_object(**kwargs)

    def get_context_data(self):
        context = super().get_context_data()
        context["submit_path"] = self.request.path
        return context


class PurchaseListView(LoginRequiredMixin, FilteredTableView):
    """ Show purchases in a generic table """

    model = Purchase
    table_class = PurchaseTable
    filter_class = PurchaseFilter
    filter_left = True
    allow_detail = True

    def get_queryset(self):
        return Purchase.objects.all().order_by("-id")

    def get_initial_data(self):
        initial = super().get_initial_data()
        initial["from_date"] = date(2018, 1, 1)
        initial["to_date"] = date(2020, 1, 1)
        return initial

    def get_buttons(self):
        return [("Export to Excel", "export")]


class PurchaseDetailAjax(LoginRequiredMixin, AjaxCrudView):
    """ Show Purchase summary in a modal over the PurchaseListView"""

    model = Purchase
    template_name = "shop/includes/partial_purchase_summary.html"
    modal_class = "modal-lg"

    def get_context_data(self):
        context = super().get_context_data()
        try:
            vendor = Contact.objects.get(id=self.object.vendor_id)
        except:
            Contact.DoesNotExist
            vendor = None
        context["vendor"] = vendor
        context["purchase"] = self.object
        lots = self.object.lot_set.all().order_by("pk")
        error = False
        for lot in lots:
            lot.items = []
            lot.total = Decimal(0)
            for item in lot.item_set.all().order_by("pk"):
                lot.items.append(item)
                lot.total += item.cost_price
            lot.error = lot.total - lot.cost
            if lot.error != 0:
                error = True
            lot.can_update = len(lot.items) > 1
        context["lots"] = lots
        context["error"] = error
        context["change_path"] = reverse("purchase_item_ajax", kwargs={"pk": 0})
        context["creating"] = False
        return context


class PurchaseItemAjax(LoginRequiredMixin, AjaxCrudView):
    """ Show second modal over PurchaseDetailAjax modal to change item cost """

    model = Item
    form_class = UpdateItemForm
    modal_id = "#modal-form-2"
    update = True
    template_name = "shop/includes/partial_purchase_item.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["submit_path"] = self.request.path
        return context
