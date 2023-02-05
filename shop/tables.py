from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django_tables2.utils import A
from shop.models import (
    Book,
    Category,
    Compiler,
    Contact,
    CustomImage,
    Enquiry,
    Invoice,
    Item,
    Purchase,
)
from tables_plus.tables import *


class CategoryTable(tables.Table):
    class Meta:
        model = Category
        fields = ("name", "parent", "description", "image", "count")
        attrs = {"class": "table table-sm table-responsive table-hover hover-link"}
        row_attrs = {
            "data-url": lambda record: reverse("category_detail", kwargs={"pk": record.pk}),
            "class": "table-row pl-4",
        }

    parent = tables.Column(empty_values=())

    @staticmethod
    def render_description(value):
        if len(value) > 80:
            return value[:80] + "..."

    @staticmethod
    def render_parent(record):
        return record.get_parent().name


class ImageColumn(tables.Column):
    @staticmethod
    def render(value):
        image = value.get_rendition("max-100x100")
        return mark_safe(f'<img src="{image.file.url}">')


class ItemTable(Table):
    class Meta:
        model = Item
        fields = (
            "selection",
            "name",
            "ref",
            "category",
            "purchased",
            "cost_price",
            "sale_price",
            "state",
            "archive",
            "featured",
            "rank",
            "visible",
            "done",
            "selection",
        )
        sequence = ("selection", "ref", "name")
        default_columns = ("selection", "name", "ref", "category", "state")
        editable_columns = ("state", "name")
        attrs = {"class": "table table-sm table-hover", "thead": {"class": "bg-light"}}

    category = tables.Column(accessor="category__name", verbose_name="Category")
    purchased = tables.Column(accessor="lot__purchase__date", verbose_name="Purchased")
    cost_price = CurrencyColumn(integer=False, verbose_name="Cost")
    sale_price = CurrencyColumn(integer=False, verbose_name="Sale price")
    image = ImageColumn(accessor="image", verbose_name="Image")
    images = tables.Column(accessor="id", verbose_name="Photos")
    selection = SelectionColumn()

    @staticmethod
    def render_images(record):
        return CustomImage.objects.filter(item=record).count()


class ContactTable(Table):
    class Meta:
        model = Contact
        fields = (
            "selection",
            "first_name",
            "company",
            "main_address__address",
            "main_address__mobile_phone",
            "main_address__email",
            "mail_consent",
            "notes",
        )
        click = reverse_lazy("contact_update", kwargs={"pk": 0})
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {
            "data-pk": lambda record: record.pk,
            "class": "table-row pl-4",
        }

    selection = SelectionColumn()

    @staticmethod
    def render_mail_consent(value):
        return "Yes" if value else ""

    @staticmethod
    def render_notes(value):
        return "Yes" if value else ""


class ContactTableTwo(Table):
    class Meta:
        model = Contact
        fields = ("first_name", "company", "address__address")
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}


class BuyersTable(Table):
    class Meta:
        model = Contact
        fields = ("first_name", "company", "address__address")
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}

    invoices = tables.Column(linkify=("buyer_invoices", A("pk")))


class MailListTable(Table):
    class Meta:
        model = Contact
        fields = ("selection", "first_name", "last_name", "main_address__email", "mail_consent", "consent_date")
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}

    selection = SelectionColumn()


class InvoiceTable(Table):
    class Meta:
        model = Invoice
        fields = ("date", "buyer", "number", "total", "paid")
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}

    total = CurrencyColumn()
    paid = CenteredTrueFalseColumn()

    @staticmethod
    def render_number(value, record):
        if record.proforma:
            return "Proforma"
        return value


class PurchaseTable(Table):
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

    @staticmethod
    def render_lots(value):
        return len(value.all())

    # def render_items(self, value, record):
    #     l = len(value.all())
    #     if l == 1:
    #         return value.all()[0].ref
    #     return f"{l} items"
    @staticmethod
    def render_vendor(value):
        if value.first_name:
            return f"{value.first_name} {value.company}"
        return value.company

    @staticmethod
    def render_vat(value, record):
        if record.margin_scheme:
            return "Margin scheme"
        else:
            return "£" + str(intcomma(value))

    @staticmethod
    def value_date(value):
        return value

    @staticmethod
    def value_invoice_number(value):
        if value == "0":
            return "-"
        else:
            return value

    @staticmethod
    def value_items(value):
        result = ""
        for i in value.all():
            result += i.ref + " "
        return result[:-1]

    @staticmethod
    def value_invoice_total(value):
        return value

    @staticmethod
    def value_buyers_premium(value):
        return value


class EnquiryTable(Table):
    class Meta:
        model = Enquiry
        fields = ("selection", "date", "subject", "message")
        attrs = {"class": "table table-sm table-hover hover-link table-responsive"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}

    subject = tables.Column(
        attrs={
            "th": {"class": "subject"},
            "td": {"class": "subject"},
        }
    )
    message = tables.Column(
        attrs={
            "th": {"class": "message"},
            "td": {"class": "message"},
        }
    )
    first_name = tables.Column(accessor="contact__first_name")
    last_name = tables.Column(accessor="contact__last_name", verbose_name="Last name")
    # email = tables.Column(accessor="contact__main_address__email")
    mail_consent = tables.Column(accessor="contact.mail_consent")
    state = tables.Column(accessor="closed")
    selection = SelectionColumn()

    @staticmethod
    def render_mail_consent(value):
        return "Yes" if value else ""

    @staticmethod
    def render_state(value):
        return "Closed" if value else "Open"

    @staticmethod
    def render_message(value):
        if len(value) > 200:
            return f"{value[:200]} ..."
        return value


class BookTable(Table):
    class Meta:
        model = Book
        fields = ("title", "author", "description", "compiler.name")
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}

    title = tables.Column(attrs={"td": {"width": "20%"}})
    author = tables.Column(attrs={"td": {"width": "20%"}})
    description = tables.Column(orderable=False)


class CompilerTable(Table):
    class Meta:
        model = Compiler
        fields = ("name", "description")
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}
