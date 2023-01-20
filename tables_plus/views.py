import logging
from enum import IntEnum
from django.http import QueryDict
from django.shortcuts import redirect, render
from django_filters.views import FilterView
from django_htmx.http import HttpResponseClientRefresh, HttpResponseClientRedirect
from django_tables2 import SingleTableMixin
from django_tables2.export.views import ExportMixin
from django_tables2.export.export import TableExport

from tables_plus.utils import (
    save_columns,
    load_columns,
    set_column,
    save_per_page,
)

logger = logging.getLogger(__name__)


class ExportMixinPlus(ExportMixin):
    def create_export(self, export_format):
        table = self.get_table(**self.get_table_kwargs())
        table.before_render(self.request)
        exclude_columns = [k for k, v in table.columns.columns.items() if not v.visible]
        exporter = self.export_class(
            export_format=export_format,
            table=table,
            exclude_columns=exclude_columns,
            dataset_kwargs=self.get_dataset_kwargs(),
        )
        return exporter.response(filename=self.get_export_filename(export_format))


class TablesPlusView(ExportMixinPlus, SingleTableMixin, FilterView):
    class FilterStyle(IntEnum):
        NONE = 0
        TOOLBAR = 1
        MODAL = 2
        HEADER = 3

    title = ""
    template_name = "tables_plus/table_plus.html"
    filter_template_name = "tables_plus/filter_modal.html"
    columns_template_name = "tables_plus/manage_columns.html"
    table_data_template_name = "tables_plus/render_table_data.html"
    rows_template_name = "tables_plus/render_rows.html"

    context_filter_name = "filter"
    table_pagination = {"per_page": 25}
    infinite_scroll = False
    #
    filter_style = FilterStyle.TOOLBAR
    filter_button = False  # only relevant for TOOLBAR style
    #
    sticky_header = False
    buttons = None
    object_name = ""
    #

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_objects = None

    def get(self, request, *args, **kwargs):
        if request.htmx:
            return self.get_htmx(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def rows_list(self):
        return [10, 15, 20, 25, 50, 100]

    def get_buttons(self):
        return []

    def get_actions(self):
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table = context["table"]
        table.filter = context["filter"]
        table.infinite_scroll = self.infinite_scroll
        table.before_render(self.request)
        if table.filter:
            table.filter.style = self.filter_style
            if self.filter_style == self.FilterStyle.HEADER:
                # build list of filters in same sequence as columns
                table.header_fields = []
                for key in table.columns.columns.keys():
                    if table.columns.columns[key].visible:
                        if key in table.filter.base_filters.keys():
                            table.header_fields.append(table.filter.form[key])
                        else:
                            table.header_fields.append(None)
        context.update(
            title=self.title,
            filter_button=self.filter_button,
            buttons=self.get_buttons(),
            actions=self.get_actions(),
            columns=self.column_states(self.request),
            rows=self.rows_list(),
            per_page=self.request.GET.get("per_page", self.table_pagination.get("per_page", 25)),
            default=True,
        )
        return context

    def render_table_data(self, request, *args, **kwargs):
        """Render only the table data"""
        saved_template_name = self.template_name
        self.template_name = self.table_data_template_name
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
        if "select_all" in request.POST and "?" in request.htmx.current_url:
            self.selected_objects = self.filtered_query_set(request, request.htmx.current_url)
        else:
            self.selected_objects = self.get_queryset().filter(pk__in=request.POST.getlist("select-checkbox"))

        if "export" in request.POST:
            path = request.path + request.POST["query"]
            if len(request.POST["query"]) > 1:
                path += "&"
            self.export_name = self.title if self.title else "Export"
            return HttpResponseClientRedirect(path + "_export=xlsx")

        response = self.handle_action(request)
        return response if response else HttpResponseClientRefresh()

    def filtered_query_set(self, request, url, next=False):
        """Recreate the queryset used in GET for use in POST"""
        query_set = self.get_queryset()
        parts = url.split("?")
        if len(parts) == 2 and self.filterset_class:
            qd = QueryDict(parts[1]).copy()
            if next:
                if "page" not in qd:
                    qd["page"] = "2"
                else:
                    qd["page"] = str(int(qd["page"]) + 1)
            return self.filterset_class(qd, queryset=query_set, request=request).qs
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
        """User clicked on a row"""
        return HttpResponseClientRefresh()

    def column_states(self, request):
        saved_columns = load_columns(request, self.table_class)
        column_states = []
        for k, v in self.table_class.base_columns.items():
            if v.verbose_name:
                column_states.append((k, v.verbose_name, k in saved_columns))
        return column_states

    def get_htmx(self, request, *args, **kwargs):
        if request.htmx.trigger_name == "filter" and self.filterset_class:
            # show filter modal
            context = {"filter": self.filterset_class(request.GET)}
            return render(request, self.filter_template_name, context)

        elif request.htmx.trigger_name == "filter_form":
            # a filter value was changed
            return self.render_table_data(request, *args, **kwargs)

        elif request.htmx.trigger_name == "columns":
            # show column dropdown
            context = {"columns": self.column_states(request)}
            return render(request, self.columns_template_name, context)

        elif "id_col" in request.htmx.trigger:
            # click on column checkbox in dropdown re-renders the table
            col_name = request.htmx.trigger_name[4:]
            checked = request.htmx.trigger_name in request.GET
            set_column(request, self.table_class, col_name, checked)
            return self.render_table_data(request, *args, **kwargs)

        elif "id_row" in request.htmx.trigger:
            # change number of rows to display
            rows = request.htmx.trigger_name
            save_per_page(request, rows)
            url = self._update_parameter(request, "per_page", rows)
            return HttpResponseClientRedirect(url)

        elif "default" in request.htmx.trigger:
            # restore default number of rows if defined in Meta else all columns"""
            try:
                column_list = list(self.table_class.Meta.default_columns)
            except AttributeError:
                column_list = list(self.table_class.base_columns.keys())
            save_columns(request, column_list)
            return HttpResponseClientRefresh()

        # elif request.htmx.trigger_name == "per_page":
        #     self.table_pagination = {"per_page": request.GET["per_page"]}
        #     return HttpResponseClientRefresh()

        elif "tr_" in request.htmx.trigger:
            if "_scroll" in request.GET:
                saved = self.template_name
                self.template_name = self.rows_template_name
                response = super().get(request, *args, **kwargs)
                self.template_name = saved
                return response

            return self.row_clicked(request.htmx.trigger.split("_")[1], request.htmx.target, request.htmx.current_url)

        elif "id_" in request.htmx.trigger:
            url = self._update_parameter(
                request, request.htmx.trigger_name, request.GET.get(request.htmx.trigger_name, "")
            )
            return HttpResponseClientRedirect(url)
        raise ValueError()

    @staticmethod
    def _update_parameter(request, key, value):
        query_dict = request.GET.copy()
        query_dict[key] = value
        return f"{request.path}?{query_dict.urlencode()}"
