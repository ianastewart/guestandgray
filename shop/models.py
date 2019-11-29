from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from enum import IntEnum
from treebeard.mp_tree import MP_Node
from wagtail.images.models import Image, AbstractImage, AbstractRendition
from wagtail.search import index


class ModelEnum(IntEnum):
    @classmethod
    def choices(cls):
        return list(
            (x.value, x.name.lower().capitalize().replace("_", " ")) for x in cls
        )


class Category(MP_Node):
    name = models.CharField(max_length=100)
    # Slug contains the full path slugified
    # We don't use a SlugField because the slug can contain / characters
    # and Django admin's validation would reject such entries
    slug = models.CharField(max_length=400)
    short_name = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image = models.ForeignKey(
        "CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="linked_category",
    )
    archive_image = models.ForeignKey(
        "CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="archive_category",
    )
    count = models.IntegerField(default=0)
    node_order_by = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.short_name:
            self.short_name = self.name[:50]
        if self.is_root():
            self.slug = slugify(self.short_name)
        else:
            self.slug = self.get_parent().slug + "/" + slugify(self.short_name)
        super().save(*args, **kwargs)
        for child in self.get_children():
            child.save()

    def breadcrumb_nodes(self, item_view=False):
        breadcrumb = []
        self.active = not item_view
        breadcrumb.append(self)
        parent = self.get_parent()
        while parent:
            parent.active = False
            breadcrumb.insert(0, parent)
            parent = parent.get_parent()
        return breadcrumb

    def get_absolute_url(self):
        return "/" + self.slug + "/"

    def get_archive_url(self):
        url = self.get_absolute_url()
        return url.replace("/catalogue/", "/archive/")


class Item(index.Indexed, models.Model):
    class State(ModelEnum):
        NOT_FOR_SALE = 0
        ON_SALE = 1
        SOLD = 2

    class Location(ModelEnum):
        IN_STOCK = 0
        AUCTION = 1
        NOT_COLLECTED = 2
        AT_RESTORER = 3

    name = models.CharField(max_length=200)
    slug = models.SlugField(null=True, blank=True, max_length=200)
    ref = models.CharField(
        null=False, blank=True, max_length=10, default="", db_index=True
    )
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL
    )
    condition = models.CharField(max_length=200, null=True, blank=True)
    dimensions = models.CharField(max_length=200, null=True, blank=True)
    provenance = models.CharField(max_length=500, null=True, blank=True)
    # notes = models.TextField(null=True, blank=True)
    archive = models.BooleanField(default=False)
    cost_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    restoration_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    price = models.IntegerField(null=True, blank=True)
    sale_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    minimum_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    # purchase_data = models.ForeignKey(
    #     "Purchase", null=True, blank=True, on_delete=models.SET_NULL
    # )
    # category_text = models.CharField(max_length=100, null=True, blank=True)
    # purchase_date = models.DateField(null=True, blank=True)
    location = models.SmallIntegerField(
        choices=Location.choices(), default=0, null=True, blank=True
    )
    show_price = models.BooleanField(default=True)
    visible = models.BooleanField(default=True)
    featured = models.BooleanField(default=True)
    # image_file = models.CharField(max_length=100, null=True, blank=True)
    image = models.ForeignKey(
        "CustomImage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="parent_object",
    )
    invoice = models.ForeignKey(
        "Invoice", null=True, blank=True, on_delete=models.SET_NULL
    )
    lot = models.ForeignKey("Lot", null=True, blank=True, on_delete=models.SET_NULL)
    search_fields = [index.SearchField("name", boost=3), index.SearchField("ref")]

    def __str__(self):
        return f"{self.ref} {self.name}"

    def get_absolute_url(self):
        return reverse("public_item", kwargs={"slug": self.slug, "pk": self.id})

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)

        super().save(*args, **kwargs)


class Purchase(models.Model):
    """ Purchase can be a lot with multiple items linked """

    date = models.DateField(null=True, blank=True, verbose_name="Purchase date")
    invoice_number = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="Vendor's invoice no."
    )
    invoice_total = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    buyers_premium = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Buyer's premium",
    )
    margin_scheme = models.BooleanField(default=True)
    vat = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="VAT"
    )
    vendor = models.ForeignKey(
        "Contact", null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        vendor = "Unknown vendor"
        if self.vendor:
            vendor = self.vendor.company
        return f"Lot: {self.lot_number} {vendor}"


class Lot(models.Model):
    number = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="Lot number"
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Cost of lot",
    )
    purchase = models.ForeignKey(
        Purchase, null=True, blank=False, on_delete=models.SET_NULL
    )


class PurchaseExpense(models.Model):
    description = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    eligible = models.BooleanField(default=False)
    purchase = models.ForeignKey(
        Purchase, null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"{self.id} {self.amount}"


class ItemRef(models.Model):
    number = models.IntegerField(null=False, blank=False)
    prefix = models.CharField(max_length=2, null=False, blank=False)

    def __str__(self):
        return f"{self.prefix}{self.number}"

    @classmethod
    def get_next(cls, increment=True):
        records = ItemRef.objects.all()
        if len(records) == 0:
            record = ItemRef.reset()
        else:
            record = records[0]
        result = record.__str__()
        if increment:
            record.number += 1
            record.save()
        return result

    @classmethod
    def reset(cls, prefix="Z", number=1):
        ItemRef.objects.all().delete()
        return ItemRef.objects.create(prefix=prefix, number=number)

    @classmethod
    def increment(cls, ref):
        number = int(ref[1:]) + 1
        return f"{ref[0]}{number}"


class Invoice(models.Model):
    date = models.DateField(null=True, blank=True)
    number = models.CharField(max_length=10, null=True, blank=True, unique=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    paid = models.BooleanField(default=False)
    buyer = models.ForeignKey(
        "Contact", null=True, blank=True, on_delete=models.SET_NULL
    )


class InvoiceExtra(models.Model):
    description = models.CharField(max_length=20, null=False, blank=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    invoice = models.ForeignKey(
        "Invoice", null=False, blank=False, on_delete=models.CASCADE
    )


class Contact(models.Model):
    """ Covers all business contacts  - buyers, vendors etc """

    title = models.CharField(max_length=20, blank=True, null=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    work_phone = models.CharField(max_length=20, blank=True, null=True)
    mobile_phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=80, blank=True, null=True)
    notes = models.CharField(max_length=500, blank=True, null=True)
    mail_consent = models.BooleanField(default=False)
    consent_date = models.DateField(null=True)
    vendor = models.BooleanField(default=False)
    restorer = models.BooleanField(default=False)
    buyer = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @property
    def name(self):
        if self.first_name:
            return f"{self.first_name} {self.company}"
        return self.company


class Enquiry(models.Model):
    date = models.DateField(auto_now_add=True)
    subject = models.CharField(max_length=80, blank=False, null=True)
    message = models.TextField(blank=False, null=True)
    items = models.ManyToManyField(Item)
    contact = models.ForeignKey(
        Contact, on_delete=models.SET_NULL, blank=True, null=True
    )
    closed = models.BooleanField(default=False)

    def __str__(self):
        return self.date


class Compiler(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200, blank=False, null=False)
    subtitle = models.CharField(max_length=100, blank=True, null=True)
    detail_1 = models.CharField(max_length=100, blank=True, null=True)
    detail_2 = models.CharField(max_length=100, blank=True, null=True)
    detail_3 = models.CharField(max_length=100, blank=True, null=True)
    author = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    compiler = models.ForeignKey(Compiler, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.title


class CustomImage(AbstractImage):
    # primary_image = models.BooleanField(default=False)
    # ref = models.CharField(max_length=10, null=True, blank=True)
    item = models.ForeignKey(
        Item, null=True, blank=True, on_delete=models.CASCADE, related_name="images"
    )

    admin_form_fields = Image.admin_form_fields + ("item",)


class CustomRendition(AbstractRendition):
    image = models.ForeignKey(
        CustomImage, on_delete=models.CASCADE, related_name="renditions"
    )

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)
