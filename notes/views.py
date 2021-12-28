from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from notes.models import Note
from notes.forms import NoteForm
from notes.tables import NoteTable
from django.views.generic import CreateView, UpdateView, DetailView
from table_manager.views import FilteredTableView, AjaxCrudView


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
