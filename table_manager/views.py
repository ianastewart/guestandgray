from django.contrib import messages
from django.http import QueryDict, JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View
from django.views.generic.edit import ModelFormMixin
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django_tables2 import SingleTableView
from django_tables2.export.views import ExportMixin
from shop.session import new_stack, push, pop


class FilteredTableView(ExportMixin, SingleTableView):
    """
    Generic view for django tables 2 with filter
    http://www.craigderington.me/django-generic-listview-with-django-filters-and-django-tables2/
    """

    template_name = "table_manager/generic_table.html"
    filter_class = None
    formhelper_class = None
    context_filter_name = "filter"
    table_pagination = {"per_page": 10}
    as_list = False
    heading = ""
    horizontal_form = False
    filter_left = True
    allow_create = False
    allow_update = False
    allow_detail = False
    auto_filter = False
    filter_button = "Filter"
    buttons = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.total = None
        self.filter = None
        self.first_run = False

    def get_initial_data(self):
        """ Initial values for filter """
        return self.table_pagination.copy()

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
        if self.filter_class and self.first_run:
            query_set = self.model.objects.none()
        else:
            query_set = self.get_queryset()
        if self.filter_class:
            initial = self.get_initial_data()
            for key, value in initial.items():
                if key == "per_page":
                    lines = value
                elif key in self.filter_class.base_filters and key not in filter_data:
                    filter_data[key] = value
            self.filter = self.filter_class(
                filter_data, queryset=query_set, request=self.request
            )
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
        return None

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
        context["object_name"] = self.model._meta.object_name
        context["buttons"] = self.get_buttons()
        context["actions"] = self.get_actions()
        context["allow_create"] = self.allow_create
        context["allow_update"] = self.allow_update
        context["allow_detail"] = self.allow_detail
        context["horizontal_form"] = self.horizontal_form
        context["heading"] = self.heading
        context["filter_left"] = self.filter_left
        context["auto_filter"] = self.auto_filter
        context["filter_button"] = self.filter_button
        return context

    def post(self, request, *args, **kwargs):
        """ post requests are actions performed on a queryset """

        self.selected_objects = self.post_query_set(request)
        if not self.selected_objects:
            self.selected_objects = self.model.objects.filter(
                pk__in=request.POST.getlist("selection")
            )

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
                    f = self.filter_class(
                        filter_data, queryset=query_set, request=self.request
                    )
                    query_set = f.qs
                return self.process_table_data(query_set, no_list=True)
        return None

    def handle_action(self, request):
        """ self.selected_objects is a queryset that returns the selection to be p[rocessed by the action """
        return None


class AjaxCrudView(ModelFormMixin, View):
    """ Generic view that handles creation, update and delete in a modal triggered by a FilteredListView """

    object = None
    form = None
    template_name = "table_manager/generic_modal_form.html"
    update = False
    allow_delete = False
    horizontal_form = False
    modal_id = "#modal-form"
    modal_class = ""

    def get_object(self, **kwargs):
        pk = kwargs.get("pk", None)
        if pk:
            try:
                self.object = self.model.objects.get(pk=pk)
                return self.object
            except:
                self.model.DoesNotExist
                pass
        return None

    def get(self, request, **kwargs):
        if request.is_ajax():
            data = {
                "path": request.path,
                "modal_id": self.modal_id,
                "modal_class": self.modal_class,
            }
            if "return_url" in request.GET:
                push(request, request.GET["return_url"])
            else:
                new_stack(request)
            try:
                self.get_object(**kwargs)
                # detail view will not have a form_class
                if self.form_class:
                    self.form = self.get_form()
                data["html_form"] = render_to_string(
                    self.template_name, self.get_context_data(), request
                )
            except TemplateDoesNotExist as e:
                data[
                    "html_form"
                ] = f"<h4>AjaxCrudView<br>Template not found: {str(e)}</h4>"
            except TemplateSyntaxError as e:
                data[
                    "html_form"
                ] = f"<h4>AjaxCrudView<br>Template syntax error: {str(e)}</h4>"
            except Exception as e:
                data["html_form"] = f"<h4>AjaxCrudView<br>Exception: {str(e)}</h4>"
            return JsonResponse(data)
        return HttpResponse("JsonCrudView received a non-ajax get request")

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            instance = self.get_object(**kwargs)
            return_url = pop(request)
            if not return_url:
                return_url = self.success_url
            data = {"return_url": return_url, "valid": True, "modal_id": self.modal_id}
            if "cancel" in request.POST:
                pass
            elif "delete" in request.POST:
                instance.delete()
                messages.add_message(
                    request, messages.INFO, f"{str(instance)} was deleted"
                )
            elif "save" in request.POST:
                if self.form_class:
                    self.form = self.get_form_class()(request.POST, instance=instance)
                    try:
                        if self.form.is_valid():
                            self.save_object(**kwargs)
                            if self.object:
                                data["pk"] = self.object.pk
                        else:
                            data["valid"] = False
                            data["html_form"] = render_to_string(
                                self.template_name, self.get_context_data(), request
                            )
                    except Exception as e:
                        data["valid"] = False
                        data["html_form"] = f"<h3>Exception: {str(e)}</h3>"
            return JsonResponse(data)
        return HttpResponse("JsonCrudView received a non-ajax post request")

    def save_object(self, **kwargs):
        self.object = self.form.save()

    def get_context_data(self):
        form_title = ""
        name = self.model._meta.object_name if self.model else ""
        if name:
            form_title = f"Update {name}" if self.update else f"Create {name}"
        context = {
            "modal": True,
            "modal_class": self.modal_class,
            "form": self.form,
            "path": self.request.path,
            "object_name": name,
            "form_title": form_title,
            "horizontal_form": self.horizontal_form,
            "allow_delete": self.allow_delete,
        }
        if self.object:
            context["object"] = self.object
            if name:
                context[name.lower()] = self.object
        return context
