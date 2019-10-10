import django_tables2 as tables
from django.shortcuts import reverse
from django.utils.safestring import mark_safe
from shop.truncater import truncate
from shop.models import Category, Item, Contact


class CategoryTable(tables.Table):
    class Meta:
        model = Category
        fields = ("name", "parent", "description", "image", "count")
        # sequence = ("name", "description", "image", "count", "dad")
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {
            "data-url": lambda record: reverse(
                "category_detail", kwargs={"pk": record.pk}
            ),
            "class": "table-row pl-4",
        }

    parent = tables.Column(empty_values=())

    def render_description(self, value):
        if len(value) > 80:
            return value[:80] + "..."

    def render_parent(self, record):
        return record.get_parent().name


class ImageColumn(tables.Column):
    def render(self, value):
        image = value.get_rendition("max-100x100")
        return mark_safe(f'<img src="{image.file.url}">')


class ItemTable(tables.Table):
    class Meta:
        model = Item
        fields = ("selection", "name", "ref", "category.name", "price")
        attrs = {"class": "table table-sm table-hover hover-link"}
        # row_attrs = {
        #     "data-url": lambda record: reverse("item_detail", kwargs={"pk": record.pk}),
        #     "class": "table-row pl-4",
        # }
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}

    image = ImageColumn(accessor="image")
    selection = tables.TemplateColumn(
        accessor="pk",
        template_name="django_tables2/custom_checkbox.html",
        verbose_name="Select",
    )


class ItemNameTable(tables.Table):
    class Meta:
        model = Item
        fields = ("name", "description", "ref")

        attrs = {"class": "table table-sm table-hover hover-link"}
        # row_attrs = {
        #             "data-url": lambda record: reverse("item_update", kwargs={"pk": record.pk}),
        #             "class": "table-row pl-4",
        #         }
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}

    name = tables.Column(accessor="description", attrs={"td": {"width": "33%"}})

    def render_name(self, value):
        return truncate(value, 60)


class ContactTable(tables.Table):
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
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}
