# Generated by Django 2.2.8 on 2019-12-18 20:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("shop", "0026_contact_main_address")]

    operations = [
        migrations.DeleteModel(name="InvoiceNumber"),
        migrations.AlterField(
            model_name="invoice",
            name="number",
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]