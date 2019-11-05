from decimal import *
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, TemplateView, CreateView, FormView
from django.shortcuts import redirect
from shop.forms import (
    NewVendorForm,
    PurchaseVendorForm,
    PurchaseDataForm,
    NewItemForm,
    PurchaseCostForm,
    PurchaseExpenseForm,
)
from shop.models import Contact, Purchase, Item, PurchaseExpense
from shop.tables import PurchaseTable
from shop.views.generic_views import FilteredTableView, AjaxCrudView
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
    """ Starts a new wizard """

    def get(self, request):
        session.clear(request)
        return redirect("purchase_create", 0)


class PurchaseCreateView(LoginRequiredMixin, DispatchMixin, FormView):
    """ Capture details of the vendor"""

    form_class = PurchaseVendorForm
    template_name = "shop/purchase_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor_id = self.initial.get("vendor_id", None)
        context["vendor"] = get_vendor(vendor_id)
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
        return redirect("purchase_item_create", index)


class PurchaseExpenseCreateView(LoginRequiredMixin, DispatchMixin, FormView):
    """ Add an expense record to a purchase """

    form_class = PurchaseExpenseForm
    template_name = "shop/purchase_expense.html"

    def post(self, request, **kwargs):
        if "back" in request.POST:
            if self.index > session.last_index(request):
                return redirect("purchase_summary", self.index)
            return redirect(session.back(self.index, request))
        return super().post(request)

    def form_valid(self, form):
        session.update_data(self.index, self.request, form)
        return session.redirect_next(self.index, self.request, "purchase_summary")


class PurchaseItemCreateView(LoginRequiredMixin, DispatchMixin, FormView):
    """ Capture item detail """

    form_class = NewItemForm
    template_name = "shop/purchase_item.html"

    def post(self, request, **kwargs):
        if "back" in request.POST:
            if self.index > session.last_index(request):
                return redirect("purchase_summary", self.index)
            return redirect(session.back(self.index, request))
        return super().post(request)

    def form_valid(self, form):
        session.update_data(self.index, self.request, form)
        return session.redirect_next(self.index, self.request, "purchase_summary")


class PurchaseSummaryCreateView(LoginRequiredMixin, DispatchMixin, TemplateView):
    """ Final stage of wizard. Allows costs to be updated"""

    template_name = "shop/purchase_summary.html"

    def post(self, request, **kwargs):
        if "back" in request.POST:
            return redirect(session.back(self.index, request))
        elif "item" in request.POST:
            return redirect("purchase_item_create", self.index)
        elif "expense" in request.POST:
            return redirect("purchase_expense_create", self.index)
        elif "save" in request.POST:
            vendor_id = session.get_data(0, request)["vendor_id"]
            data = session.get_data(1, request)
            purchase = Purchase.objects.create(
                date=data["date"],
                invoice_number=data["invoice_number"],
                invoice_total=data["invoice_total"],
                buyers_premium=data["buyers_premium"],
                cost_lot=data["cost_lot"],
                lot_number=data["lot_number"],
                vendor_id=vendor_id,
                paid_date=data["paid_date"],
                margin_scheme=data["margin_scheme"],
                vat=data["vat"],
            )
            i = 2
            while i <= session.last_index(request):
                data = session.get_data(i, request)
                item = Item.objects.create(
                    name=data["name"],
                    cost_price=data["cost_price"],
                    purchase_data=purchase,
                )
                i += 1
            return redirect("purchase_list")
        return redirect("purchase_summary", self.index)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expenses_total = Decimal(0)
        items_total = Decimal(0)
        expenses = []
        items = []
        i = 0
        posted = session.get_data(i, self.request)
        context["vendor"] = get_vendor(posted["vendor_id"])
        i += 1
        posted = session.get_data(i, self.request)
        context["invoice_total"] = posted["invoice_total"]
        context["cost_lot"] = posted["cost_lot"]

        context["vendor"] = Contact.objects.get(id=self.object.vendor_id)
        context["date"] = self.object.date
        context["invoice_number"] = self.object.invoice_number
        context["invoice_total"] = self.object.invoice_total
        context["lot_no"] = self.object.lot_number
        context["buyers_premium"] = self.object.buyers_premium
        context["cost_lot"] = self.object.cost_lot
        while True:
            i += 1
            posted = session.get_data(i, self.request)
            if posted:
                if posted["form_class"] == PurchaseExpenseForm.__name__:
                    expenses.append([posted["description"], posted["amount"]])
                    expenses_total += posted["amount"]
                elif posted["form_class"] == NewItemForm.__name__:
                    items.append([posted["name"], posted["cost_price"], str(i)])
                    items_total += posted["cost_price"]
            else:
                break
        context["expenses"] = expenses
        context["expenses_total"] = expenses_total
        context["items"] = items
        context["items_total"] = items_total
        context["remaining"] = context["cost_lot"] - items_total
        context["excess"] = items_total - context["cost_lot"]
        return context


class PurchaseSummaryAjaxView(LoginRequiredMixin, AjaxCrudView):
    """ Handles updates to item costs """

    form_class = NewItemForm
    template_name = "shop/includes/partial_purchase_item.html"

    def get_posted(self, **kwargs):
        """ fetch object data from session"""
        index = kwargs.get("index", None)
        if index:
            return session.get_data(index, self.request)
        return None

    def get_form(self, **kwargs):
        data = self.get_posted(**kwargs)
        self.form = self.form_class(data)

    def save_object(self, **kwargs):
        index = kwargs.get("index", None)
        if index:
            session.update_data(index, self.request, self.form)
            self.request.session.modified = True
            self.object = None
        else:
            super().save_object(**kwargs)


class PurchaseListView(LoginRequiredMixin, FilteredTableView):
    model = Purchase
    table_class = PurchaseTable
    allow_detail = True
    modal_class = "modal-lg"

    def get_queryset(self):
        return Purchase.objects.all().order_by("-id")


class PurchaseDetailAjax(LoginRequiredMixin, AjaxCrudView):
    model = Purchase
    template_name = "shop/includes/partial_purchase_summary.html"

    def get_context_data(self):
        context = super().get_context_data()
        items_total = Decimal(0)
        context["vendor"] = Contact.objects.get(id=self.object.vendor_id)
        context["date"] = self.object.date
        context["invoice_number"] = self.object.invoice_number
        context["invoice_total"] = self.object.invoice_total
        context["lot_no"] = self.object.lot_number
        context["buyers_premium"] = self.object.buyers_premium
        context["cost_lot"] = self.object.cost_lot

        context["purchase"] = self.object
        items = self.object.item_set.all().order_by("pk")
        for item in items:
            items_total += item.cost_price
        context["items"] = items
        context["items_total"] = items_total
        context["remaining"] = context["cost_lot"] - items_total
        context["excess"] = items_total - context["cost_lot"]
        context["can_update"] = len(items) > 1
        return context


class PurchaseItemAjax(LoginRequiredMixin, AjaxCrudView):
    """ Handles updates to item costs in a purchase after creation """

    model = Item
    form_class = NewItemForm
    template_name = "shop/includes/partial_purchase_item.html"


def get_vendor(vendor_id):
    if vendor_id:
        try:
            vendor = Contact.objects.get(id=vendor_id)
            name = vendor.company
            if vendor.first_name:
                name = f"{vendor.first_name} {name}"
            return f"{name}\n{vendor.address}"
        except Contact.DoesNotExist:
            return "Vendor not found"
    return "No vendor id"
