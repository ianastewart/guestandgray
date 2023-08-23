from django_tableaux.columns import *
from notes.models import Note
from django.shortcuts import reverse
from django.utils.text import Truncator


class NoteTable(tables.Table):
    class Meta:
        model = Note
        fields = ("title", "content", "item", "updated_at", "user")
        sequence = ("selection", "...")
        attrs = {"class": "table table-sm table-hover"}

    selection = SelectionColumn()

    @staticmethod
    def render_item(value):
        url = reverse("item_detail", kwargs={"pk": value.pk})
        return mark_safe(f'<a href="{url}">{value.ref}</a>')

    @staticmethod
    def render_updated_at(value):
        return value.strftime("%d/%m/%y")

    @staticmethod
    def render_content(value):
        return Truncator(value).words(25)
