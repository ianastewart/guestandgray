from django.forms import ModelForm, ModelChoiceField
from shop.models import Object, Section


class SectionForm(ModelForm):
    title = "Section"

    class Meta:
        model = Section
        fields = ("name", "image",)


class ObjectForm(ModelForm):
    title = "Object"

    class Meta:
        model = Object
        fields = ("name", "description", "price", "image_file", "section_text", "section")

    # category = ModelChoiceField(queryset=Category.objects.all(), to_field_name="name")
