from requests_html import HTMLSession
from django.core.management.base import BaseCommand
from shop.models import Item, CustomImage, Category
from shop.import_helper import load_image
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Scrapes site to populate archive"

    def add_arguments(selfself, parser):
        parser.add_argument("--create", action="store_true", help="Create sold objects")

    def handle(self, *args, **options):
        url = "https://www.chinese-porcelain-art.com/acatalog/"
        session = HTMLSession()
        r = session.get(url)
        links_set = r.html.absolute_links
        links = []
        for l in links_set:
            bits = l.split("?")
            if len(bits) == 2 and bits[1][:9] == "SECTIONID":
                page = bits[1][10:].split("&")[0]
                links.append(url + page)
        links.sort()
        # l = "https://www.chinese-porcelain-art.com/acatalog/Catalogue_Chinese_Snuff_Bottles_104.html"
        # page = session.get(l)
        # if page.status_code == 200:
        #     parse(page, self.stdout, options["create"])
        #
        for link in links:
            page = session.get(link)
            if page.status_code == 200:
                parse(page, self.stdout, options["create"])


def parse(page, stdout, create=False):
    try:
        user = User.objects.all().first()
        sold = False
        cat = ""
        number = 0
        content = page.html.find("#ContentPage")[0]
        cc = content.find(".boxheading")
        if cc:
            # Catalogue page
            for c in cc:
                cat = c.text
                cat = cat.replace("Stuff", "Snuff")
                if c.text[:4] == "Sold":
                    cat = c.text[5:]
                    sold = True
                p = cat.find(" Page")
                if p > 0:
                    number = int(cat[p + 5 :])
                    cat = cat[:p]
                stdout.write(f"Catalogue page, {cat}, {sold}, {number}")
                return
        # object grid page
        tables = content.find("table")
        spans = content.find(".actxsmall")
        found1 = False
        for span in spans:
            if found1:
                cat = span.text
                if span.text[:4] == "Sold":
                    s = content.text.find("Sold")
                    e = content.text.find("\n")
                    cat = content.text[s + 12 : e]
                    if "Chinese" in cat:
                        cat = cat[8:]
                        if "Armorial" in cat:
                            cat = "Porcelain with Armorials and European Designs"
                        cat = cat.replace("Ming-Earlier", "Ming & Earlier")
                        cat = cat.replace("Blanc", "Imperial, Blanc")
                    elif "Japanese" in cat:
                        cat = cat[9:]
                    elif "European" in cat:
                        cat = cat[9:]
                        if "Pottery" in cat:
                            cat = cat[15:]
                    z = cat.find(">")
                    if z > 0:
                        cat = cat[: z - 1]
                    sold = True
                break
            if span.text == "Catalogue":
                found1 = True
        if sold:
            cat_db = Category.objects.filter(name=cat)
            if len(cat_db) != 1:
                stdout.write(f"{cat} not found")
            cat_db = cat_db[0]
        # process a grid of objects
        # skip the enclosing table by starting at 1
        for i in range(1, len(tables)):
            tds = tables[i].find("td")
            if len(tds) > 1:
                images0 = tds[0].find("img")
                alist = tds[1].find("a")
                if images0 and alist:
                    # stdout.write(page.url, "grid page")
                    # product table
                    name = images0[0].attrs["title"]
                    ref = alist[0].attrs["name"][1:]
                    image_file = alist[1].attrs["href"]
                    text = tds[1].html
                    br = text.find("<br/>")
                    div = text.find("<div")
                    description = text[br + 6 : div]
                    prices = tds[1].find(".product-price")
                    price = 0
                    if prices:
                        price = prices[0].text.split("£")[1]
                        price = int(price.replace(",", "").replace(".", ""))
                    items = Item.objects.filter(ref=ref)
                    if not items:
                        if not sold:
                            stdout.write(f"{name} {ref} is not in the database")
                        else:
                            if create:
                                item = Item.objects.create(
                                    name=name,
                                    ref=ref,
                                    description=description,
                                    price=price,
                                    category=cat_db,
                                    image_file=image_file,
                                    archive=True,
                                )
                                item.save()
                                load_image(item, user)
                            # stdout.write(
                            #     f"{cat}, {sold}, {name}, {ref}, {description[:20]}, {price}"
                            # )
    except Exception as e:
        stdout.write(f"Exception {e} on {page.url}")
        pass
