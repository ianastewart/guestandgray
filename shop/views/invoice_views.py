from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse


from shop.models import Invoice
from shop.tables import InvoiceTable
from table_manager.views import FilteredTableView, AjaxCrudView
from shop.filters import InvoiceFilter
from shop.session import cart_invoice_to_session, push


class InvoiceDetailView(LoginRequiredMixin, AjaxCrudView):
    model = Invoice
    template_name = "shop/includes/partial_invoice_detail.html"
    modal_class = "modal-lg"

    def get_context_data(self):
        context = super().get_context_data()
        context["items"] = self.object.item_set.all().order_by("id")
        context["charges"] = self.object.invoicecharge_set.all().order_by("id")
        context["total"] = self.object.total
        return context

    def post(self, request, **kwargs):
        invoice = self.get_object(**kwargs)
        if "paid" in request.POST:
            invoice.paid = True
            invoice.save()
        elif "update" in request.POST:
            cart_invoice_to_session(request, invoice)
            # push(request.session, reverse("cart_contents"))
            # return redirect("cart_contents")

        return super().post(request, **kwargs)


class InvoiceListView(LoginRequiredMixin, FilteredTableView):
    model = Invoice
    table_class = InvoiceTable
    table_pagination = {"per_page": 15}
    filter_class = InvoiceFilter
    allow_detail = True
    heading = "Invoices"

    def get_queryset(self):
        return Invoice.objects.all().order_by("-date")
