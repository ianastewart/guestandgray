# Generated by Django 3.1.6 on 2021-09-15 07:15
# Manually created to make og_image refer to custom image in coderedcms but with migration as part of shop
# https://stackoverflow.com/questions/29575802/django-migration-file-in-an-other-app

from django.db import migrations, models
import django.db.models.deletion

TARGET_APP = "coderedcms"


class Migration(migrations.Migration):
    def __init__(self, name, app_label):
        # overriding application operated upon
        super(Migration, self).__init__(name, TARGET_APP)

    # specify what original migration file it replaces
    # or leave migration loader confused about unapplied migration
    replaces = ((TARGET_APP, __module__.rsplit(".", 1)[-1]),)

    dependencies = [
        ("shop", "0041_seo_description"),
        ("coderedcms", "0022_auto_20210731_1853"),
    ]

    operations = [
        migrations.AlterField(
            model_name="coderedpage",
            name="og_image",
            field=models.ForeignKey(
                blank=True,
                help_text="Shown when linking to this page on social media.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="shop.customimage",
                verbose_name="Preview image",
            ),
        ),
    ]
