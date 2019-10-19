# Generated by Django 2.2.6 on 2019-10-19 08:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("shop", "0011_category_archive_image")]

    operations = [
        migrations.RenameField(
            model_name="book", old_name="sub_title1", new_name="detail_1"
        ),
        migrations.RenameField(
            model_name="book", old_name="sub_title2", new_name="detail_2"
        ),
        migrations.RenameField(
            model_name="book", old_name="sub_title3", new_name="detail_3"
        ),
        migrations.AddField(
            model_name="book",
            name="subtitle",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]