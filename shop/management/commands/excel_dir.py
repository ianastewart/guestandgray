import os

from django.core.management.base import BaseCommand
from openpyxl import Workbook

from shop.management.utils import sanitize


class Command(BaseCommand):
    help = "Create excel file containing filenames"

    def add_arguments(self, parser):
        parser.add_argument("directory", type=str, help="Source directory path")

    def handle(self, *args, **options):
        path = options["directory"]
        dir_name = "Excel directory.xlsx"
        if not os.path.exists(path):
            self.stdout.write(f"{path} does not exist")
        else:
            book = Workbook()
            sheet = book.active
            files = os.listdir(path)
            files.sort()
            row = 1
            for name in files:
                if name != dir_name:
                    sheet.cell(row=row, column=1).value = name
                    ref, changed, new_name = sanitize(name)
                    sheet.cell(row=row, column=2).value = ref
                    if changed:
                        sheet.cell(row=row, column=3).value = new_name
                    row += 1
            target = os.path.join(path, dir_name)
            try:
                os.remove(target)
            except OSError:
                pass
            book.save(target)
