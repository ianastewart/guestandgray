from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponseNotFound
from shop.models import Contact, Enquiry, Address
from shop.forms import ContactForm, EnquiryForm
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
        return (
            Contact.objects.all().prefetch_related("main_address").order_by("company")
        )


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

    def save_object(self, **kwargs):
        super().save_object(**kwargs)
        data = self.form.cleaned_data
        adr = Address.objects.create(
            address=data["address"],
            work_phone=data["work_phone"],
            mobile_phone=data["mobile_phone"],
            email=data["email"],
            contact=self.object,
        )
        self.object.main_address = adr
        self.object.save()


class ContactUpdateView(LoginRequiredMixin, AjaxCrudView):
    model = Contact
    form_class = ContactForm
    template_name = "shop/includes/partial_contact_form.html"
    update = True
    allow_delete = True

    def get_form_kwargs(self):
        """ add data from latest linked address object """
        kwargs = super().get_form_kwargs()
        adr = self.object.main_address
        kwargs["initial"]["email"] = adr.email
        kwargs["initial"]["work_phone"] = adr.work_phone
        kwargs["initial"]["mobile_phone"] = adr.mobile_phone
        kwargs["initial"]["address"] = adr.address
        return kwargs

    def get_context_data(self):
        context = super().get_context_data()
        context["addresses"] = self.object.addresses()
        return context

    def save_object(self, **kwargs):
        super().save_object(**kwargs)
        adr = self.object.main_address
        data = self.form.cleaned_data
        # ignore a reformatting of existing address
        if self.unformat(data["address"]) == self.unformat(adr.address):
            adr.address = data["address"]
            adr.work_phone = data["work_phone"]
            adr.mobile_phone = data["mobile_phone"]
            adr.email = data["email"]
            adr.save()
            messages.info(self.request, f"Address for {self.object.name} was updated")
        # create new record if address is really changed
        else:
            adr = Address.objects.create(
                address=data["address"],
                work_phone=data["work_phone"],
                mobile_phone=data["mobile_phone"],
                email=data["email"],
                contact=self.object,
            )
            self.object.main_address = adr
            self.object.save()
            messages.info(self.request, f"New address for {self.object.name} created")

    @staticmethod
    def unformat(address):
        return address.replace(" ", "").replace("\r", "").replace("\n", "")


class EnquiryListView(LoginRequiredMixin, FilteredTableView):
    model = Enquiry
    table_class = EnquiryTable
    table_pagination = {"per_page": 10}
    allow_detail = True
    template_name = "shop/filtered_table.html"

    def get_queryset(self):
        return Enquiry.objects.all().order_by("-date")


class EnquiryDetailAjax(LoginRequiredMixin, AjaxCrudView):
    model = Enquiry
    template_name = "shop/enquiry_detail.html"


class ContactCreateAjax(LoginRequiredMixin, AjaxCrudView):
    """ Create a new vendor in modal within the PurchaseCreateView """

    model = Contact
    form_class = ContactForm
    template_name = "shop/includes/partial_contact_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["hide_controls"] = True
        return context


def contact_lookup(request, pk=None):
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
            adr = vendor.main_address
            address_short = "No address"
            address = ""
            if adr:
                address_short = adr.address[:15]
                address = adr.address.replace("\n", "<br>")
            value = f"{name}, {address_short}"
            html = name + "<br>" + address
            dict = {"id": vendor.id, "value": value, "html": html}
            results.append(dict)
        return JsonResponse(results, safe=False)
    return HttpResponseNotFound
