from django.forms import ModelForm, ModelChoiceField
from shop.models import Object, Category


class CategoryForm(ModelForm):
    title = "Category"

    class Meta:
        model = Category
        fields = ("name", "image")


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
