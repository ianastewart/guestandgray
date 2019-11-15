# Generated by Django 2.2.6 on 2019-11-04 08:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("shop", "0017_auto_20191026_1519")]

    operations = [
        migrations.RemoveField(model_name="purchase", name="vat_rate"),
        migrations.AddField(
            model_name="purchase",
            name="cost_lot",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AlterField(
            model_name="purchase",
            name="vat",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name="VAT",
            ),
        ),
    ]