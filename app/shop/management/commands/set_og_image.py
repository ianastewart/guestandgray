from django.db import transaction, connection
from django.core.management.base import BaseCommand, CommandError

# https://palewi.re/posts/2014/07/25/django-recipe-base-management-command-running-custom-sql/


class SimpleSQLCommand(BaseCommand):
    help = "A base class for packaging simple SQL operations as a command"
    # Overriding these attributes is what you will need to do when subclassing
    # this command for use.
    flush = None  # An optional Django database model to be flushed
    sql = ""  # The SQL command to be run

    def handle(self, *args, **options):
        # Validate
        if not self.sql:
            raise CommandError("'sql' attribute must be set")

        # Flush model if it is provided
        if self.flush:
            if options.get("verbosity") >= 1:
                self.stdout.write("- Flushing %s" % self.flush.__name__)
            self.flush_model(self.flush)

        # Run custom sql
        if options.get("verbosity") >= 1:
            self.stdout.write("- Running custom SQL")
        self.execute_sql(self.sql)

    @transaction.atomic
    def flush_model(self, model):
        """
        Flushes the provided model using the lower-level TRUNCATE SQL command.
        """
        cursor = connection.cursor()
        cursor.execute("TRUNCATE %s CASCADE;" % (model._meta.db_table))

    @transaction.atomic
    def execute_sql(self, sql):
        """
        Executes the provided SQL command.
        """
        cursor = connection.cursor()
        cursor.execute(sql)


class Command(SimpleSQLCommand):
    sql = """
DROP INDEX coderedcms_coderedpage_og_image_id_ded00310;
ALTER TABLE coderedcms_coderedpage DROP CONSTRAINT coderedcms_coderedpa_og_image_id_ded00310_fk_wagtailim;
ALTER TABLE coderedcms_coderedpage ADD CONSTRAINT coderedcms_coderedpa_og_image_id_fk_image \
    FOREIGN KEY (og_image_id) REFERENCES shop_customimage(id) DEFERRABLE INITIALLY DEFERRED;
CREATE UNIQUE INDEX coderedcms_coderedpage_og_image_id_ded00310 on coderedcms_coderedpage (og_image_id);
          """
