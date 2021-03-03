# Complete migration of coderedcms to use customimage everywhere

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("website", "0006_carousel_slide_image"),
    ]

    operations = [
        # cover image
        migrations.RunSQL(
            [
                "DROP INDEX coderedcms_coderedpage_cover_image_id_07449f7d;",
                "ALTER TABLE coderedcms_coderedpage DROP CONSTRAINT coderedcms_coderedpa_cover_image_id_07449f7d_fk_wagtailim;",
                "ALTER TABLE coderedcms_coderedpage ADD CONSTRAINT coderedcms_coderedpa_cover_image_id_fk_image \
             FOREIGN KEY (cover_image_id) REFERENCES shop_customimage(id) DEFERRABLE INITIALLY DEFERRED;",
                "CREATE UNIQUE INDEX coderedcms_coderedpage_cover_image_id_07449f7d on coderedcms_coderedpage (cover_image_id);",
            ]
        ),
        # og_image
        migrations.RunSQL(
            [
                "DROP INDEX coderedcms_coderedpage_og_image_id_ded00310;",
                "ALTER TABLE coderedcms_coderedpage DROP CONSTRAINT coderedcms_coderedpa_og_image_id_ded00310_fk_wagtailim;",
                "ALTER TABLE coderedcms_coderedpage ADD CONSTRAINT coderedcms_coderedpa_og_image_id_fk_image \
             FOREIGN KEY (og_image_id) REFERENCES shop_customimage(id) DEFERRABLE INITIALLY DEFERRED;",
                "CREATE UNIQUE INDEX coderedcms_coderedpage_og_image_id_ded00310 on coderedcms_coderedpage (og_image_id);",
            ]
        ),
        # struct_org_logo
        migrations.RunSQL(
            [
                "DROP INDEX coderedcms_coderedpage_struct_org_logo_id_98229fdd;",
                "ALTER TABLE coderedcms_coderedpage DROP CONSTRAINT coderedcms_coderedpa_struct_org_logo_id_98229fdd_fk_wagtailim;",
                "ALTER TABLE coderedcms_coderedpage ADD CONSTRAINT coderedcms_coderedpa_struct_org_logo_id_fk_image \
             FOREIGN KEY (struct_org_logo_id) REFERENCES shop_customimage(id) DEFERRABLE INITIALLY DEFERRED;",
                "CREATE UNIQUE INDEX coderedcms_coderedpage_struct_org_logo_id_98229fdd on coderedcms_coderedpage (struct_org_logo_id);",
            ]
        ),
        # struct_org_image
        migrations.RunSQL(
            [
                "DROP INDEX coderedcms_coderedpage_struct_org_image_id_567d6591;",
                "ALTER TABLE coderedcms_coderedpage DROP CONSTRAINT coderedcms_coderedpa_struct_org_image_id_567d6591_fk_wagtailim;",
                "ALTER TABLE coderedcms_coderedpage ADD CONSTRAINT coderedcms_coderedpa_struct_org_image_id_fk_image \
             FOREIGN KEY (struct_org_image_id) REFERENCES shop_customimage(id) DEFERRABLE INITIALLY DEFERRED;",
                "CREATE UNIQUE INDEX coderedcms_coderedpage_struct_org_image_id_567d6591 on coderedcms_coderedpage (struct_org_image_id);",
            ]
        ),
        # layoutsettings logo
        migrations.RunSQL(
            [
                "DROP INDEX coderedcms_layoutsettings_logo_id_ef53b3c9;",
                "ALTER TABLE coderedcms_layoutsettings DROP CONSTRAINT coderedcms_layoutset_logo_id_ef53b3c9_fk_wagtailim;",
                "ALTER TABLE coderedcms_layoutsettings ADD CONSTRAINT coderedcms_layoutset_logo_id_fk_image \
             FOREIGN KEY (logo_id) REFERENCES shop_customimage(id) DEFERRABLE INITIALLY DEFERRED;",
                "CREATE UNIQUE INDEX coderedcms_layoutsettings_logo_id_ef53b3c9 on coderedcms_layoutsettings (logo_id);",
            ]
        ),
        # layoutsettings favicon
        migrations.RunSQL(
            [
                "DROP INDEX coderedcms_layoutsettings_favicon_id_bdb026a2;",
                "ALTER TABLE coderedcms_layoutsettings DROP CONSTRAINT coderedcms_layoutset_favicon_id_bdb026a2_fk_wagtailim;",
                "ALTER TABLE coderedcms_layoutsettings ADD CONSTRAINT coderedcms_layoutset_favicon_id_fk_image \
             FOREIGN KEY (favicon_id) REFERENCES shop_customimage(id) DEFERRABLE INITIALLY DEFERRED;",
                "CREATE UNIQUE INDEX coderedcms_layoutsettings_favicon_id_bdb026a2 on coderedcms_layoutsettings (favicon_id);",
            ]
        ),
    ]
