import os
import datetime
from decimal import *
from django.conf import settings
from django.core.management.base import BaseCommand
from shop.models import Item, Contact, Invoice
from shop.truncater import truncate
from openpyxl import load_workbook


class Command(BaseCommand):
    help = "Process Excel stock file"

    def add_arguments(selfself, parser):
        parser.add_argument("workbook", type=str, help="workbook name")

    def handle(self, *args, **options):
        path = os.path.join(settings.MEDIA_ROOT, "excel", options["workbook"])
        if not os.path.exists(path):
            self.stdout.write(f"{path} does not exist")
        else:
            try:
                wb = load_workbook(filename=path, read_only=True, data_only=True)
                self.stdout.write(f"Workbook loaded")
                for ws in wb.worksheets:
                    # if ws.title == "Buyers":
                    #     self.import_buyers(ws)
                    # if ws.title == "Vendors":
                    #     self.import_vendors(ws)
                    #     vendors = Contact.objects.filter(vendor=True).count()
                    #     self.stdout.write(f"Created {vendors} vendors")
                    if "Stock" in ws.title:
                        self.import_stock(ws)
                # path = os.path.join(settings.MEDIA_ROOT, "excel", "stock-annotated.xlsx")
                # wb.save(path)
            except Exception as e:
                self.stdout.write(f"Exception processing sheet {ws.title} \n{str(e)}")

    def import_vendors(self, ws):
        self.stdout.write("Import vendors")
        Contact.objects.filter(vendor=True).delete()
        done = False
        max_address = 0
        max_name = 0
        for row in ws.iter_rows(min_row=1, min_col=2, max_row=500, max_col=2):
            for cell in row:
                if cell.value:
                    name, address = parse_name_address(cell.value, vendor=True)
                    if len(address) > max_address:
                        max_address = len(address)
                    if len(name) > max_name:
                        max_name = len(name)
                    Contact.objects.create(company=name, address=address, vendor=True)
                else:
                    done = True
            if done:
                break
        self.stdout.write(f"Name: {max_name} Address {max_address}")

    def import_buyers(self, ws):
        self.stdout.write("Import buyers")
        try:
            rowgen = ws.rows
            cols = [c.value for c in next(rowgen)]
            try:
                col_date = cols.index("Date")
                col_invoice_no = cols.index("Invoice no")
                col_address = cols.index("Address")
            except ValueError as e:
                self.stdout.write(f"Header error in sheet {ws.title}:\n{str(e)}")
                return
            Contact.objects.filter(buyer=True).delete()
            Invoice.objects.all().delete()
            new_contacts = 0
            existing_contacts = 0
            new_invoices = 0
            errors = 0
            for row in rowgen:
                dat = row[col_date].value
                number = row[col_invoice_no].value
                adr = row[col_address].value
                buyer = None
                if adr:
                    first_name, name, address = parse_name_address(adr)
                    contacts = Contact.objects.filter(company=name)
                    if len(contacts) > 0:
                        for contact in contacts:
                            if contact.address[:10] == address[:10]:
                                buyer = contact
                                existing_contacts += 1
                                if not buyer.buyer:
                                    buyer.buyer = True
                                    buyer.save()
                                break
                if not buyer and adr:
                    buyer = Contact.objects.create(
                        first_name=first_name, company=name, address=address, buyer=True
                    )
                    new_contacts += 1
                if number:
                    date = parse_date(dat)  # date defaults if missing
                    try:
                        Invoice.objects.create(date=date, number=number, buyer=buyer)
                        new_invoices += 1
                    except Exception as e:
                        self.stdout.write(f"Duplicate invoice: {number}")
                        errors += 1
                if not adr and not number and not dat:
                    pass
            self.stdout.write(
                f"New contacts: {new_contacts}, Existing contacts: {existing_contacts}, Invoices: {new_invoices} Errors: {errors}"
            )
        except Exception as e:
            self.stdout.write(f"Exception in {ws.title} row {row[0].row}\n{str(e)}")

    def import_stock(self, ws):
        self.stdout.write("Import stock")
        Item.objects.filter(category__isnull=True).delete()
        rowgen = ws.rows
        cols = [c.value for c in next(rowgen)]
        try:
            col_pdate = cols.index("PDate")
            col_vendor = cols.index("Vendor")
            col_cost_lot = cols.index("CostLot")
            col_cost_item = cols.index("CostItem")
            col_cost_rest = cols.index("Cost Rest")
            col_stock_no = cols.index("Stock No")
            col_description = cols.index("Full Description")
            col_price = cols.index("Price")
            col_sale_date = cols.index("SaleDate")
            col_inv_no = cols.index("InvNo")
            col_section = cols.index("Section Text")
        except ValueError as e:
            self.stdout.write(f"Header error in sheet {ws.title}:\n{str(e)}")
            return
        exists = 0
        created = 0
        try:
            for row in rowgen:
                try:
                    ref = row[col_stock_no].value
                    item = Item.objects.get(ref=ref)
                    exists += 1
                except Item.DoesNotExist:
                    description = row[col_description].value
                    price = row[col_price].value
                    if price == "refund" or price == "returned":
                        continue
                    if not price:
                        price = 0
                    inv = row[col_inv_no].value
                    archive = True if not inv else False
                    item = Item.objects.create(
                        name=truncate(description),
                        ref=ref,
                        description=description,
                        sale_price=Decimal(price),
                        category=None,
                        image=None,
                        archive=archive,
                        visible=False,
                    )
                    created += 1
                    self.stdout.write(str(ref))
                    pass
        except Exception as e:
            self.stdout.write(f"Exception in {ws.title} row {row[0].row}\n{str(e)}")
        self.stdout.write(f"Exists: {exists} Missing: {created}")


def parse_name_address(string, vendor=False):
    """ Separate name and address by first comma or first numeral """
    try:
        first_name = ""
        name = ""
        address = ""
        comma = string.find(",")
        if comma > 0:
            name = string[:comma].strip()
            address = string[comma + 1 :]
        else:
            i = has_digit(string)
            if i:
                name = string[:i].strip()
                address = string[i:]
            else:
                space = string.find(" ")
                if space > 0:
                    name = string[:space].strip()
                    address = string[space + 1 :]
                else:
                    name = "?"
                    address = string
        address = address.strip()
        if vendor:
            address = address.replace(", ", "\n").replace(",", "\n")
            return name, address
        # Try for a first name
        save_address = address
        if len(address) > 0 and not address[0].isdigit():
            comma = address.find(",")
            if comma > 0 and comma < 30:
                first_name = address[:comma].strip()
                address = address[comma + 1 :]
            else:
                at = address.find("@")
                if at > 0:
                    first_name = address[:at].strip()
                    address = address[at + 1 :]
                else:
                    i = has_digit(address)
                    if i < 20:
                        first_name = address[:i].strip()
                        address = address[i:]
                    else:
                        space = address.find(" ")
                        if space > 0 and space < 30:
                            first_name = address[:space].strip()
                            address = address[space + 1 :]
        address = address.strip().replace(", ", "\n").replace(",", "\n")
        if has_digit(first_name):  # or len(first_name) > 30:
            address = save_address
            first_name = ""
        return first_name, name, address
    except Exception as e:
        raise


def has_digit(string):
    """ return 0 if no digit else position of first digit """
    for i, c in enumerate(string):
        if c.isdigit():
            return i
    return 0


def parse_date(value):
    """ Parse date in form dd.mm.yy """
    if value:
        if type(value) is datetime.datetime:
            return value
        bits = value.split(".")
        if len(bits) == 3:
            day = int(bits[0])
            month = int(bits[1])
            year = int(bits[2])
            # handle known rogue values
            if year > 100:
                year -= 200
            if year > 50:
                year += 1900
            else:
                year += 2000
            if month == 35:
                month = 5
            return datetime.date(year, month, day)
        else:
            return datetime.date(2015, 9, 21)
    return datetime.date(1900, 1, 1)
