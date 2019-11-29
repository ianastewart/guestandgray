import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from shop.models import Invoice
from shop.tables import InvoiceTable
from table_manager.views import FilteredTableView, AjaxCrudView
from shop.filters import InvoiceFilter

logger = logging.getLogger(__name__)


class StaffHomeView(LoginRequiredMixin, TemplateView):
    template_name = "shop/staff_home.html"


class InvoiceDetailView(LoginRequiredMixin, AjaxCrudView):
    model = Invoice
    template_name = "shop/includes/partial_invoice_detail.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["items"] = self.object.item_set.all()
        context["extras"] = self.object.invoiceextra_set.all()
        return context


class InvoiceListView(LoginRequiredMixin, FilteredTableView):
    model = Invoice
    table_class = InvoiceTable
    table_pagination = {"per_page": 15}
    filter_class = InvoiceFilter
    allow_detail = True
    heading = "Invoices"

    def get_queryset(self):
        return Invoice.objects.all().order_by("-date")
