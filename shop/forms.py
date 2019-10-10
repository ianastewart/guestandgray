from django.forms import ModelForm, ModelChoiceField, ValidationError
from shop.models import Item, Category, Contact, Address


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
        fields = ("name", "ref", "description", "price", "category")


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


class AddressForm(ModelForm):
    class Meta:
        model = Address
        fields = ("address1", "address2", "address3", "town", "post_code", "country")
