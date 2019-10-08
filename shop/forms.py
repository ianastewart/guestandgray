from django.forms import ModelForm, ModelChoiceField, ValidationError
from shop.models import Item, Category


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
