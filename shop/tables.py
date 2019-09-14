import django_tables2 as tables
from django.shortcuts import reverse
from django.utils.safestring import mark_safe


from django.utils.html import escape


from shop.models import Item


class ImageColumn(tables.Column):
    def render(self, value):
        image = value.get_rendition("max-100x100")
        return mark_safe(f'<img src="{image.file.url}">')


class ItemTable(tables.Table):
    class Meta:
        model = Item
        fields = ("selection", "name", "ref", "category.name", "price")
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {
            "data-url": lambda record: reverse("item_detail", kwargs={"pk": record.pk}),
            "class": "table-row pl-4",
        }

    image = ImageColumn(accessor="image")
    selection = tables.TemplateColumn(
        accessor="pk",
        template_name="django_tables2/custom_checkbox.html",
        verbose_name="Select",
    )
