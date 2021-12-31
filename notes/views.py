from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from notes.models import Note
from notes.forms import NoteForm
from notes.tables import NoteTable
from django.views.generic import CreateView, UpdateView, DetailView, View
from table_manager.views import FilteredTableView, AjaxCrudView
from shop.models import Item


class NoteListView(LoginRequiredMixin, FilteredTableView):
    model = Note
    table_class = NoteTable
    table_pagination = {"per_page": 100}
    allow_create = True
    allow_update = True

    def get_queryset(self):
        return Note.objects.all().order_by("title")


class NoteCreateView(LoginRequiredMixin, AjaxCrudView):
    model = Note
    form_class = NoteForm

    def save_object(self, data, **kwargs):
        super().save_object(data, **kwargs)
        self.object.user = self.request.user
        self.object.save()


class NoteUpdateView(NoteCreateView):
    update = True
    allow_delete = True


class NoteHtmxView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        bits = request.htmx.trigger_name.split("-")
        item = Item.objects.filter(pk=bits[1]).first()
        note = Note.objects.filter(item=item).first() if item else None
        template = "notes/note_form.html"
        if note:
            form = NoteForm(initial={"title": note.title, "content": note.content})
        else:
            form = NoteForm()
        context = {"note": note, "form": form, "item": item}
        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        template = "notes/close_modal.html"
        form = NoteForm(request.POST)
        item = Item.objects.get(pk=request.POST["item"])
        note = Note.objects.filter(item=item).first() if item else None
        if "delete" in request.POST:
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
                if not title:
                    title = item.ref
                if note:
                    note.title = title
                    note.content = content
                    note.user = request.user
                    note.save()
                else:
                    note = Note.objects.create(
                        title=title, content=content, item=item, user=request.user
                    )
        context = {"note": note, "item": item}
        return render(request, template, context)
