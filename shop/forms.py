import django.forms as forms
from django.urls import reverse_lazy
from django.forms import ModelForm, ModelChoiceField, ValidationError
from tempus_dominus.widgets import DatePicker
from shop.models import (
    Item,
    Category,
    Purchase,
    PurchaseExpense,
    Contact,
    Book,
    Compiler,
)


class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ("name", "short_name", "description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent_category"] = ModelChoiceField(
            empty_label=None,
            queryset=Category.objects.all()
            .exclude(
                pk__in=self.instance.get_descendants().values_list("pk", flat=True)
            )
            .exclude(pk__in=[self.instance.pk])
            .order_by("name"),
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
            "ref",
            "purchase_date",
            "cost_price",
            "restoration_cost",
            "sale_price",
            "minimum_price",
            "archive",
            "location",
            "visible",
            "show_price",
            "featured",
        )


class ArchiveItemForm(ItemForm):
    title = "Archive Item"

    class Meta(ItemForm.Meta):
        model = Item
        exclude = (
            "minimum_price",
            "archive",
            "location",
            "visible",
            "show_price",
            "featured",
        )


class NewItemForm(ModelForm):
    class Meta:
        model = Item
        fields = ("name", "cost_price")

    cost_price = forms.DecimalField(max_digits=8, decimal_places=2, required=True)


class ContactForm(ModelForm):
    class Meta:
        model = Contact
        fields = (
            "first_name",
            "company",
            "address",
            "work_phone",
            "mobile_phone",
            "email",
            "notes",
            "vendor",
            "restorer",
            "buyer",
        )

    first_name = forms.CharField(label="Name (optional)", required=False)
    company = forms.CharField(label="Last name/Company", required=True)
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class NewVendorForm(ContactForm):
    class Meta(ContactForm.Meta):
        exclude = ("vendor", "restorer", "buyer")

    title = "Create new vendor"
    path = reverse_lazy("contact_create")


class EnquiryForm(ModelForm):
    class Meta:
        model = Contact
        fields = ("first_name", "last_name", "mobile_phone", "email")

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
    vendor_id = forms.CharField(
        max_length=10, required=False, widget=forms.HiddenInput()
    )


class PurchaseForm(ModelForm):
    class Meta:
        model = Purchase
        fields = (
            "date",
            "invoice_number",
            "lot_number",
            "invoice_total",
            "buyers_premium",
            # "vendor",
            "paid_date",
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


class PurchaseExpenseForm(ModelForm):
    class Meta:
        model = PurchaseExpense
        fields = "description", "amount", "eligible"


class PurchaseDataForm(ModelForm):
    class Meta:
        model = Purchase
        fields = (
            "date",
            "invoice_number",
            "lot_number",
            "cost_lot",
            "invoice_total",
            "buyers_premium",
            "margin_scheme",
            "vat",
            "paid_date",
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
        self.fields["cost_lot"].required = True
        self.fields["invoice_total"].required = True

    def clean(self):
        cleaned_data = super().clean()
        if len(self.errors) == 0:
            cost = cleaned_data["cost_lot"]
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
            sum = cost + premium + vat
            if sum != total:
                raise forms.ValidationError(
                    f"The sum of the fields (£{sum}) does not equal the invoice total."
                )


class PurchaseCostForm(forms.Form):
    new_cost = forms.DecimalField(max_digits=8, decimal_places=2, required=True)
    item_id = forms.CharField(required=False, widget=forms.HiddenInput)
