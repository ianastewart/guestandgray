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


class CustomImage(AbstractImage):
    primary_image = models.BooleanField(default=False)
    ref = models.CharField(max_length=10, null=True, blank=True)
    item = models.ForeignKey(
        Item, null=True, blank=True, on_delete=models.CASCADE, related_name="images"
    )

    admin_form_fields = Image.admin_form_fields + ("ref", "primary_image", "item")


class CustomRendition(AbstractRendition):
    image = models.ForeignKey(
        CustomImage, on_delete=models.CASCADE, related_name="renditions"
    )

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)
