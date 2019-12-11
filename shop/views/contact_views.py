from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseNotFound
from shop.models import Contact, Enquiry
from shop.forms import ContactForm
from shop.tables import ContactTable, ContactTableTwo, EnquiryTable
from table_manager.views import FilteredTableView, AjaxCrudView
from shop.filters import ContactFilter


class ContactListView(LoginRequiredMixin, FilteredTableView):
    model = Contact
    table_class = ContactTable
    filter_class = ContactFilter
    heading = "Contacts"
    table_pagination = {"per_page": 100}
    allow_create = True
    allow_update = True

    def get_queryset(self):
        return Contact.objects.all().order_by("last_name")


class VendorListView(ContactListView):
    table_class = ContactTableTwo
    heading = "Vendors"

    def get_queryset(self):
        return Contact.objects.filter(vendor=True).order_by("company")


class BuyerListView(ContactListView):
    table_class = ContactTableTwo
    heading = "Buyers"

    def get_queryset(self):
        return Contact.objects.filter(buyer=True).order_by("company")


class ContactCreateView(LoginRequiredMixin, AjaxCrudView):
    model = Contact
    form_class = ContactForm
    template_name = "shop/includes/partial_contact_form.html"


class ContactUpdateView(LoginRequiredMixin, AjaxCrudView):
    model = Contact
    form_class = ContactForm
    template_name = "shop/includes/partial_contact_form.html"
    update = True
    allow_delete = True


class EnquiryListView(LoginRequiredMixin, FilteredTableView):
    model = Enquiry
    table_class = EnquiryTable
    table_pagination = {"per_page": 10}
    allow_update = True

    def get_queryset(self):
        return Enquiry.objects.all().order_by("-date")


class ContactCreateAjax(LoginRequiredMixin, AjaxCrudView):
    """ Create a new vendor in modal within the PurchaseCreateView """

    model = Contact
    form_class = ContactForm
    template_name = "shop/includes/partial_contact_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["hide_controls"] = True
        return context


def vendor_lookup(request, pk=None):
    """ Lookup for typeahead function """
    if request.user.is_authenticated and request.is_ajax():
        results = []
        q = request.GET.get("term", "").lower()
        if "pk=" in q:
            pk = q.split("=")[1]
            vendors = Contact.objects.filter(pk=pk)
        else:
            vendors = Contact.objects.filter(company__icontains=q).order_by("company")
        for vendor in vendors:
            name = f"{vendor.company}"
            if vendor.first_name:
                name = f"{vendor.first_name} {name}"
            value = f"{name}, {vendor.address[:15]}"
            html = name + "<br>" + vendor.address.replace("\n", "<br>")
            dict = {"id": vendor.id, "value": value, "html": html}
            results.append(dict)
        return JsonResponse(results, safe=False)
    return HttpResponseNotFound
