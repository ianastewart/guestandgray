from django.http import QueryDict
from django_tables2 import SingleTableView


class FilteredTableView(SingleTableView):
    """
    Generic view for django tables 2 with filter
    http://www.craigderington.me/django-generic-listview-with-django-filters-and-django-tables2/
    """

    filter_class = None
    formhelper_class = None
    context_filter_name = "filter"
    table_pagination = {"per_page": 10}
    as_list = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.total = None
        self.filter = None
        self.first_run = False

    def get_initial_data(self, **kwargs):
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

    def get_total(self, query_set):
        """ optional total shown above table"""
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        # context["lines"] = self.table_pagination["per_page"]
        if self.filter_class:
            context[self.context_filter_name] = self.filter
            context["first_run"] = self.first_run
        if self.total:
            context["total"] = self.total
        return context

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
                    filter = self.filter_class(
                        filter_data, queryset=query_set, request=self.request
                    )
                    query_set = filter.qs
                return self.process_table_data(query_set, no_list=True)
        return None
