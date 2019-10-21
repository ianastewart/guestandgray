import django.forms as forms
from django.forms import ModelForm, ModelChoiceField, ValidationError
from shop.models import Item, Category, Contact, Address, Book, Compiler


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
    title = "Item"

    class Meta:
        model = Item
        fields = (
            "name",
            "ref",
            "description",
            "price",
            "category",
            "dimensions",
            "condition",
            "provenance",
        )


class ContactForm(ModelForm):
    class Meta:
        model = Contact
        fields = (
            "title",
            "first_name",
            "last_name",
            "company",
            "work_phone",
            "mobile_phone",
            "email",
            "notes",
        )


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


class AddressForm(ModelForm):
    class Meta:
        model = Address
        fields = ("address1", "address2", "address3", "town", "post_code", "country")


class BookForm(ModelForm):
    class Meta:
        model = Book
        fields = ("title", "author", "description", "subtitle", "compiler")

    compiler = ModelChoiceField(
        queryset=Compiler.objects.all().order_by("name"), required=False
    )
