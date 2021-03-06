import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.contrib.humanize.templatetags.humanize import intcomma
from django_tables2.utils import A
from django_tables2_column_shifter.tables import ColumnShiftTable
from table_manager.tables import *
from shop.models import (
    Category,
    Item,
    Invoice,
    Purchase,
    Contact,
    Enquiry,
    Book,
    Compiler,
)


class CategoryTable(tables.Table):
    class Meta:
        model = Category
        fields = ("name", "parent", "description", "image", "count")
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


class ContactTable(tables.Table):
    class Meta:
        model = Contact
        fields = (
            "first_name",
            "company",
            "main_address__address",
            "main_address__mobile_phone",
            "main_address__email",
            "mail_consent",
            "notes",
        )
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}

    def render_mail_consent(self, value):
        return "Yes" if value else ""

    def render_notes(self, value):
        return "Yes" if value else ""


class ContactTableTwo(tables.Table):
    class Meta:
        model = Contact
        fields = ("first_name", "company", "address__address")
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}


class BuyersTable(tables.Table):
    class Meta:
        model = Contact
        fields = ("first_name", "company", "address__address")
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}

    invoices = tables.Column(linkify=("buyer_invoices", A("pk")))


class InvoiceTable(ColumnShiftTable):
    class Meta:
        model = Invoice
        fields = ("date", "buyer", "number", "total", "paid")
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}

    total = CurrencyColumn()
    paid = CenteredTrueFalseColumn()

    def render_number(self, value, record):
        if record.proforma:
            return "Proforma"
        return value


class PurchaseTable(ColumnShiftTable):
    class Meta:
        model = Purchase
        fields = (
            "date",
            "vendor",
            "invoice_number",
            "invoice_total",
            "buyers_premium",
            "vat",
            "lots",
        )
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}

    invoice_number = RightAlignedColumn()
    lots = RightAlignedColumn(accessor="lot_set")
    invoice_total = CurrencyColumn()
    buyers_premium = CurrencyColumn()
    vat = RightAlignedColumn()
    # items = RightAlignedColumn(accessor="item_set")

    def render_lots(self, value):
        return len(value.all())

    # def render_items(self, value, record):
    #     l = len(value.all())
    #     if l == 1:
    #         return value.all()[0].ref
    #     return f"{l} items"

    def render_vendor(self, value):
        if value.first_name:
            return f"{value.first_name} {value.company}"
        return value.company

    def render_vat(self, value, record):
        if record.margin_scheme:
            return "Margin scheme"
        else:
            return "£" + str(intcomma(value))

    def value_date(self, value):
        return value

    def value_invoice_number(self, value):
        if value == "0":
            return "-"
        else:
            return value

    def value_items(self, value):
        result = ""
        for i in value.all():
            result += i.ref + " "
        return result[:-1]

    def value_invoice_total(self, value):
        return value

    def value_buyers_premium(self, value):
        return value


class EnquiryTable(tables.Table):
    class Meta:
        model = Enquiry
        fields = ("date", "subject", "message")
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}

    first_name = tables.Column(accessor="contact.first_name")
    last_name = tables.Column(accessor="contact.company", verbose_name="Last name")
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
