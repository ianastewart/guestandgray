# Generated by Django 2.2.4 on 2019-09-10 16:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("shop", "0011_auto_20190910_1726")]

    operations = [
        migrations.RenameField(
            model_name="object", old_name="new_category", new_name="category"
        )
    ]