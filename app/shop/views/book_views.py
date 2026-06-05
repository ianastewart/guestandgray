from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import reverse, redirect
from django.views.generic import UpdateView, CreateView, TemplateView, View
from django_tableaux.buttons import Button
from django.core.exceptions import ImproperlyConfigured
from django_tableaux.views import TableauxView
from shop.forms import BookForm, CompilerForm
from shop.models import Book, Compiler
from shop.tables import BookTable, CompilerTable
from django.template.response import TemplateResponse
from table_manager.views import AjaxCrudView
from django_htmx.http import HttpResponseClientRefresh, HttpResponseClientRedirect
from django.forms import models as model_forms


class CrudView(View):
    """
    View to handle Create and Update with optional Delete confirmation in update
    """

    model = None
    fields = None
    form_class = None
    template_name = ""
    object = None
    form = None
    update = False
    allow_delete = False
    confirm_delete = True
    success_url = None
    title = ""

    def get_object(self, **kwargs):
        self.object = self.model.objects.filter(pk=kwargs.get("pk", None)).first()
        return self.object

    def get(self, request, *args, **kwargs):
        self.form = self.get_form(instance=self.get_object(**kwargs))
        return self.render_to_response(self.get_context_data(form=self.form))

    def render_to_response(self, context):
        return TemplateResponse(
            request=self.request, template=self.template_name, context=context
        )

    def post(self, request, *args, **kwargs):
        self.get_object(**kwargs)
        if "delete" in request.POST:
            if self.object:
                self.object.delete()
                return self.success_response()
            raise ImproperlyConfigured(
                f"Delete action without object in {self.__class__.__name__}"
            )
        self.form = self.get_form(data=request.POST, instance=self.object)
        if self.form.is_valid():
            return self.form_valid(self.form)
        return self.form_invalid(self.form)

    def get_context_data(self, **kwargs):
        if not self.title:
            self.title = f"{'Update' if self.object else 'Create'} {self.model._meta.object_name.lower()}"
        kwargs["view"] = self
        kwargs["success_url"] = self.request.META["HTTP_REFERER"]
        kwargs["object_verbose_name"] = self.model._meta.verbose_name
        kwargs["context_object_name"] = self.model._meta.object_name.lower()
        if self.object:
            kwargs["object"] = self.object
        return kwargs

    def get_form_class(self):
        if self.form_class is not None:
            return self.form_class

        if self.model is not None and self.fields is not None:
            return model_forms.modelform_factory(self.model, fields=self.fields)

        msg = (
            "'%s' must either define 'form_class' or both 'model' and "
            "'fields', or override 'get_form_class()'"
        )
        raise ImproperlyConfigured(msg % self.__class__.__name__)

    def get_form(self, data=None, files=None, **kwargs):
        cls = self.get_form_class()
        return cls(data=data, files=files, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        return self.success_response()

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def success_response(self, **kwargs):
        if "hx_target" in self.request.POST:
            return HttpResponseClientRefresh()
        return HttpResponseClientRedirect(self.get_success_url())

    def get_success_url(self):
        if self.success_url:
            return self.success_url
        if "success_url" in self.request.POST:
            return self.request.POST["success_url"]
        raise ImproperlyConfigured(f"No success url" in {self.__class__.__name__})


class CompilerListView(LoginRequiredMixin, TableauxView):
    model = Compiler
    table_class = CompilerTable
    table_pagination = {"per_page": 100}
    template_name = "shop/table.html"
    click_action = TableauxView.ClickAction.GET
    click_url_name = "compiler_update"
    click_target = "#content"

    def get_queryset(self):
        return Compiler.objects.all().order_by("name")

    def get_buttons(self):
        return [Button("New compiler", href=reverse("compiler_create"))]


class CompilerCreateView(LoginRequiredMixin, CrudView):
    model = Compiler
    fields = ["name"]
    # form_class = CompilerForm
    template_name = "shop/crud_form.html"


class CompilerUpdateView(CompilerCreateView):
    update = True
    allow_delete = True


class BookListView(LoginRequiredMixin, TableauxView):
    model = Book
    table_class = BookTable
    template_name = "shop/table_wide.html"
    title = "Books"
    table_pagination = {"per_page": 100}
    click_action = TableauxView.ClickAction.HX_GET
    click_url_name = "book_update"
    click_target = "body"

    def get_queryset(self):
        return Book.objects.all().select_related("compiler").order_by("title")

    def get_buttons(self):
        return [Button("New book", href=reverse("book_create"))]


class BookCreateView(LoginRequiredMixin, CrudView):
    model = Book
    form_class = BookForm
    template_name = "shop/crud_form.html"


class BookUpdateView(BookCreateView):
    update = True
    allow_delete = True
