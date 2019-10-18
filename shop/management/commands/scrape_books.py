from requests_html import HTMLSession
from django.core.management.base import BaseCommand
from shop.models import Book


class Command(BaseCommand):
    help = "Scrapes site to populate archive"

    def add_arguments(selfself, parser):
        parser.add_argument("--create", action="store_true", help="Create objects")

    def handle(self, *args, **options):
        self.create = options["create"]
        if self.create:
            print("Deleting all books")
            Book.objects.all().delete()
        else:
            print("Testing book scraping")

        self.session = HTMLSession()
        count = 0
        url = "https://chinese-porcelain-art.com/annotated-bibliographies/compiled-by-margaret-medley/"
        count += self.scrape_url(url, "Margaret Medley")
        url = "https://chinese-porcelain-art.com/annotated-bibliographies/cyril-beecher-update-on-margaret-medleys-bibliography/"
        count += self.scrape_url(url, "Cyril Beecher")
        url = "https://chinese-porcelain-art.com/annotated-bibliographies/hanshan-tang-books-ltd/"
        count += self.scrape_url(url, "Hanshan Tang")
        books = len(Book.objects.all())
        print(f"Processed {count} rows. There are {books} books in the database.")

    def scrape_url(self, url, compiler):
        page = self.session.get(url)
        tables = page.html.find("table")
        rows = tables[0].find("tr")
        for row in rows:
            subtitle = ""
            detail_1 = ""
            detail_2 = ""
            detail_3 = ""
            entries = row.text.split("\n")
            author = entries[0]
            title = entries[1]
            l = len(entries)
            description = entries[l - 1]
            if l == 4:
                detail_1 = entries[2]
            if l > 4:
                subtitle = entries[2]
            if l >= 5:
                detail_1 = entries[3]
            if l >= 6:
                detail_2 = entries[4]
            if l >= 7:
                detail_3 = entries[5]
            # special cases
            if "(Trans." in subtitle:
                detail_1 = subtitle
                subtitle = ""
            if l == 12:
                description = ""
                for n in range(6, 12):
                    description += entries[n] + "\n"
            if self.create:
                try:
                    Book.objects.create(
                        author=author,
                        title=title,
                        subtitle=subtitle,
                        detail_1=detail_1,
                        detail_2=detail_2,
                        detail_3=detail_3,
                        description=description,
                        compiler=compiler,
                    )
                except Exception as e:
                    pass
            else:
                print(author, title, description)
        return len(rows)
