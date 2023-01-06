import linecache
import logging
import sys
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, QueryDict
from django.shortcuts import redirect, render
from django.template.loader import render_to_string, TemplateDoesNotExist
from django.views.generic import View
from django.views.generic.edit import ModelFormMixin
from django_tables2 import SingleTableView
from django_tables2.export.views import ExportMixin
from django.utils.html import mark_safe
from table_manager.buttons import AjaxButton
from table_manager.session import debug_stack, new_stack, pop, push
from django.conf import settings
from table_manager.session import save_columns, load_columns, toggle_column
from django_htmx.http import HttpResponseClientRefresh

logger = logging.getLogger(__name__)


class ExtendedTableView(ExportMixin, SingleTableView):
    """
    Generic view for django tables 2 with filter
    http://www.craigderington.me/django-generic-listview-with-django-filters-and-django-tables2/
    """

    template_name = "table_manager/generic_table.html"
    filter_template_name = "table_manager/htmx_filter.html"
    columns_template_name = "table_manager/htmx_columns.html"
    filter_class = None
    context_filter_name = "filter"
    table_pagination = {"per_page": 25}
    header = ""
    #
    filter_row = False
    filter_button = False
    filter_modal = False
    #
    sticky_header = True
    allow_create = False
    allow_update = False
    allow_detail = False

    buttons = None
    object_name = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.object_name and self.model:
            self.object_name = self.model._meta.object_name
        self.filter = None
        self.first_run = False

    def get(self, request, *args, **kwargs):
        if request.htmx:
            return self.get_htmx(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def get_initial_data(self):
        """Initial values for filter"""
        if self.table_pagination:
            return self.table_pagination.copy()
        return {}

    def get_table_data(self):
        """Returns a filtered queryset"""
        filter_data = self.request.GET.copy()
        lines = 0
        self.first_run = len(filter_data) == 0
        per_page = filter_data.pop("per_page", None)
        if per_page:
            try:
                lines = int(per_page[0])
                self.table_pagination["per_page"] = lines
            except ValueError:
                pass
        # When first called there will be no parameters in the url. We initialise the filter with the correct values
        # but return an empty queryset and set the first_run flag
        # When rendered the filter form will get submitted through javascript and the correct data gets populated
        if self.object_list:
            query_set = self.object_list
        else:
            query_set = self.get_queryset()
        if self.filter_class:
            initial = self.get_initial_data()
            for key, value in initial.items():
                if key == "per_page":
                    lines = value
                elif key in self.filter_class.base_filters and key not in filter_data:
                    filter_data[key] = value
            self.filter = self.filter_class(filter_data, queryset=query_set, request=self.request)
            query_set = self.filter.qs
            if lines:
                self.filter.data["per_page"] = lines
        return self.process_table_data(query_set)

    def process_table_data(self, query_set):
        """
        Process table data after it has been filtered, before it is rendered.
        Used, for example to convert filtered junior records into parent records
        Also can calculate a total or return a list when table uses properties
        """
        return query_set

    def get_buttons(self):
        if self.allow_create:
            return [AjaxButton(f"New {self.object_name}", href="create")]
        return []

    def get_actions(self):
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        # context["lines"] = self.table_pagination["per_page"]
        if self.filter_class:
            context[self.context_filter_name] = self.filter
            context["first_run"] = self.first_run
        context["object_name"] = self.object_name
        context["buttons"] = self.get_buttons()
        context["actions"] = self.get_actions()
        context["allow_create"] = self.allow_create
        context["allow_update"] = self.allow_update
        context["allow_detail"] = self.allow_detail
        context["header"] = self.header
        context["columns"] = self.column_states(self.request)
        context["default"] = True
        context["filter_button"] = self.filter_button
        return context

    def render_table_data(self, request, *args, **kwargs):
        """Render only the table data"""
        saved_template_name = self.template_name
        self.template_name = "table_manager/htmx_table_data.html"
        response = super().get(request, *args, **kwargs)
        self.template_name = saved_template_name
        return response

    def post(self, request, *args, **kwargs):
        """post requests are actions performed on a queryset"""
        if request.htmx:
            return self.post_htmx(request, *args, **kwargs)
        self.selected_objects = self.post_query_set(request)
        if not self.selected_objects:
            self.selected_objects = self.model.objects.filter(pk__in=request.POST.getlist("selection"))

        path = request.path + request.POST["query"]
        if "export" in request.POST:
            if self.heading:
                self.export_name = self.heading
            return redirect(path + "&_export=xlsx" "")

        response = self.handle_action(request)
        if response:
            if response.__class__.__name__ in ["JsonResponse", "HttpResponse"]:
                return response
            # assume its a path to redirect to
            return redirect(response)
        if "per_page" in request.POST:
            path += f"&per_page={request.POST['per_page']}"
        return redirect(path)

    def post_query_set(self, request):
        """
        May be called during a POST request.
        If 'Select all' has been pressed, return a queryset of all records matching the filter
        data which is posted in a hidden query field. It has paging information stripped out by
        the tables2 'querystring' template tag
        """
        if "select_all" in request.POST:
            query = request.POST.get("query", None)
            if query:
                if query[0] == "?":
                    query = query[1:]
                filter_data = QueryDict(query)
                query_set = self.get_queryset()
                if self.filter_class:
                    f = self.filter_class(filter_data, queryset=query_set, request=self.request)
                    query_set = f.qs
                return self.process_table_data(query_set)
        return None

    def handle_action(self, request):
        """
        The actions are in request.POST as normal
        self.selected_objects is a queryset that contains the selection to be processed by the action
        Possible return values:
        - None: (default) - reloads the last path
        - url - redirect to the url
        - JsonResponse - return it
        """
        return None

    def column_states(self, request):
        saved_columns = load_columns(request)
        column_states = []
        for k, v in self.table_class.base_columns.items():
            if v.verbose_name:
                column_states.append((k, v.verbose_name, k in saved_columns))
        return column_states

    def get_htmx(self, request, *args, **kwargs):
        if request.htmx.trigger_name == "filter" and self.filter_class:
            context = {"filter": self.filter_class()}
            return render(request, self.filter_template_name, context)

        elif request.htmx.trigger_name == "filter_form":
            return self.render_table_data(request, *args, **kwargs)

        elif request.htmx.trigger_name == "columns":
            context = {"columns": self.column_states(request)}
            return render(request, self.columns_template_name, context)

        elif "id_col" in request.htmx.trigger:
            """Click on column checkbox in dropdown has an immediate effect"""
            toggle_column(request, request.htmx.trigger_name)
            return self.render_table_data(request, *args, **kwargs)

        elif "default" in request.htmx.trigger:
            """Restore defaults if defined in Meta else all columns"""
            try:
                column_list = list(self.table_class.Meta.default_columns)
            except AttributeError:
                column_list = list(self.table_class.base_columns.keys())
            save_columns(request, column_list)
            return HttpResponseClientRefresh()

        elif request.htmx.trigger_name == "per_page":
            self.table_pagination = {"per_page": request.GET['per_page']}
            return HttpResponseClientRefresh()

    def post_htmx(self, request, *args, **kwargs):
        if "columns_save" in request.POST:
            column_list = []
            for key in request.POST.items():
                if key[1] == "on":
                    column_list.append(key[0])
            save_columns(request, column_list)
            return self.render_table_data(request, *args, **kwargs)
