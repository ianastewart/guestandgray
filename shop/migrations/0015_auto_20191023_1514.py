# Generated by Django 2.2.6 on 2019-10-23 14:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("shop", "0014_auto_20191021_1103")]

    operations = [
        migrations.CreateModel(
            name="Purchase",
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
                ("purchase_date", models.DateField(blank=True, null=True)),
                (
                    "invoice_number",
                    models.CharField(blank=True, max_length=10, null=True),
                ),
                (
                    "invoice_total",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                (
                    "buyers_premium",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("lot_number", models.CharField(blank=True, max_length=10, null=True)),
                ("paid_date", models.DateField(blank=True, null=True)),
                ("margin_scheme", models.BooleanField(default=True)),
                (
                    "vat_rate",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=4, null=True
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PurchaseExpense",
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
                ("expense_type", models.CharField(max_length=50)),
                (
                    "amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("eligible", models.BooleanField(default=False)),
                (
                    "purchase",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="shop.Purchase",
                    ),
                ),
            ],
        ),
        migrations.RemoveField(model_name="item", name="category_text"),
        migrations.RemoveField(model_name="item", name="image_file"),
        migrations.AddField(
            model_name="contact", name="buyer", field=models.BooleanField(default=False)
        ),
        migrations.AddField(
            model_name="contact", name="other", field=models.BooleanField(default=False)
        ),
        migrations.AddField(
            model_name="contact",
            name="restorer",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="contact",
            name="vendor",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="item",
            name="cost_price",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="item", name="featured", field=models.BooleanField(default=True)
        ),
        migrations.AddField(
            model_name="item",
            name="location",
            field=models.SmallIntegerField(
                choices=[
                    (0, "Auction"),
                    (1, "Not collected"),
                    (2, "At restorer"),
                    (3, "In stock"),
                ],
                default=0,
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="minimum_price",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="purchase_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="item",
            name="restoration_cost",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="sale_price",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="show_price",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="contact",
            name="address",
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name="contact",
            name="notes",
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name="enquiry",
            name="contact",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="shop.Contact",
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="image",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="parent_object",
                to="shop.CustomImage",
            ),
        ),
        migrations.DeleteModel(name="Address"),
        migrations.AddField(
            model_name="purchase",
            name="vendor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="shop.Contact",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="purchase_data",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="shop.Purchase",
            ),
        ),
    ]