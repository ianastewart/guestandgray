import linecache
import logging
import sys
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, QueryDict
from django.shortcuts import redirect
from django.template.loader import render_to_string, TemplateDoesNotExist
from django.views.generic import View
from django.views.generic.edit import ModelFormMixin
from django_tables2 import SingleTableView
from django_tables2.export.views import ExportMixin
from django.utils.html import mark_safe
from table_manager.buttons import AjaxButton
from table_manager.session import debug_stack, new_stack, pop, push
from django.conf import settings

logger = logging.getLogger(__name__)

class FilteredTableView(ExportMixin, SingleTableView):
    """
    Generic view for django tables 2 with filter
    http://www.craigderington.me/django-generic-listview-with-django-filters-and-django-tables2/
    """

    template_name = "table_manager/generic_table.html"
    filter_class = None
    formhelper_class = None
    context_filter_name = "filter"
    table_pagination = {"per_page": 25}
    as_list = False
    heading = ""
    horizontal_form = False
    wide_screen = False
    allow_create = False
    allow_update = False
    allow_detail = False
    filter_button = None
    buttons = None
    column_shifter = None
    object_name = ""
    filter_left = False
    filter_right = False
    css_title = "bg-white"
    css_filter = "bg-light"
    css_actions = "bg-white"
    css_table = "bg-white"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.object_name and self.model:
            self.object_name = self.model._meta.object_name
        self.total = None
        self.filter = None
        self.first_run = False

    def get_initial_data(self):
        """ Initial values for filter """
        if self.table_pagination:
            return self.table_pagination.copy()
        return {}

    def get_table_data(self):
        """ Returns a filtered queryset"""
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
        # if self.filter_class and self.first_run:
        #     query_set = self.get_queryset()
        # else:
        #     query_set = self.get_queryset()
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

    def process_table_data(self, query_set, no_list=False):
        """
        Process table data after it has been filtered, before it is rendered.
        Used, for example to convert filtered junior records into parent records
        Also can calculate a total or return a list when table uses properties
        """
        self.total = self.get_total(query_set)
        if self.as_list and not no_list:
            return list(query_set)
        return query_set

    def get_total(self, query_set=None):
        """ optional total shown above table"""
        return None

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
        if self.total:
            context["total"] = self.total
        context["object_name"] = self.object_name
        context["buttons"] = self.get_buttons()
        context["actions"] = self.get_actions()
        context["allow_create"] = self.allow_create
        context["allow_update"] = self.allow_update
        context["allow_detail"] = self.allow_detail
        context["horizontal_form"] = self.horizontal_form
        context["heading"] = self.heading
        context["filter_button"] = self.filter_button
        context["filter_left"] = self.filter_left
        context["filter_right"] = self.filter_right
        context["column_shifter"] = self.column_shifter
        return context

    def post(self, request, *args, **kwargs):
        """ post requests are actions performed on a queryset """

        self.selected_objects = self.post_query_set(request)
        if not self.selected_objects:
            self.selected_objects = self.model.objects.filter(pk__in=request.POST.getlist("selection"))

        path = request.path + request.POST["query"]
        if "export" in request.POST:
            if self.heading:
                self.export_name = self.heading
            return redirect(path + "&_export=xlsx" "")

        success_url = self.handle_action(request)
        if success_url:
            return redirect(success_url)
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
                return self.process_table_data(query_set, no_list=True)
        return None

    def handle_action(self, request):
        """
        The actions are in request.POST as normal
        self.selected_objects is a queryset that contains the selection to be processed by the action"""
        return None


class AjaxCrudView(ModelFormMixin, View):
    """ Generic view that handles creation, update and delete in a modal triggered by a FilteredListView """

    object = None
    object_name = None
    form = None
    template_name = "table_manager/generic_modal_form.html"
    update = False
    allow_delete = False
    target_id = "#modal-form"
    title = ""
    no_validate = False

    def get_object(self, **kwargs):
        pk = kwargs.get("pk", None)
        if pk:
            try:
                self.object = self.model.objects.get(pk=pk)
                return self.object
            except self.model.DoesNotExist:
                return None
        return None

    def get(self, request, **kwargs):
        if request.is_ajax():
            return_url = request.GET["return_url"]
            no_push = request.GET["no_push"] == "true"
            if return_url == "":
                new_stack(request)
            if not no_push:
                push(request, return_url, True)
            data = {}
            data["path"] = request.path
            data["target_id"] = self.target_id
            data["html"] = self.render(request, **kwargs)
            return JsonResponse(data)
        return HttpResponse("JsonCrudView received a non-ajax get request")

    def render(self, request, **kwargs):
        """ get context and return html """
        try:
            self.get_object(**kwargs)
            # detail view will not have a form_class
            if self.form_class:
                self.form = self.get_form()
            self.context = self.get_context_data()
            self.context["buttons"] = self.get_buttons()
            html = render_to_string(self.template_name, self.context, request)
        except TemplateDoesNotExist as e:
            html = self._format_exception("Template does not exist", e)
        except Exception as e:
            message = "AjaxCrudView Exception in GET"
            html = self._format_exception(message, e)
        return html

    def post(self, request, *args, **kwargs):
        debug_stack(request)
        if not request.is_ajax():
            return HttpResponse("JsonCrudView received a non-ajax post request")
        target_id = request.POST.get("x_target_id")
        if not target_id:
            target_id = self.target_id
        validate = request.POST.get("x_validate") == "true" and not self.no_validate
        action_response = None
        next_is_ajax = True
        # default return values assuming simple crud operation was successful
        data = {"target_id": target_id, "html": ""}
        try:
            self.instance = self.get_object(**kwargs)
            if "cancel" in request.POST:
                self.cancel(data)
                return JsonResponse(self._set_next_url(data))

            elif "submit_delete" in request.POST:
                self.delete(data)
                return JsonResponse(self._set_next_url(data))

            if validate:
                if self.form_class:
                    self.form = self.get_form()
                    # self.form = self.get_form_class()(request.POST, instance=self.instance)
                    form_valid = self.form.is_valid()
                    if not form_valid:
                        data["html"] = self.render(request, **kwargs)
                        # its possible that get context data will have set form_class=None
                        if self.form_class:
                            data["form_invalid"] = True
                            return JsonResponse(data)

                    else:
                        if "submit_save" in request.POST:
                            # default save action only works for a model form
                            if hasattr(self.form, "save"):
                                self.save_object(data, **kwargs)
                                action_response = self.handle_action("save", pk=self.object.pk)

            if action_response is None:
                for key in request.POST.keys():
                    if "submit_" in key or "action_" in key:
                        bits = key.split("_")
                        action = bits[1] if len(bits) > 1 else ""
                        pk = bits[2] if len(bits) > 2 else None
                        value = bits[3] if len(bits) > 3 else None
                        action_response = self.handle_action(action, pk=pk, value=value)

            if action_response:
                # response can be tuple(url, is_ajax) or just a url which is assumed as ajax
                if type(action_response) is tuple and len(action_response) > 0:
                    next_url = action_response[0]
                    if len(action_response) > 1:
                        next_is_ajax = action_response[1]
                else:
                    next_url = action_response
            else:
                next_url = ""
                next_is_ajax = False
            return JsonResponse(self._set_next_url(data, next_url=next_url, next_is_ajax=next_is_ajax))

        except Exception as e:
            message = "Exception in POST"
            data["error"] = True
            data["html"] = self._format_exception(message, e)
        return JsonResponse(data)

    def _set_next_url(self, data, next_url=None, next_is_ajax=False):
        if next_url == "":
            next_url, next_is_ajax = pop(self.request)
        data["next_url"] = next_url
        data["is_ajax"] = next_is_ajax
        data["no_push"] = self.request.POST.get("x_no_return") == "true"
        return data

    def save_object(self, data, **kwargs):
        self.object = self.form.save()
        data["pk"] = self.object.pk if self.object else ""

    def cancel(self, data):
        pass

    def delete(self, data):
        self.instance.delete()
        messages.add_message(self.request, messages.INFO, f"{str(self.instance)} was deleted")

    def next_url(self, pk=None):
        """ called after save so a new form can be shown in a modal """
        return ""

    def handle_action(self, action, **kwargs):
        """ return a url. "" or a tuple (url, is_ajax) """
        return ""

    def get_context_data(self, **kwargs):
        name = self.model._meta.object_name if self.model else ""
        if self.object_name:
            name = self.object_name
        if not self.title:
            if name:
                self.title = f"Update {name}" if self.update else f"Create {name}"
        context = {
            "view": self,
            "modal": True,
            "form": self.form,
            "path": self.request.path,
            "object_name": name,
            "form_title": self.title,
            "update": self.update,
        }

        if self.object:
            context["object"] = self.object
            if name:
                context[name.lower()] = self.object
        return context

    def get_buttons(self):
        """ This is called after self.context has been defined """
        self.buttons = [AjaxButton("Save")]
        if self.allow_delete:
            self.buttons.insert(0, AjaxButton("Delete", button_class="btn-danger"))
        return self.buttons

    def _format_exception(self, message, e):

        exc_type, exc_obj, tb = sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        trace = f"{exc_obj}\n{filename}, line {lineno}\n{line}"
        logger.error(f"{message}\n{trace}")
        trace = mark_safe(trace.replace("\n", "<br>"))
        context = {"message": message, "path": self.request.path, "trace": trace, "debug": settings.DEBUG}
        if hasattr(e, "template_debug"):
            context["template_name"] = e.template_debug["name"]
            context["during"] = e.template_debug["during"]
        return render_to_string("table_manager/modal_error_template.html", context, request=None)
