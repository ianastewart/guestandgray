# Generated by Django 2.2.4 on 2019-09-14 17:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import taggit.managers
import wagtail.core.models
import wagtail.images.models
import wagtail.search.index


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("wagtailcore", "0041_group_collection_permissions_verbose_name_plural"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("taggit", "0002_auto_20150616_2121"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("path", models.CharField(max_length=255, unique=True)),
                ("depth", models.PositiveIntegerField()),
                ("numchild", models.PositiveIntegerField(default=0)),
                ("name", models.CharField(max_length=100)),
                ("slug", models.CharField(max_length=400)),
                ("short_name", models.CharField(blank=True, max_length=50, null=True)),
                ("description", models.TextField(blank=True, null=True)),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="CustomImage",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255, verbose_name="title")),
                (
                    "file",
                    models.ImageField(
                        height_field="height",
                        upload_to=wagtail.images.models.get_upload_to,
                        verbose_name="file",
                        width_field="width",
                    ),
                ),
                ("width", models.IntegerField(editable=False, verbose_name="width")),
                ("height", models.IntegerField(editable=False, verbose_name="height")),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="created at"
                    ),
                ),
                ("focal_point_x", models.PositiveIntegerField(blank=True, null=True)),
                ("focal_point_y", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "focal_point_width",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                (
                    "focal_point_height",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                ("file_size", models.PositiveIntegerField(editable=False, null=True)),
                (
                    "file_hash",
                    models.CharField(blank=True, editable=False, max_length=40),
                ),
                ("primary_image", models.BooleanField(default=False)),
                ("ref", models.CharField(blank=True, max_length=10, null=True)),
                (
                    "collection",
                    models.ForeignKey(
                        default=wagtail.core.models.get_root_collection_id,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="wagtailcore.Collection",
                        verbose_name="collection",
                    ),
                ),
            ],
            options={"abstract": False},
            bases=(wagtail.search.index.Indexed, models.Model),
        ),
        migrations.CreateModel(
            name="Item",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(blank=True, max_length=200, null=True)),
                ("ref", models.CharField(blank=True, default="", max_length=10)),
                ("description", models.TextField(blank=True, null=True)),
                ("price", models.IntegerField(blank=True, null=True)),
                ("image_file", models.CharField(blank=True, max_length=50, null=True)),
                (
                    "category_text",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="shop.Category",
                    ),
                ),
                (
                    "image",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="parent_object",
                        to="shop.CustomImage",
                    ),
                ),
            ],
            bases=(wagtail.search.index.Indexed, models.Model),
        ),
        migrations.AddField(
            model_name="customimage",
            name="item",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="images",
                to="shop.Item",
            ),
        ),
        migrations.AddField(
            model_name="customimage",
            name="tags",
            field=taggit.managers.TaggableManager(
                blank=True,
                help_text=None,
                through="taggit.TaggedItem",
                to="taggit.Tag",
                verbose_name="tags",
            ),
        ),
        migrations.AddField(
            model_name="customimage",
            name="uploaded_by_user",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
                verbose_name="uploaded by user",
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="image",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="linked_category",
                to="shop.CustomImage",
            ),
        ),
        migrations.CreateModel(
            name="CustomRendition",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("filter_spec", models.CharField(db_index=True, max_length=255)),
                (
                    "file",
                    models.ImageField(
                        height_field="height",
                        upload_to=wagtail.images.models.get_rendition_upload_to,
                        width_field="width",
                    ),
                ),
                ("width", models.IntegerField(editable=False)),
                ("height", models.IntegerField(editable=False)),
                (
                    "focal_point_key",
                    models.CharField(
                        blank=True, default="", editable=False, max_length=16
                    ),
                ),
                (
                    "image",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="renditions",
                        to="shop.CustomImage",
                    ),
                ),
            ],
            options={"unique_together": {("image", "filter_spec", "focal_point_key")}},
        ),
    ]
