from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from enum import IntEnum
from wagtail.images.models import Image, AbstractImage, AbstractRendition


class CustomImage(AbstractImage):

    primary_image = models.BooleanField(default=False)
    ref = models.CharField(max_length=10, null=True, blank=True)
    object = models.ForeignKey(
        "Object", null=True, blank=True, on_delete=models.CASCADE, related_name="images"
    )

    admin_form_fields = Image.admin_form_fields + ("ref", "primary_image", "object")


class CustomRendition(AbstractRendition):
    image = models.ForeignKey(
        CustomImage, on_delete=models.CASCADE, related_name="renditions"
    )

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)


class ModelEnum(IntEnum):
    @classmethod
    def choices(cls):
        return list(
            (x.value, x.name.lower().capitalize().replace("_", " ")) for x in cls
        )


class Category(models.Model):
    name = models.CharField(max_length=200)
    image = models.ForeignKey(
        CustomImage,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sections",
    )

    def __str__(self):
        return self.name


class Object(models.Model):
    class State(ModelEnum):
        NOT_FOR_SALE = 0
        ON_SALE = 1
        SOLD = 2

    name = models.CharField(max_length=200)
    slug = models.SlugField(null=True, blank=True, max_length=200)
    ref = models.CharField(null=False, blank=True, max_length=10, default="")
    description = models.TextField(null=True, blank=True)
    # dimensions = models.CharField(max_length=200, null=True, blank=True)
    # condition = models.CharField(max_length=200, null=True, blank=True)
    # provenance = models.CharField(max_length=200, null=True, blank=True)
    # extra = models.TextField(null=True, blank=True)
    price = models.IntegerField(null=True, blank=True)
    image_file = models.CharField(max_length=50, null=True, blank=True)
    image = models.ForeignKey(
        CustomImage, null=True, on_delete=models.SET_NULL, related_name="parent_object"
    )
    category_text = models.CharField(max_length=100, null=True, blank=True)
    # creation_date = models.DateTimeField(auto_now_add=True)
    # sold_date = models.DateTimeField(null=True, blank=True)
    # state = models.SmallIntegerField(choices=State.choices(), default=0)
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("public_object", kwargs={"slug": self.slug, "pk": self.id})

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)
