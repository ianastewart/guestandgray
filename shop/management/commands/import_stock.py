import os
from django.conf import settings
from django.core.management.base import BaseCommand
from shop.models import Item, Contact
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
            wb = load_workbook(filename=path, read_only=True, data_only=True)
            for ws in wb.worksheets:
                if ws.title == "Vendors":
                    import_vendors(ws)
                    vendors = Contact.objects.filter(vendor=True).count()
                    self.stdout.write(f"Created {vendors} vendors")


def import_vendors(ws):
    Contact.objects.filter(vendor=True).delete()
    done = False
    max_address = 0
    max_name = 0
    for row in ws.iter_rows(min_row=1, min_col=2, max_row=500, max_col=2):
        for cell in row:
            if cell.value:
                comma = cell.value.find(",")
                if comma > 0:
                    name = cell.value[:comma].strip()
                    address = cell.value[comma + 1 :]
                else:
                    for i, c in enumerate(cell.value):
                        if c.isdigit():
                            name = cell.value[:i].strip()
                            address = cell.value[i:]
                            break
                address = address.strip().replace(", ", "\n").replace(",", "\n")
                print(name)
                print(address)
                print("---")
                if len(address) > max_address:
                    max_address = len(address)
                if len(name) > max_name:
                    max_name = len(name)
                Contact.objects.create(company=name, address=address, vendor=True)
            else:
                done = True
        if done:
            break
    print(f"Name: {max_name} Address {max_address}")
