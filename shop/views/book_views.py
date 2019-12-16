import logging
from django.contrib.auth.mixins import LoginRequiredMixin

from shop.forms import BookForm, CompilerForm
from shop.models import Book, Compiler
from shop.tables import BookTable, CompilerTable
from table_manager.views import FilteredTableView, AjaxCrudView


class CompilerListView(LoginRequiredMixin, FilteredTableView):
    model = Compiler
    table_class = CompilerTable
    table_pagination = {"per_page": 100}
    allow_create = True
    allow_update = True

    def get_queryset(self):
        return Compiler.objects.all().order_by("name")


class CompilerCreateView(LoginRequiredMixin, AjaxCrudView):
    model = Compiler
    form_class = CompilerForm


class CompilerUpdateView(CompilerCreateView):
    update = True
    allow_delete = True


class BookListView(LoginRequiredMixin, FilteredTableView):
    model = Book
    table_class = BookTable
    table_pagination = {"per_page": 100}
    allow_create = True
    allow_update = True

    def get_queryset(self):
        return Book.objects.all().select_related("compiler").order_by("title")


class BookCreateView(LoginRequiredMixin, AjaxCrudView):
    model = Book
    form_class = BookForm


class BookUpdateView(BookCreateView):
    update = True
    allow_delete = True
