from table_manager.tables import *
from notes.models import Note


class NoteTable(tables.Table):
    class Meta:
        model = Note
        fields = ("title", "content", "updated_at", "user")
        attrs = {"class": "table table-sm table-hover hover-link"}
        row_attrs = {"data-pk": lambda record: record.pk, "class": "table-row pl-4"}
