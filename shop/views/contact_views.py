from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponseNotFound, HttpResponse
from django.views.generic import CreateView, UpdateView
from django_htmx.http import HttpResponseClientRefresh, trigger_client_event
from shop.models import Contact, Enquiry, Address
from shop.forms import ContactForm, EnquiryForm
from shop.tables import ContactTable, ContactTableTwo, EnquiryTable, MailListTable
from table_manager.views import FilteredTableView, AjaxCrudView
from tables_plus.views import TablesPlusView, ModalMixin
from tables_plus.buttons import Button
from shop.filters import ContactFilter, EnquiryFilter


class ContactListView(LoginRequiredMixin, TablesPlusView):
    title = "Contacts"
    template_name = "shop/table.html"
    table_class = ContactTable
    filterset_class = ContactFilter
    filter_style = TablesPlusView.FilterStyle.HEADER
    click_url_name = "contact_update"
    click_method = "hxget"

    def get_queryset(self):
        return Contact.objects.all().prefetch_related("main_address").order_by("company")

    def get_buttons(self):
        return [Button("New contact", hx_get=reverse("contact_create"), hx_target="#modals-here")]

    def row_clicked(self, pk, target, url):
        return

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


class ContactCreateView(LoginRequiredMixin, ModalMixin, CreateView):
    model = Contact
    form_class = ContactForm
    modal_template_name = "shop/includes/modal_contact_form.html"
    title = "Create contact"

    def form_valid(self, form):
        contact = form.save()
        data = form.cleaned_data
        adr = Address.objects.create(
            address=data["address"],
            work_phone=data["work_phone"],
            mobile_phone=data["mobile_phone"],
            email=data["email"],
            contact=contact,
        )
        contact.main_address = adr
        contact.save()
        return HttpResponseClientRefresh()


class ContactUpdateView(LoginRequiredMixin, ModalMixin, UpdateView):
    model = Contact
    form_class = ContactForm
    modal_template_name = "shop/includes/modal_contact_form.html"
    title = "Update contact"
    allow_delete = True

    def get_form_kwargs(self):
        """add data from latest linked address object"""
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

    def form_invalid(self, form):
        return super().form_invalid(form)

    def form_valid(self, form):
        contact = form.save()
        adr = contact.main_address
        data = form.cleaned_data
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
                contact=contact,
            )
            contact.main_address = adr
            contact.save()
            messages.info(self.request, f"New address for {self.object.name} created")
        response = HttpResponse("")
        return trigger_client_event(response, "trigger", {"url": self.request.htmx.current_url_abs_path})

    @staticmethod
    def unformat(address):
        return address.replace(" ", "").replace("\r", "").replace("\n", "")


class EnquiryListView(LoginRequiredMixin, TablesPlusView):
    model = Enquiry
    table_class = EnquiryTable
    filterset_class = EnquiryFilter
    allow_detail = True
    template_name = "shop/table.html"

    def get_queryset(self):
        return Enquiry.objects.all().order_by("-id")

    def get_actions(self):
        return [
            ("set_open", "Set open"),
            ("set_closed", "Set closed"),
            ("delete", "Delete"),
        ]

    def handle_action(self, request):
        if "set_open" in request.POST:
            self.selected_objects.update(closed=False)
        elif "set_closed" in request.POST:
            self.selected_objects.update(closed=True)
        elif "delete" in request.POST:
            self.selected_objects.delete()


class EnquiryDetailAjax(LoginRequiredMixin, AjaxCrudView):
    model = Enquiry
    allow_delete = True
    template_name = "shop/enquiry_detail.html"

    def handle_action(self, action, **kwargs):
        if action == "open":
            self.object.closed = False
        elif action == "close":
            self.object.closed = True
        self.object.save()
        return


class ContactCreateAjax(LoginRequiredMixin, AjaxCrudView):
    """Create a new vendor in modal within the PurchaseCreateView"""

    model = Contact
    form_class = ContactForm
    template_name = "shop/includes/partial_contact_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["hide_controls"] = True
        return context


def contact_lookup(request, pk=None):
    """Lookup for typeahead function"""
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


class MailListView(LoginRequiredMixin, FilteredTableView):
    model = Contact
    table_class = MailListTable
    table_pagination = {"per_page": 10}
    allow_detail = True
    template_name = "table_manager/htmx_table.html"
    # templaate_name = "shop/filtered_table.html"
    # template_name = "table_manager/generic_table.html"

    def get_queryset(self):
        return Contact.objects.filter(mail_consent=True)

    def get_actions(self):
        return [
            ("remove_consent", "Remove mail consent"),
            ("export", "Export to Excel"),
        ]

    def handle_action(self, request):
        if "remove_consent" in request.POST:
            self.selected_objects.update(mail_consent=False)
