import logging
from enum import IntEnum

from django.http import QueryDict, HttpResponse
from django.shortcuts import render, reverse
from django.urls.resolvers import NoReverseMatch
from django_filters.views import FilterView
from django_htmx.http import HttpResponseClientRefresh, HttpResponseClientRedirect, trigger_client_event
from django_tables2 import SingleTableMixin
from django_tables2.export.export import TableExport

from tables_plus.utils import (
    save_columns,
    load_columns,
    set_column,
    visible_columns,
    save_per_page,
)

logger = logging.getLogger(__name__)


class TablesPlusView(SingleTableMixin, FilterView):
    class FilterStyle(IntEnum):
        NONE = 0
        TOOLBAR = 1
        MODAL = 2
        HEADER = 3

    title = ""
    template_name = "tables_plus/table_plus.html"
    filter_template_name = "tables_plus/modal_filter.html"
    table_data_template_name = "tables_plus/render_table_data.html"
    rows_template_name = "tables_plus/render_rows.html"

    context_filter_name = "filter"
    table_pagination = {"per_page": 25}
    infinite_scroll = False
    infinite_load = False
    #
    filter_style = FilterStyle.TOOLBAR
    filter_button = False  # only relevant for TOOLBAR style
    #
    column_settings = False
    row_settings = True
    #
    click_method = "get"
    click_url_name = ""
    click_target = "#modals-here"
    #
    sticky_header = False
    buttons = []
    object_name = ""
    #
    export_format = "csv"
    export_class = TableExport
    export_name = "table"
    dataset_kwargs = None

    export_formats = (TableExport.CSV,)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_objects = None

    def get_export_filename(self, export_format):
        return "{}.{}".format(self.export_name, export_format)

    def get_dataset_kwargs(self):
        return self.dataset_kwargs

    def get(self, request, *args, **kwargs):
        if request.htmx:
            return self.get_htmx(request, *args, **kwargs)
        if "_export" in request.GET:
            export_format = request.GET.get("_export", self.export_format)
            qs = self.get_queryset()
            subset = request.GET.get("_subset", None)
            if subset:
                if subset == "selected":
                    qs = qs.filter(id__in=request.session.get("selected_ids", []))
                elif subset == "all":
                    filterset_class = self.get_filterset_class()
                    filterset = self.get_filterset(filterset_class)
                    if not filterset.is_bound or filterset.is_valid() or not self.get_strict():
                        qs = filterset.qs
            return self.export(request, query_set=qs)
        return super().get(request, *args, **kwargs)

    def export(self, request, filename="Export", export_format="csv", query_set=None, all_columns=False):
        """Use tablib to export in desired format"""
        self.object_list = query_set
        table = self.get_table()
        exclude_columns = []
        if not all_columns:
            table.before_render(request)
            exclude_columns = [k for k, v in table.columns.columns.items() if not v.visible]
        exclude_columns.append("selection")
        exporter = self.export_class(
            export_format=export_format,
            table=table,
            exclude_columns=exclude_columns,
            dataset_kwargs=self.get_dataset_kwargs(),
        )
        return exporter.response(filename=f"{filename}.{export_format}")

    def rows_list(self):
        return [10, 15, 20, 25, 50, 100]

    def get_buttons(self):
        return []

    def get_actions(self):
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.table = context["table"]
        self.preprocess_table(self.table, context["filter"])
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

    def post(self, request, *args, **kwargs):
        if request.htmx:
            if "td_" in request.htmx.target:
                bits = request.htmx.target.split("_")
                return self.cell_changed(
                    record_pk=bits[1],
                    column_name=visible_columns(request, self.table_class)[int(bits[2])],
                    target=request.htmx.target,
                )

        if "columns_save" in request.POST:
            column_list = []
            for key in request.POST.items():
                if key[1] == "on":
                    column_list.append(key[0])
            save_columns(request, column_list)
            return self.render_template(self.table_data_template_name, *args, **kwargs)

        # It's an action performed on a queryset`
        if "select_all" in request.POST:
            subset = "all"
            self.selected_objects = self.filtered_query_set(request, request.htmx.current_url)
        else:
            subset = "selected"
            request.session["selected_ids"] = request.POST.getlist("select-checkbox")
            self.selected_objects = self.get_queryset().filter(pk__in=request.POST.getlist("select-checkbox"))

        if "export" in request.POST:
            # Export is a special case which must redirect to a GET with parameters
            path = request.path + request.POST["query"]
            if len(request.POST["query"]) > 1:
                path += "&"
            export_format = self.get_export_format()
            return HttpResponseClientRedirect(f"{path}_export={export_format}&_subset={subset}")

        response = self.handle_action(request)
        return response if response else HttpResponseClientRefresh()

    def get_export_format(self):
        return self.export_format

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

    def cell_clicked(self, record_pk, column_name, target):
        """User clicked on a cell"""
        return HttpResponseClientRefresh()

    def cell_changed(self, record_pk, column_name, target):
        """Cell value changed"""
        return HttpResponseClientRefresh()

    def column_states(self, request):
        saved_columns = load_columns(request, self.table_class)
        column_states = []
        for key in self.table.sequence:
            verbose = self.table_class.base_columns[key].verbose_name
            if verbose:
                column_states.append((key, verbose, key in saved_columns))
        return column_states

    def get_htmx(self, request, *args, **kwargs):

        if request.htmx.trigger == "table_data":
            # triggered refresh of table data after create or update
            return self.render_template(self.table_data_template_name, *args, **kwargs)

        elif request.htmx.trigger_name == "filter" and self.filterset_class:
            # show filter modal
            context = {"filter": self.filterset_class(request.GET)}
            return render(request, self.filter_template_name, context)

        elif request.htmx.trigger_name == "filter_form":
            # a filter value was changed
            return self.render_template(self.table_data_template_name, *args, **kwargs)

        elif request.htmx.trigger_name == "load_more":
            return self.render_template(self.rows_template_name, *args, **kwargs)

        elif "id_col" in request.htmx.trigger:
            # click on column checkbox in dropdown re-renders the table
            col_name = request.htmx.trigger_name[4:]
            checked = request.htmx.trigger_name in request.GET
            set_column(request, self.table_class, col_name, checked)
            return self.render_template(self.table_data_template_name, *args, **kwargs)

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

        elif "tr_" in request.htmx.trigger:
            if "_scroll" in request.GET:
                return self.render_template(self.rows_template_name, *args, **kwargs)

            return self.row_clicked(request.htmx.trigger.split("_")[1], request.htmx.target, request.htmx.current_url)

        elif "td_" in request.htmx.trigger:
            # cell clicked
            bits = request.htmx.trigger.split("_")
            return self.cell_clicked(
                record_pk=bits[1],
                column_name=visible_columns(request, self.table_class)[int(bits[2])],
                target=request.htmx.target,
            )

        elif "id_" in request.htmx.trigger:
            # filter value changed
            url = self._update_parameter(
                request, request.htmx.trigger_name, request.GET.get(request.htmx.trigger_name, "")
            )
            return HttpResponseClientRedirect(url)

        raise ValueError("Bad htmx get request")

    def preprocess_table(self, table, _filter):
        """Add extra attributes needed for rendering to the table"""
        table.filter = _filter
        table.infinite_scroll = self.infinite_scroll
        table.infinite_load = self.infinite_load
        table.method = self.click_method
        table.url = ""
        table.pk = False
        if self.click_url_name:
            # handle case when there is no PK passed (create)
            try:
                table.url = reverse(self.click_url_name)
            except NoReverseMatch:
                # Detail or update views have a pk
                try:
                    table.url = reverse(self.click_url_name, kwargs={"pk": 0})[:-2]
                    table.pk = True
                except NoReverseMatch:
                    pass
        table.target = self.click_target
        editable = table.Meta.editable_columns if hasattr(table.Meta, "editable_columns") else []
        # set columns visbility
        columns = load_columns(self.request, table)
        if not columns:
            if hasattr(table.Meta, "default_columns"):
                columns = table.Meta.default_columns
            else:
                columns = table.base_columns
            save_columns(self.request, columns)
        for k, v in table.base_columns.items():
            if v.verbose_name:
                table.columns.show(k) if k in columns else table.columns.hide(k)
        # build a string containing the numbers of visible editable columns
        visible = [col for col in table.sequence if col in columns]
        editable = table.Meta.editable_columns if hasattr(table.Meta, "editable_columns") else []
        table.editable_columns = editable
        if table.filter:
            table.filter.style = self.filter_style
            if self.filter_style == self.FilterStyle.HEADER:
                # build list of filters in same sequence as columns
                table.header_fields = []
                for key in table.sequence:
                    if table.columns.columns[key].visible:
                        if key in table.filter.base_filters.keys():
                            table.header_fields.append(table.filter.form[key])
                        else:
                            table.header_fields.append(None)

    def render_template(self, template_name, *args, **kwargs):
        saved = self.template_name
        self.template_name = template_name
        response = super().get(self.request, *args, **kwargs)
        self.template_name = saved
        return response

    @staticmethod
    def _update_parameter(request, key, value):
        query_dict = request.GET.copy()
        query_dict[key] = value
        return f"{request.path}?{query_dict.urlencode()}"


class ModalMixin:
    """Mixin to convert generic views to operate as modal views when called by hx-get"""

    title = ""

    def get_template_names(self):
        # handle case where same view can have different templates
        if self.request.htmx:
            if hasattr(self, "modal_template_name"):
                return [self.modal_template_name]
        if hasattr(self, "template_name"):
            return [self.template_name]
        raise ValueError("Template name missing")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url = self.request.resolver_match.route
        if "<int:pk>" in url and self.object:
            url = url.replace("<int:pk>", str(self.object.pk))
        context["modal_url"] = "/" + url
        return context

    def reload_table(self):
        response = HttpResponse("")
        return trigger_client_event(response, "reload", {"url": self.request.htmx.current_url_abs_path})
