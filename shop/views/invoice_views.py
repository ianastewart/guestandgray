from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse


from shop.models import Invoice
from shop.tables import InvoiceTable
from django.views.generic import DetailView
from tables_plus.views import TablesPlusView, ModalMixin
from shop.filters import InvoiceFilter
from shop.session import cart_invoice_to_session


class InvoiceListView(LoginRequiredMixin, TablesPlusView):
    model = Invoice
    table_class = InvoiceTable
    filterset_class = InvoiceFilter
    template_name = "shop/table.html"
    title = "Invoices"
    click_method = "hxget"
    click_url_name = "invoice_detail"

    def get_queryset(self):
        return Invoice.objects.all().order_by("-date", "id")


class InvoiceDetailView(LoginRequiredMixin, ModalMixin, DetailView):
    model = Invoice
    template_name = "shop/invoice_detail_modal.html"
    modal_class = "modal-lg"

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["items"] = self.object.item_set.all().order_by("id")
        context["charges"] = self.object.invoicecharge_set.all().order_by("id")
        context["total"] = self.object.total
        self.title = f"Invoice number {self.object.number}"
        return context

    def post(self, request, **kwargs):
        invoice = self.get_object(**kwargs)
        if "paid" in request.POST:
            invoice.paid = True
            invoice.save()
        elif "update" in request.POST:
            cart_invoice_to_session(request, invoice)
        return super().post(request, **kwargs)
