import django.forms as forms
from django.urls import reverse_lazy
from django.forms import Form, ModelForm, ModelChoiceField, ValidationError
from tempus_dominus.widgets import DatePicker
from shop.models import (
    Item,
    Category,
    Purchase,
    Lot,
    Contact,
    Address,
    Book,
    Compiler,
    InvoiceCharge,
    Photo,
)


class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ("name", "short_name", "description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent_category"] = ModelChoiceField(
            empty_label=None,
            required=False,
            queryset=Category.objects.allowed_parents(self.instance),
        )

    category_ref = forms.CharField(required=False, label="Item ref for category image")
    archive_ref = forms.CharField(required=False, label="Item ref for archive image")

    def clean_parent_category(self):
        parent = self.cleaned_data["parent_category"]
        if parent is None:
            if self.instance and self.instance.get_root().pk == self.instance.pk:
                return parent
            raise forms.ValidationError("Parent category cannot be empty")
        return parent


class ItemCategoriseForm(ModelForm):
    class Meta:
        model = Category
        fields = ("id",)

    new_category = ModelChoiceField(
        empty_label=None,
        required=True,
        queryset=Category.objects.all().order_by("name"),
    )


class ItemForm(ModelForm):
    class Meta:
        model = Item
        fields = (
            "name",
            "description",
            "category",
            "dimensions",
            "condition",
            "provenance",
            "notes",
            "ref",
            "cost_price",
            "restoration_cost",
            "sale_price",
            "minimum_price",
            "archive",
            "state",
            "location",
            "visible",
            "show_price",
            "featured",
            "done",
            "book",
            "rank",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "provenance": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    category = forms.ChoiceField(required=True, choices=Category.objects.leaf_choices())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cost_price"].widget.attrs["readonly"] = "readonly"

    def clean_rank(self):
        rank = self.cleaned_data["rank"]
        if rank < 1 or rank > 10:
            raise forms.ValidationError("Rank must be between 1 and 10")
        return self.cleaned_data["rank"]


class ArchiveItemForm(ItemForm):
    title = "Archive Item"

    class Meta(ItemForm.Meta):
        model = Item
        exclude = ("minimum_price", "archive", "location", "show_price", "featured")


class UpdateItemForm(ModelForm):
    class Meta:
        model = Item
        fields = ("name", "cost_price")

    cost_price = forms.DecimalField(max_digits=8, decimal_places=2, required=True)


class ImageForm(Form):

    limit = forms.ChoiceField(
        label="Resize image",
        required=False,
        choices=(
            (0, "No resize"),
            (1000, "Resize to 1000x1000"),
            (2000, "Resize to 2000x2000"),
            (3000, "Resize to 3000x3000"),
            (4000, "Resize to 4000x4000"),
            (5000, "Resize to 5000x5000"),
        ),
    )
    crop = forms.BooleanField(label="Crop nearly square images", required=False)


class CartPriceForm(ModelForm):
    class Meta:
        model = Item
        fields = ("sale_price", "agreed_price")

    sale_price = forms.DecimalField(max_digits=8, decimal_places=2, required=False)
    # agreed_price is just used stored temporarily in the session instance
    agreed_price = forms.DecimalField(max_digits=8, decimal_places=2, required=True)

    def clean_sale_price(self):
        # Because this field is disabled and not required we need to reset its value
        # or it gets set to None
        if "sale_price" in self.initial:
            self.cleaned_data["sale_price"] = self.initial["sale_price"]
        return self.cleaned_data["sale_price"]


class InvoiceChargeForm(ModelForm):
    class Meta:
        model = InvoiceCharge
        fields = ("charge_type", "description", "amount")


class InvoiceBuyerForm(forms.Form):
    contact_id = forms.IntegerField(required=True, widget=forms.HiddenInput)


class InvoiceCreateForm(forms.Form):
    # invoice_date is marked as required but is ignored for proforma invoices
    invoice_date = forms.DateField(
        required=True,
        widget=DatePicker(
            options={"useCurrent": True},
            attrs={"append": "fa fa-calendar", "icon_toggle": True},
        ),
    )
    # proforma is set by custom radio buttons
    proforma = forms.BooleanField(required=False, widget=forms.HiddenInput)


class ContactForm(ModelForm):
    class Meta:
        model = Contact
        fields = ("first_name", "company", "notes", "vendor", "restorer", "buyer")

    first_name = forms.CharField(label="Name (optional)", required=False)
    company = forms.CharField(label="Last name/Company", required=True)
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 5}))
    work_phone = forms.CharField(max_length=20, required=False)
    mobile_phone = forms.CharField(max_length=20, required=False)
    email = forms.EmailField(max_length=80, required=False)


class AddressForm(ModelForm):
    class Meta:
        model = Address
        fields = ("address", "work_phone", "mobile_phone", "email")


class NewVendorForm(ContactForm):
    class Meta(ContactForm.Meta):
        exclude = ("vendor", "restorer", "buyer")

    title = "Create new vendor"
    path = reverse_lazy("contact_create")


class NewContactForm(ContactForm):
    class Meta(ContactForm.Meta):
        exclude = ("vendor", "restorer", "buyer")

    title = "Create new buyer"
    path = reverse_lazy("contact_create")


class EnquiryForm(ModelForm):
    class Meta:
        model = Contact
        fields = ("first_name", "last_name")

    email = forms.EmailField(max_length=100, required=True)
    subject = forms.CharField(max_length=50, required=False)
    message = forms.CharField(
        max_length=2000, required=False, widget=forms.Textarea(attrs={"rows": 3})
    )
    mail_consent = forms.BooleanField(
        required=False, label="Please add me to your mailing list"
    )


class BookForm(ModelForm):
    class Meta:
        model = Book
        fields = ("title", "author", "description", "subtitle", "compiler")

    compiler = ModelChoiceField(queryset=Compiler.objects.all(), required=False)


class CompilerForm(ModelForm):
    class Meta:
        model = Compiler
        fields = ("name", "description")


class PurchaseVendorForm(forms.Form):
    contact_id = forms.CharField(
        max_length=10, required=False, widget=forms.HiddenInput()
    )


class PurchaseForm(ModelForm):
    class Meta:
        model = Purchase
        fields = (
            "date",
            "invoice_number",
            "invoice_total",
            "buyers_premium",
            # "vendor",
            "margin_scheme",
            "vat",
        )

    new_vendor = forms.BooleanField(
        widget=forms.RadioSelect(
            choices=((False, "Search existing vendors"), ("True", "Create new vendor"))
        )
    )
    vendor_search = forms.CharField(
        max_length=50,
        label="Vendor",
        help_text="Type 3 or more letters to search by company name",
    )
    date = forms.DateField(
        widget=DatePicker(
            options={"useCurrent": True},
            attrs={"append": "fa fa-calendar", "icon_toggle": True},
        )
    )


class PurchaseLotForm(ModelForm):
    class Meta:
        model = Lot
        fields = ("number", "cost")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields["cost"].required = True


class PurchaseDataForm(ModelForm):
    class Meta:
        model = Purchase
        fields = (
            "date",
            "invoice_number",
            "invoice_total",
            "buyers_premium",
            "margin_scheme",
            "vat",
        )

    date = forms.DateField(
        widget=DatePicker(
            options={"useCurrent": True},
            attrs={"prepend": "fa fa-calendar", "icon_toggle": True},
        ),
        label="Purchase date",
        required=True,
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set required fields here.
        # They are allowed to be empty in the model to cope with old incomplete imported data
        self.fields["invoice_number"].required = True
        self.fields["invoice_total"].required = True

    def clean(self):
        cleaned_data = super().clean()
        if len(self.errors) == 0:
            total = cleaned_data["invoice_total"]
            premium = cleaned_data["buyers_premium"]
            if not premium:
                premium = 0
                cleaned_data["buyers_premium"] = 0
            vat = cleaned_data["vat"]
            if not vat:
                vat = 0
                cleaned_data["vat"] = 0
            if not cleaned_data["margin_scheme"] and vat == 0:
                raise forms.ValidationError(
                    f"VAT cannot be zero when outside the margin sheme."
                )
            # sum = cost + premium + vat
            # if sum != total:
            #     raise forms.ValidationError(
            #         f"The sum of the fields (£{sum}) does not equal the invoice total."
            #     )


class PurchaseCostForm(forms.Form):
    new_cost = forms.DecimalField(max_digits=8, decimal_places=2, required=True)
    item_id = forms.CharField(required=False, widget=forms.HiddenInput)


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ("file",)
