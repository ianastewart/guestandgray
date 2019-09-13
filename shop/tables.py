import django_tables2 as tables
from django.shortcuts import reverse
from shop.models import Item


class ItemTable(tables.Table):
    class Meta:
        model = Item
        fields = ("name", "ref", "category.name", "price")
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {
            "data-url": lambda record: reverse("item_detail", kwargs={"pk": record.pk}),
            "class": "table-row pl-4",
        }

    selection = tables.TemplateColumn(
        accessor="pk",
        template_name="django_tables2/custom_checkbox.html",
        verbose_name="Select",
    )
