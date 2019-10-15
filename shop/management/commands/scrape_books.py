from requests_html import HTMLSession
from django.core.management.base import BaseCommand
from shop.models import Book


class Command(BaseCommand):
    help = "Scrapes site to populate archive"

    def add_arguments(selfself, parser):
        parser.add_argument("--create", action="store_true", help="Create objects")

    def handle(self, *args, **options):

        if options["create"]:
            print("Deleting all books")
            Book.objects.all().delete()
        else:
            print("Testing book scraping")

        url = "https://chinese-porcelain-art.com/annotated-bibliographies/compiled-by-margaret-medley/"
        session = HTMLSession()
        page = session.get(url)
        tables = page.html.find("table")
        rows = tables[0].find("tr")
        for row in rows:
            entries = row.text.split("\n")
            author = entries[0]
            title = entries[1]
            if len(entries) == 5:
                author += "\n " + entries[2]
            description = entries[-1]
            if options["create"]:
                Book.objects.create(author=author, title=title, description=description)
            else:
                print(author, title, description)
        books = len(Book.objects.all())

        print(f"Processed {len(rows)} rows. There are {books} books in the database.")
