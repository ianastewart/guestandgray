# Generated by Django 2.2.4 on 2019-08-19 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='object',
            name='has_image',
            field=models.NullBooleanField(),
        ),
    ]
