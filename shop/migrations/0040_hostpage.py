# Generated by Django 3.1.6 on 2021-08-19 18:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0039_item_updated"),
    ]

    operations = [
        migrations.CreateModel(
            name="HostPage",
            fields=[
                (
                    "coderedpage_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="coderedcms.coderedpage",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("coderedcms.coderedpage",),
        ),
    ]