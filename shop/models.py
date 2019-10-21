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

    name = models.CharField(max_length=200)
    slug = models.SlugField(null=True, blank=True, max_length=200)
    ref = models.CharField(
        null=False, blank=True, max_length=10, default="", db_index=True
    )
    description = models.TextField(null=True, blank=True)
    dimensions = models.CharField(max_length=200, null=True, blank=True)
    condition = models.CharField(max_length=200, null=True, blank=True)
    provenance = models.CharField(max_length=500, null=True, blank=True)
    # notes = models.TextField(null=True, blank=True)
    price = models.IntegerField(null=True, blank=True)
    image_file = models.CharField(max_length=100, null=True, blank=True)
    image = models.ForeignKey(
        "CustomImage",
        null=True,
        on_delete=models.SET_NULL,
        related_name="parent_object",
    )
    category_text = models.CharField(max_length=100, null=True, blank=True)
    # creation_date = models.DateTimeField(auto_now_add=True)
    # sold_date = models.DateTimeField(null=True, blank=True)
    # state = models.SmallIntegerField(choices=State.choices(), default=0)

    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL
    )
    visible = models.BooleanField(default=True)
    archive = models.BooleanField(default=False)

    search_fields = [index.SearchField("name", boost=3), index.SearchField("ref")]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("public_item", kwargs={"slug": self.slug, "pk": self.id})

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Address(models.Model):
    address1 = models.CharField(max_length=50)
    address2 = models.CharField(max_length=50, blank=True, null=True)
    address3 = models.CharField(max_length=50, blank=True, null=True)
    town = models.CharField(max_length=50)
    post_code = models.CharField(max_length=15, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.address1}, {self.address2}, {self.town}"


class Contact(models.Model):
    title = models.CharField(max_length=20, blank=True, null=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30)
    company = models.CharField(max_length=50, blank=True, null=True)
    work_phone = models.CharField(max_length=20, blank=True, null=True)
    mobile_phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=80, blank=True, null=True)
    notes = models.CharField(max_length=1000, blank=True, null=True)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    mail_consent = models.BooleanField(default=False)
    consent_date = models.DateField(null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Enquiry(models.Model):
    date = models.DateField(auto_now_add=True)
    subject = models.CharField(max_length=80, blank=False, null=True)
    message = models.TextField(blank=False, null=True)
    items = models.ManyToManyField(Item)
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True)
    closed = models.BooleanField(default=False)


class Compiler(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField(blank=True, null=True)


class Book(models.Model):
    title = models.CharField(max_length=200, blank=False, null=False)
    subtitle = models.CharField(max_length=100, blank=True, null=True)
    detail_1 = models.CharField(max_length=100, blank=True, null=True)
    detail_2 = models.CharField(max_length=100, blank=True, null=True)
    detail_3 = models.CharField(max_length=100, blank=True, null=True)
    author = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    compiler = models.ForeignKey(Compiler, on_delete=models.SET_NULL, null=True)


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
