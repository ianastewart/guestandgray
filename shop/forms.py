from django.forms import ModelForm, ModelChoiceField, ValidationError
from shop.models import Item, Category


class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ("name", "short_name", "description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent_category"] = ModelChoiceField(
            queryset=Category.objects.all().order_by("depth", "name")
        )

    def clean(self):
        current_parent = self.instance.get_parent()
        new_parent = self.cleaned_data["parent_category"]
        if current_parent.id != new_parent.id:
            if new_parent.is_descendant_of(self.instance):
                raise ValidationError(
                    "You cannot make a category report to one of its children"
                )
        return self.cleaned_data


class ItemForm(ModelForm):
    title = "Item"

    class Meta:
        model = Item
        fields = ("name", "ref", "description", "price", "category")
