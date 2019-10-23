from decimal import *
from requests_html import HTMLSession
from django.core.management.base import BaseCommand
from shop.models import Item, CustomImage, Category
from shop.truncater import truncate
from shop.import_helper import load_image
from django.contrib.auth.models import User
from collections import OrderedDict


class Command(BaseCommand):
    help = "Scrapes site to populate archive"

    def add_arguments(selfself, parser):
        parser.add_argument("--objects", action="store_true", help="Check object pages")
        parser.add_argument("--create", action="store_true", help="Create objects")
        parser.add_argument(
            "--categories", action="store_true", help="Recreate the category tree"
        )

    def handle(self, *args, **options):
        if options["categories"]:
            make_top_categories()
        if options["create"]:
            Item.objects.all().delete()

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
        for link in links:
            page = session.get(link)
            if page.status_code == 200:
                parse(page, options)


def parse(page, options):
    try:
        user = User.objects.all().first()
        sold = False
        cat = ""
        number = 0
        content = page.html.find("#ContentPage")[0]
        cc = content.find(".boxheading")
        notes = ""
        if cc:
            # this is a catalogue index page
            # extract the catalogue name from the top
            if options["categories"]:
                top_cat = ""

                gt = page.text.find("&nbsp;>&nbsp;")
                if gt > 0:
                    subtext = page.text[gt:]
                    start = subtext.find("<strong>") + 8
                    subtext = subtext[start:]
                    end = subtext.find("<")
                    top_cat = subtext[:end]
                    if "Ming" in top_cat:
                        ming = True
                    top_cat = top_cat.replace("Ming&#45;", "Ming and ")  # sold case
                    top_cat = sanitize(top_cat)
                    top_cat = top_cat.replace("Sold ", "")
                    top_cat = top_cat.replace("Sold", "")
                    if top_cat:
                        # find any associated notes
                        tds = content.find("td")
                        for td in tds:
                            if 'width="75%"' in td.html:
                                notes = td.text
                                break
                        cat, parents = categorise(top_cat)
                        if cat:
                            print(">>>", cat, parents)
                            # check parents are present
                            for c in parents:
                                queryset = Category.objects.filter(name=c)
                                if len(queryset) != 1:
                                    print(c, "is not present", cat)
                                    return
                            if len(Category.objects.filter(name=cat)) == 0:
                                if queryset:
                                    parent = queryset[0]
                                    parent.add_child(name=cat, description=notes)
                # Catalogue index page
                # Some pages have different sub categories e.g European Porcelain and Glass
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

                    cat, category = categorise(cat, index=True)
                    if cat:
                        try:
                            Category.objects.get(name=cat)
                        except Category.DoesNotExist:
                            parent = Category.objects.get(name=category[-1])
                            parent.add_child(name=cat, description=notes)
                            print(cat, "created on index page")
        else:
            # object grid page - all categories should exist now
            c = page.text.find('"actxsmall">Catalogue')
            s = page.text[c:].find("<strong>")
            top_cat = page.text[c:][s + 8 :]
            e = top_cat.find("</strong>")
            top_cat = top_cat[:e]
            if top_cat[:4] == "Sold":
                top_cat = top_cat[5:]
                sold = True
            p = top_cat.find(" Page")
            page_text = ""
            if p > 0:
                number = int(top_cat[p + 5 :])
                top_cat = top_cat[:p]
                page_text = f"Page {number}"
            top_cat = sanitize(top_cat)
            cat, category = categorise(top_cat, index=False)
            cat_db = None
            if cat:
                cat_db = Category.objects.filter(name=cat)
                if len(cat_db) != 1:
                    print(f">>> Object grid {cat} not found")
                else:
                    print("----------------------", page_text, cat)
                    cat_db = cat_db[0]
            else:
                print("ERROR: No cat found for", top_cat)

            # process a grid of objects
            # skip the enclosing table by starting at 1
            if options["objects"]:
                tables = content.find("table")
                for i in range(1, len(tables)):
                    tds = tables[i].find("td")
                    if len(tds) > 1:
                        images0 = tds[0].find("img")
                        alist = tds[1].find("a")
                        if images0 and alist:
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
                                price = price.replace(",", "")
                            sale_price = Decimal(price)
                            items = Item.objects.filter(ref=ref)
                            if len(items) == 1:
                                print(items[0].name, "found")
                            elif len(items) > 1:
                                print("Multiple items with ref", ref)
                            else:  # if found, just refresh the category and archive state
                                if options["create"]:
                                    item = Item.objects.create(
                                        name=truncate(description),
                                        ref=ref,
                                        description=description,
                                        sale_price=price,
                                        category=cat_db,
                                        image_file=image_file,
                                        archive=sold,
                                    )
                                    item.save()
                                    load_image(item, user)
                                    print(item.name, "created")
    except Exception as e:
        print(f"Exception {e} on {page.url}")
        pass


def sanitize(string):
    string = string.replace("&#45;", "-")
    string = string.replace("&#38;", "and")
    string = string.replace("&#44;", ",")
    string = string.replace("&#47;", "/")
    string = string.replace("Stuff", "Snuff")
    string = string.replace("&", "and")
    return string


def make_top_categories():
    Category.objects.all().delete()
    get = lambda node_id: Category.objects.get(pk=node_id)
    root = Category.add_root(name="Catalogue")
    chinese = root.add_child(name="Chinese")
    chinese.add_child(name="Drawings")
    chinese.add_child(name="Ming and Earlier")
    chinese.add_child(name="Qing Porcelain")
    chinese.add_child(name="Qing Works of Art")
    root.add_child(name="Japanese")
    european = root.add_child(name="European")
    european.add_child(name="Porcelain")
    european.add_child(name="Glass")
    pottery = european.add_child(name="Pottery")
    pottery.add_child(name="English Pottery")
    pottery.add_child(name="Italian Pottery")
    pottery.add_child(name="Spanish Pottery")
    pottery.add_child(name="French/German Pottery")
    pottery.add_child(name="Dutch Delft")
    root.add_child(name="Other")
    return


def categorise(cat, index=False):
    # retuns sanitized cat and list of parent categories
    # cat = "" for a category that exists with sub categories
    result = []
    if cat == "Blue and White" and index:
        return "", result
    if cat == "Pottery" and index:
        return "", result
    if "Armorials and European" in cat:
        if index:
            return "", result
        s = cat.find(">")
        if s > 0:
            cat = cat[2:]
    if "Imperial" in cat:
        result.append("Chinese")
        cat = "Imperial, Blanc de Chine and Monochromes"
    elif "Chinese" in cat:
        result.append("Chinese")
        cat = cat[8:]
        if cat == "Blue and White":
            if index:
                return "", result
            else:
                result.append("Qing Porcelain")
                cat = "Blue and White Porcelain"
        elif "Blue and White Qing" in cat:
            result.append("Qing Porcelain")
            cat = "Blue and White Porcelain"
        elif cat == "Famille-Rose":
            result.append("Qing Porcelain")
            cat = "Famille-Rose Porcelain"
        elif "Tea Wares" in cat:
            result.append("Qing Porcelain")
            cat = "Blue and White Tea Wares"
        elif "Kangxi" in cat or "Imari" in cat or "Famille" in cat:
            result.append("Qing Porcelain")
        elif "Qing Works" in cat:
            pass
        elif "Armorial Porcelain" in cat:
            cat = "Armorial Porcelain"
        elif "with European Designs" in cat:
            cat = "European Designs"
        elif "Ming" in cat and "arlier" in cat:
            cat = "Ming and Earlier"
        elif cat.find("mperial") <= 0:
            cat = cat.replace("Blanc", "Imperial, Blanc")
    elif "Japanese" in cat:
        result.append("Japanese")
        cat = cat[9:]
    elif "Dutch Delft" in cat:
        result.append("European")
        result.append("Pottery")
    elif "European" in cat:
        result.append("European")
        cat = cat[9:]
        if "Pottery" in cat:
            cat = cat[8:]
            result.append("Pottery")
        elif "Porcelain" in cat:
            result.append("Porcelain")
            cat = cat[10:]
            if "and Glass" in cat:
                cat = ""
            cat = "" if index else "Porcelain"
        elif "Glass" in cat:
            result.append("Glass")
            cat = "" if index else "Glass"
    else:
        result.append("Other")
    return cat, result
