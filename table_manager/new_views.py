import logging

from django.http import QueryDict
from django.shortcuts import redirect, render
from django_filters.views import FilterView
from django_htmx.http import HttpResponseClientRefresh, HttpResponseClientRedirect
from django_tables2 import SingleTableMixin
from django_tables2.export.views import ExportMixin

from table_manager.buttons import Button
from table_manager.session import save_columns, load_columns, toggle_column, save_per_page, update_url

logger = logging.getLogger(__name__)


class ExtendedTableView(ExportMixin, SingleTableMixin, FilterView):

    template_name = "table_manager/generic_table.html"
    filter_template_name = "table_manager/htmx_filter.html"
    columns_template_name = "table_manager/htmx_columns.html"

    context_filter_name = "filter"
    table_pagination = {"per_page": 25}
    header = ""
    #
    filter_row = False
    filter_button = False
    filter_modal = False
    #
    sticky_header = True
    buttons = None
    object_name = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.object_name and self.model:
            self.object_name = self.model._meta.object_name
        self.filter = None
        self.selected_objects = None

    def get(self, request, *args, **kwargs):
        if request.htmx:
            return self.get_htmx(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def rows_list(self):
        return [10, 15, 20, 25, 50, 100]

    def get_buttons(self):
        if self.allow_create:
            return [Button(f"New {self.object_name}", href="create")]
        return []

    def get_actions(self):
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        # load_columns(self.request, context["table"])
        context["buttons"] = self.get_buttons()
        context["actions"] = self.get_actions()
        context["columns"] = self.column_states(self.request)
        context["rows"] = self.rows_list()
        per_page = self.request.GET.get('per_page', self.table_pagination.get("per_page", 25))
        context["per_page"] = f"{per_page} rows"
        context["header"] = self.header

        context["default"] = True
        context["filter_button"] = self.filter_button
        return context

    def render_table_data(self, request, *args, **kwargs):
        """ Render only the table data"""
        saved_template_name = self.template_name
        self.template_name = "table_manager/htmx_table_data.html"
        response = super().get(request, *args, **kwargs)
        self.template_name = saved_template_name
        return response

    def post(self, request, *args, **kwargs):
        if "columns_save" in request.POST:
            column_list = []
            for key in request.POST.items():
                if key[1] == "on":
                    column_list.append(key[0])
            save_columns(request, column_list)
            return self.render_table_data(request, *args, **kwargs)
        # It's an action performed on a queryset
        if "select_all" in request.POST:
            self.selected_objects = self.filtered_query_set(request)
        else:
            self.selected_objects = self.model.objects.filter(pk__in=request.POST.getlist("selection"))

        path = request.path + request.POST["query"]
        if "export" in request.POST:
            if self.heading:
                self.export_name = self.heading
            return redirect(path + "&_export=xlsx" "")
        response = self.handle_action(request)
        return response if response else HttpResponseClientRefresh()

    def filtered_query_set(self, request):
        """ Recreate the queryset used in GET for use in POST """
        query_set = self.get_queryset()
        if self.filterset_class:
            parts = request.htmx.current_url.split("?")
            if len(parts) == 2:
                filter_data = QueryDict(parts[1])
                f = self.filterset_class(filter_data, queryset=query_set, request=self.request)
                return f.qs
        return query_set

    def handle_action(self, request):
        """
        The action is in the request.POST dictionary
        self.selected_objects is a queryset that contains the objects to be processed
        Possible return values:
        - None: (default) - reloads the last path
        - HttpResponse to be returned
        """
        return None

    def row_clicked(self, pk, target, url):
        """ User clicked on a row """
        return HttpResponseClientRefresh()

    def column_states(self, request):
        saved_columns = load_columns(request, self.table_class)
        column_states = []
        for k, v in self.table_class.base_columns.items():
            if v.verbose_name:
                column_states.append((k, v.verbose_name, k in saved_columns))
        return column_states

    def get_htmx(self, request, *args, **kwargs):
        if request.htmx.trigger_name == "filter" and self.filter_class:
            context = {"filter": self.filter_class(request.GET)}
            return render(request, self.filter_template_name, context)

        elif request.htmx.trigger_name == "filter_form":
            return self.render_table_data(request, *args, **kwargs)

        elif request.htmx.trigger_name == "columns":
            context = {"columns": self.column_states(request)}
            return render(request, self.columns_template_name, context)

        elif "id_col" in request.htmx.trigger:
            """ Click on column checkbox in dropdown re-renders the table """
            toggle_column(request, request.htmx.trigger_name[4:], self.table_class)
            return self.render_table_data(request, *args, **kwargs)

        elif "id_row" in request.htmx.trigger:
            rows = request.htmx.trigger_name
            save_per_page(request, rows)
            url = update_url(request.htmx.current_url, rows)
            return HttpResponseClientRedirect(url)

        elif "default" in request.htmx.trigger:
            """ Restore defaults if defined in Meta else all columns"""
            try:
                column_list = list(self.table_class.Meta.default_columns)
            except AttributeError:
                column_list = list(self.table_class.base_columns.keys())
            save_columns(request, column_list)
            return HttpResponseClientRefresh()

        elif request.htmx.trigger_name == "per_page":
            self.table_pagination = {"per_page": request.GET["per_page"]}
            return HttpResponseClientRefresh()

        elif "tr_" in request.htmx.trigger:
            return self.row_clicked(request.htmx.trigger.split("_")[1], request.htmx.target, request.htmx.current_url)

    # def _base_key(self):
    #     return self.request.resolver_match.view_name
    #
    # def _save_columns(self, column_list):
    #     key = f"{self._base_key()}:columns"
    #     self.request.session[key] = list(column_list)
    #
    # def _load_columns(self):
    #     key = f"{self._base_key()}:columns"
    #     if key in self.request.session:
    #         return self.request.session[key]
    #     if hasattr(self.table_class.Meta, "default_columns"):
    #         columns = self.table_class.Meta.default_columns
    #     else:
    #         columns = self.table_class.Meta.base_columns
    #     self._save_columns(columns)
    #     return columns
    #
    # def _toggle_column(self, column_name):
    #     columns = load_columns(self.request)
    #     columns.remove(column_name) if column_name in columns else columns.append(column_name)
    #     save_columns(self.request, columns)
    #
    # def _save_per_page(self, value):
    #     key = f"{self._base_key()}:per_page"
    #     self.request.session[key] = value
    #
    #
    # def _load_per_page(self):
    #     key = f"per_page:{self._base_key()}"
    #     if key in self.request.session:
    #         return self.request.session[key]
    #     return 0
