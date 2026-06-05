from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0050_customimage_description"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="item",
            name="archive",
        ),
    ]
