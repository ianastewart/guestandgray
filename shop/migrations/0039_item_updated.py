# Generated by Django 3.1.6 on 2021-04-07 10:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0038_auto_20210404_1012"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="updated",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
