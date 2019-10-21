import django_tables2 as tables
from django.shortcuts import reverse
from django.utils.safestring import mark_safe
from shop.truncater import truncate
from shop.models import Category, Item, Contact, Enquiry, Book, Compiler


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
        fields = ("selection", "name", "ref", "category.name", "price", "archive")
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
            "mail_consent",
            "notes",
        )
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}

    def render_mail_consent(self, value):
        return "Yes" if value else ""

    def render_notes(self, value):
        return "Yes" if value else ""


class EnquiryTable(tables.Table):
    class Meta:
        model = Enquiry
        fields = ("date", "subject", "message")
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}

    first_name = tables.Column(accessor="contact.first_name")
    last_name = tables.Column(accessor="contact.last_name")
    email = tables.Column(accessor="contact.email")
    mail_consent = tables.Column(accessor="contact.mail_consent")

    def render_mail_consent(self, value):
        return "Yes" if value else ""


class BookTable(tables.Table):
    class Meta:
        model = Book
        fields = ("title", "author", "description", "compiler.name")
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}

    title = tables.Column(attrs={"td": {"width": "20%"}})
    author = tables.Column(attrs={"td": {"width": "20%"}})
    description = tables.Column(orderable=False)


class CompilerTable(tables.Table):
    class Meta:
        model = Compiler
        fields = ("name", "description")
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}
