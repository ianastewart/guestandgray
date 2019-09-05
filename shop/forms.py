from django.forms import ModelForm, ModelChoiceField, ValidationError
from treebeard.exceptions import InvalidMoveToDescendant
from shop.models import Object, Category


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
            if self.instance.is_descendant_of(new_parent):
                raise ValidationError(
                    "You cannot make a category report to one of its children"
                )
        return self.cleaned_data


class ObjectForm(ModelForm):
    title = "Object"

    class Meta:
        model = Object
        fields = (
            "name",
            "ref",
            "description",
            "price",
            "image_file",
            "category_text",
            "category",
        )

    # category = ModelChoiceField(queryset=Category.objects.all(), to_field_name="name")
