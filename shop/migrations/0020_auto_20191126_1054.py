# Generated by Django 2.2.7 on 2019-11-26 10:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("shop", "0019_auto_20191115_1527")]

    operations = [
        migrations.RemoveField(model_name="item", name="purchase_data"),
        migrations.RemoveField(model_name="item", name="purchase_date"),
        migrations.RemoveField(model_name="purchase", name="cost_lot"),
        migrations.RemoveField(model_name="purchase", name="lot_number"),
        migrations.RemoveField(model_name="purchase", name="paid_date"),
        migrations.AlterField(
            model_name="purchase",
            name="invoice_number",
            field=models.CharField(
                blank=True,
                max_length=10,
                null=True,
                verbose_name="Vendor's invoice no.",
            ),
        ),
        migrations.CreateModel(
            name="Lot",
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
                ("number", models.CharField(blank=True, max_length=10, null=True)),
                (
                    "cost",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=10,
                        null=True,
                        verbose_name="VAT",
                    ),
                ),
                (
                    "purchase",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="shop.Purchase",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="item",
            name="lot",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="shop.Lot",
            ),
        ),
    ]
