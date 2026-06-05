from django.shortcuts import render, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from notes.models import Note
from notes.forms import NoteForm
from notes.tables import NoteTable
from django.views.generic import CreateView, UpdateView, DetailView, View
from table_manager.views import FilteredTableView, AjaxCrudView
from django_tableaux.views import TableauxView, SelectedMixin
from django_tableaux.buttons import Button
from shop.models import Item
from django_htmx.http import HttpResponseClientRefresh


class NoteListView(LoginRequiredMixin, TableauxView):
    model = Note
    table_class = NoteTable
    table_pagination = {"per_page": 100}
    template_name = "shop/table_wide.html"
    column_settings = True
    click_action = TableauxView.ClickAction.HX_GET
    click_url_name = "notes:update"

    def get_queryset(self):
        return Note.objects.all().order_by("title")

    def get_actions(self):
        return (("delete", "Delete"),)

    def handle_action(self, request, action):
        if action == "delete":
            self.selected_objects.delete()

    def get_buttons(self):
        return [
            Button("New note", hx_get=reverse("notes:htmx"), hx_target="#modals-here")
        ]


class NoteHtmxView(LoginRequiredMixin, View):
    """
    This view can be called from an item page or from the notes list page
    It handles both update and creation
    """

    def get(self, request, *args, **kwargs):
        template = "notes/note_form.html"
        pk = kwargs.get("pk", None)
        if pk:
            # Called from note list view
            note = Note.objects.filter(pk=pk).first()
            item = note.item
        elif request.htmx.trigger_name == "new-note":
            # Create called from note list view
            note = None
            item = None
        else:
            # Called from item view - trigger name contains item pk
            bits = request.htmx.trigger_name.split("-")
            item = Item.objects.filter(pk=bits[1]).first()
            note = Note.objects.filter(item=item).first() if item else None

        if note:
            form = NoteForm(initial={"title": note.title, "content": note.content})
        else:
            form = NoteForm()
        context = {"note": note, "form": form, "item": item}
        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        form = NoteForm(request.POST)
        item_pk = request.POST.get("item_pk", None)
        item = Item.objects.get(pk=item_pk) if item_pk else None
        note_pk = request.POST.get("note_pk", None)
        note = Note.objects.filter(pk=note_pk).first() if note_pk else None
        if note and "delete" in request.POST:
            note.delete()
            note = None
        elif form.is_valid():
            title = form.cleaned_data["title"]
            content = form.cleaned_data["content"]
            if not title and not content:
                if note:
                    note.delete()
                    note = None
            else:
                changed = False
                if not title:
                    title = item.ref if item else "Untitled"
                    changed = True
                if note:
                    if note.title != title:
                        note.title = title
                        changed = True
                    if note.content != content:
                        note.content = content
                        changed = True
                    if changed:
                        note.user = request.user
                        note.save()
                else:
                    note = Note.objects.create(
                        title=title, content=content, item=item, user=request.user
                    )
        return HttpResponseClientRefresh()
