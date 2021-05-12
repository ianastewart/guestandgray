from django.core.management.base import BaseCommand
from wagtail.core.models import Site


class Command(BaseCommand):
    help = "Set wagtail site to localhost:8000"

    def add_arguments(self, parser):
        parser.add_argument("host")
        parser.add_argument("port", type=int)

    def handle(self, *args, **kwargs):
        host = kwargs["host"]
        port = kwargs["port"]
        site = Site.objects.all().first()
        site.hostname = host
        site.port = port
        site.save()
        self.stdout.write(f"Wagtail site updated to {host} {port}")
