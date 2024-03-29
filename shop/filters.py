from django_filters import (
    CharFilter,
    ChoiceFilter,
    DateFilter,
    FilterSet,
    ModelChoiceFilter,
    BooleanFilter,
)
from tempus_dominus.widgets import DatePicker
from django.contrib.postgres.search import SearchVector
from shop.models import Category, Compiler, Item, Contact


# noinspection PyUnusedLocal
class ItemFilter(FilterSet):
    class Meta:
        model = Item
        fields = ["ref", "category"]

    name = CharFilter(field_name="name", lookup_expr="icontains")
    category = ChoiceFilter(
        field_name="category",
        label="Category",
        choices=[],
        empty_label="-- All categories --",
        method="cat_filter",
    )
    archive = ChoiceFilter(
        field_name="archive",
        empty_label=None,
        choices=(("", "Stock & Archive"), ("0", "Stock only"), ("1", "Archive only")),
    )
    state = ChoiceFilter(
        field_name="state", empty_label="-- All --", choices=Item.State.choices()
    )
    # purchased_after = DateFilter(
    #     field_name="lot__purchase__date",
    #     label="Purchased after",
    #     lookup_expr="gt",
    #     widget=DatePicker(options={"format": "DD/MM/YYYY"}),
    # )
    # image = ChoiceFilter(
    #     field_name="image",
    #     empty_label=None,
    #     choices=(
    #         (0, "No filter"),
    #         (1, "With an image"),
    #         (2, "Without an image"),
    #     ),
    #     method="image_filter",
    # )
    # search = CharFilter(method="search_filter", label="Search")
    # # per_page = PaginationFilter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # dynamically create the choices now
        self.filters["category"].extra["choices"] = [
            (0, "-- No category --"),
        ] + Category.objects.leaf_choices()

    @staticmethod
    def search_filter(queryset, name, value):
        # https://django.cowhite.com/blog/mastering-search-in-django-postgres/
        if not value:
            return queryset
        return queryset.annotate(
            search=SearchVector("name", "ref"),
        ).filter(search=value)

    @staticmethod
    def cat_filter(queryset, name, value):
        if not value:
            return queryset
        elif value == "0":
            return queryset.filter(category__isnull=True)
        return queryset.filter(category_id=value)

    @staticmethod
    def image_filter(queryset, name, value):
        if value == "0":
            return queryset
        elif value == "1":
            return queryset.filter(image__isnull=False)
        return queryset.filter(image__isnull=True)


class CompilerFilter(FilterSet):
    compiler = ModelChoiceFilter(
        queryset=Compiler.objects.order_by("name"), empty_label="All compilers"
    )


class ContactFilter(FilterSet):
    class Meta:
        model = Contact
        fields = ["first_name"]

    first_name = CharFilter(lookup_expr="icontains")
    company = CharFilter(lookup_expr="icontains")
    vendor = BooleanFilter()
    restorer = BooleanFilter()
    buyer = BooleanFilter()


# noinspection PyUnusedLocal
class EnquiryFilter(FilterSet):
    state = ChoiceFilter(
        field_name="closed",
        choices=((0, "Open enquiries"), (1, "Closed enquiries"), (2, "All enquiries")),
        empty_label=None,
        method="state_filter",
        label="State",
    )
    subject = CharFilter(lookup_expr="icontains")
    subject2 = CharFilter(field_name="subject", lookup_expr="icontains", exclude=True)
    message = CharFilter(lookup_expr="icontains")
    message2 = CharFilter(field_name="message", lookup_expr="icontains", exclude=True)

    @staticmethod
    def state_filter(queryset, name, value):
        if value == "0":
            return queryset.filter(closed=False)
        elif value == "1":
            return queryset.filter(closed=True)
        return queryset


class InvoiceFilter(FilterSet):
    number = CharFilter()


class PurchaseFilter(FilterSet):
    from_date = DateFilter(
        field_name="date",
        label="Date from",
        lookup_expr="gte",
        widget=DatePicker(options={"format": "DD/MM/YYYY"}),
    )
    to_date = DateFilter(
        field_name="date",
        label="Date to",
        lookup_expr="lte",
        widget=DatePicker(options={"format": "DD/MM/YYYY"}),
    )
