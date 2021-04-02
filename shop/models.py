from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from enum import IntEnum
from treebeard.mp_tree import MP_Node, MP_NodeManager
from wagtail.images.models import Image, AbstractImage, AbstractRendition
from wagtail.search import index


class ModelEnum(IntEnum):
    @classmethod
    def choices(cls):
        return list(
            (x.value, x.name.lower().capitalize().replace("_", " ")) for x in cls
        )


class CategoryManager(MP_NodeManager):
    def empty_nodes(self, instance=None):
        """ returns node above current node that have no item """
        cats = Category.objects.all().exclude(name="Catalogue").order_by("name")
        if instance:
            cats.exclude(pk=instance.pk)
        choices = [(cat.id, cat.name) for cat in cats if cat.item_set.count() == 0]
        root = Category.objects.get(name="Catalogue")
        choices.insert(0, (root.id, "Catalogue (root)"))
        return choices

    def leafs(self):
        return [cat for cat in self.all().order_by("name") if cat.is_leaf()]

    def leaf_choices(self):
        return [
            (cat.id, cat.name) for cat in self.all().order_by("name") if cat.is_leaf()
        ]


class Category(MP_Node):
    """
    Categories are organised in a tree using Django Treebeard
    See also cat_tree.py
    """

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
    sequence = models.PositiveIntegerField(default=0)
    count = models.IntegerField(default=0)
    hidden = models.BooleanField(default=False)
    node_order_by = ["sequence"]
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def post_save(self):
        """ Called after create or update to ensure tree slugs are updated is correct """
        self = Category.objects.get(id=self.id)
        if not self.short_name:
            self.short_name = self.name[:50]
        if self.is_root():
            self.slug = slugify(self.short_name)
        else:
            self.slug = self.get_parent().slug + "/" + slugify(self.short_name)
        self.save()
        for child in self.get_children():
            child.post_save()

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

    def archive_slug(self):
        return self.slug.replace("catalogue/", "archive/")

    def shop_items(self):
        return self.item_set.filter(
            archive=False, visible=True, image__isnull=False
        ).order_by("-featured", "rank", "-sale_price", "name")

    def shop_count(self):
        return self.shop_items().count()

    def archive_items(self):
        return self.item_set.filter(
            archive=True, visible=True, image__isnull=False
        ).order_by("-featured", "rank", "-sale_price", "name")

    def archive_count(self):
        return self.archive_items().count()


class Item(index.Indexed, models.Model):
    class State(ModelEnum):
        NOT_FOR_SALE = 0
        ON_SALE = 1
        RESERVED = 2
        SOLD = 3

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
    notes = models.TextField(null=True, blank=True)
    provenance = models.TextField(null=True, blank=True)
    state = models.SmallIntegerField(choices=State.choices(), default=0)
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
    location = models.SmallIntegerField(
        choices=Location.choices(), default=0, null=True, blank=True
    )
    show_price = models.BooleanField(default=True)
    visible = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    done = models.BooleanField(default=False)
    rank = models.SmallIntegerField(default=10)
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
    book = models.ForeignKey("Book", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.ref} {self.name}"

    def get_absolute_url(self):
        return reverse("public_item_ref", kwargs={"ref": self.ref})

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
    address = models.ForeignKey(
        "Address", null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        vendor = "Unknown vendor"
        if self.vendor:
            vendor = self.vendor.company
        return f"Invoice: {self.invoice_number} Vendor: {vendor}"


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

    def __str__(self):
        return f"Lot: {self.number} Purchase id: {self.purchase.id}"


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
    """ Generates unique alphanumeric reference numbers for items """

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


# class InvoiceNumber(models.Model):
#     """ Generate sequential numbers for invoices """
#
#     invoice_number = models.IntegerField(null=False, blank=False)
#
#     @classmethod
#     def get_next(cls, increment=True):
#         records = InvoiceNumber.objects.all()
#         if len(records) == 0:
#             record = InvoiceNumber.reset()
#         else:
#             record = records[0]
#         result = record.invoice_number
#         if increment:
#             record.invoice_number = result + 1
#             record.save()
#         return result
#
#     @classmethod
#     def reset(cls, number=1):
#         InvoiceNumber.objects.all().delete()
#         return InvoiceNumber.objects.create(invoice_number=number)


class Invoice(models.Model):
    date = models.DateField(null=True, blank=True)
    number = models.CharField(max_length=10, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    proforma = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    buyer = models.ForeignKey(
        "Contact", null=True, blank=True, on_delete=models.SET_NULL
    )
    address = models.ForeignKey(
        "Address", null=True, blank=True, on_delete=models.SET_NULL
    )

    @classmethod
    def next_number(cls):
        invs = cls.objects.all().order_by("-number")
        if invs:
            return int(invs.first().number) + 1
        return 1


class InvoiceCharge(models.Model):
    class ChargeType(ModelEnum):
        SHIPPING = 0
        INSURANCE = 1
        OTHER = 2

    charge_type = models.SmallIntegerField(
        choices=ChargeType.choices(), default=0, null=False, blank=False
    )
    description = models.CharField(max_length=50, null=False, blank=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    invoice = models.ForeignKey(
        "Invoice", null=True, blank=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.description} £{self.amount}"


class Contact(models.Model):
    """ Covers all business contacts  - buyers, vendors etc """

    title = models.CharField(max_length=20, blank=True, null=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)

    company = models.CharField(max_length=100, blank=True, null=True)

    notes = models.CharField(max_length=500, blank=True, null=True)
    mail_consent = models.BooleanField(default=False)
    consent_date = models.DateField(null=True)
    vendor = models.BooleanField(default=False)
    restorer = models.BooleanField(default=False)
    buyer = models.BooleanField(default=False)
    main_address = models.OneToOneField(
        "address",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="main_contact",
    )

    def __str__(self):
        return self.name

    @property
    def name(self):
        if self.first_name:
            return f"{self.first_name} {self.company}"
        return self.company

    @property
    def details(self):
        if self.main_address:
            return f"{self.name}\n{self.main_address.address}"
        return self.name

    def addresses(self):
        return self.address_set.all().order_by("-date")


class Address(models.Model):
    """ A Contact can have multiple addresses stored in address history"""

    shipping = models.BooleanField(default=True)
    billing = models.BooleanField(default=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    work_phone = models.CharField(max_length=20, blank=True, null=True)
    mobile_phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=80, blank=True, null=True)
    contact = models.ForeignKey(
        Contact, null=False, blank=False, on_delete=models.CASCADE
    )
    date = models.DateTimeField(auto_now_add=True)


class Enquiry(models.Model):
    date = models.DateField(auto_now_add=True)
    subject = models.CharField(max_length=80, blank=False, null=True)
    message = models.TextField(max_length=1000, blank=False, null=True)
    items = models.ManyToManyField(Item)
    closed = models.BooleanField(default=False)
    notes = models.CharField(max_length=2000, blank=True, null=True)

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
    item = models.ForeignKey(
        Item, null=True, blank=True, on_delete=models.CASCADE, related_name="images"
    )
    show = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField(default=0)
    admin_form_fields = Image.admin_form_fields + ("item",)


class CustomRendition(AbstractRendition):
    image = models.ForeignKey(
        CustomImage, on_delete=models.CASCADE, related_name="renditions"
    )

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)


class Photo(models.Model):
    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to="photos/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
