import os
import datetime
from django.conf import settings
from django.db import transaction
from django.core.management.base import BaseCommand
from shop.models import Item, Contact, Invoice
from decimal import *
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
                wb = load_workbook(filename=path, data_only=True)
                self.stdout.write(f"Workbook loaded")
                for ws in wb.worksheets:
                    if ws.title == "Buyers":
                        self.import_buyers(ws)
                    # if ws.title == "Vendors":
                    #     self.import_vendors(ws)
                    #     vendors = Contact.objects.filter(vendor=True).count()
                    #     self.stdout.write(f"Created {vendors} vendors")
                    # if "Stock" in ws.title:
                    #     self.check_stock(ws)
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
            date = parse_date(row[col_date].value)
            number = row[col_invoice_no].value
            adr = row[col_address].value
            if adr:
                first_name, name, address = parse_name_address(adr)
                buyer = None
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
                try:
                    with transaction.atomic():
                        if not buyer:
                            buyer = Contact.objects.create(
                                first_name=first_name,
                                company=name,
                                address=address,
                                buyer=True,
                            )
                            new_contacts += 1
                        if number:
                            Invoice.objects.create(
                                date=date, number=number, buyer=buyer
                            )
                            new_invoices += 1
                except Exception as e:
                    self.stdout.write(f"Duplicate invoice: {number}")
                    errors += 1
            else:
                break
        self.stdout.write(
            f"New contacts: {new_contacts}, Existing contacts: {existing_contacts}, Invoices: {new_invoices} Errors: {errors}"
        )

    def check_stock(self, ws):
        col_PDate = 1
        col_Stock_No = 15
        exists = 0
        missing = 0
        date = None
        for row in ws.rows:
            if row[1] == "PDate":
                continue
            try:
                ref = row[col_Stock_No]
                item = Item.objects.get(ref=ref)
                exists += 1
            except Item.DoesNotExist:
                row[21].value = "Missing"
                missing += 1
                self.stdout.write(str(ref))
                pass
        self.stdout.write(f"Exists: {exists} Missing: {missing}")


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
        if not address[0].isdigit():
            comma = address.find(",")
            if comma > 0:
                first_name = address[:comma].strip()
                address = address[comma + 1 :]
            else:
                i = has_digit(address)
                if i:
                    first_name = address[:i].strip()
                    address = address[i:]
                else:
                    space = address.find(" ")
                    if space > 0:
                        first_name = address[:space].strip()
                        address = address[space + 1 :]
        address = address.strip().replace(", ", "\n").replace(",", "\n")
        if has_digit(first_name):
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


def parse_date(string):
    """ Parse date in form dd.mm.yy """
    if string:
        bits = string.split(".")
        day = int(bits[0])
        month = int(bits[1])
        year = int(bits[2])
        if year > 50:
            year += 1900
        else:
            year += 2000
        return datetime.date(year, month, day)
    return datetime.date(1900, 1, 1)
