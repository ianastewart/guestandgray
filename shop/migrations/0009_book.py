# Generated by Django 2.2.6 on 2019-10-12 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("shop", "0008_auto_20191012_0926")]

    operations = [
        migrations.CreateModel(
            name="Book",
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
                ("title", models.CharField(max_length=200)),
                ("author", models.CharField(max_length=100)),
                ("info", models.CharField(blank=True, max_length=100, null=True)),
                ("description", models.TextField(blank=True, null=True)),
            ],
        )
    ]
