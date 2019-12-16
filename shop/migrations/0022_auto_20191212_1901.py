# Generated by Django 2.2.8 on 2019-12-12 19:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("shop", "0021_auto_20191210_1257")]

    operations = [
        migrations.CreateModel(
            name="InvoiceNumber",
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
                ("invoice_number", models.IntegerField()),
            ],
        ),
        migrations.AddField(
            model_name="invoice",
            name="proforma",
            field=models.BooleanField(default=False),
        ),
    ]
