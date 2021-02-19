

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('website', '0005_auto_20210203_1153'),
    ]

    operations = [
        migrations.RunSQL([
            "DROP INDEX coderedcms_carouselslide_image_id_47e5d4bd;",
            "ALTER TABLE coderedcms_carouselslide DROP CONSTRAINT coderedcms_carousels_image_id_47e5d4bd_fk_wagtailim;",
            "ALTER TABLE coderedcms_carouselslide ADD CONSTRAINT coderedcms_carousels_image_id_fk_image \
             FOREIGN KEY (image_id) REFERENCES shop_customimage(id) DEFERRABLE INITIALLY DEFERRED;",
            "CREATE UNIQUE INDEX coderedcms_carouselslide_image_id_47e5d4bd on coderedcms_carouselslide (image_id);"
        ])
    ]
