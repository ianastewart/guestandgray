from django_filters import (
    CharFilter,
    ChoiceFilter,
    DateFilter,
    FilterSet,
    ModelChoiceFilter,
    BooleanFilter,
)
from tempus_dominus.widgets import DatePicker

from shop.models import Category, Compiler
from table_manager.filters import PaginationFilter

PER_PAGE_CHOICES = (
    (10, "10 rows"),
    (15, "15 rows"),
    (20, "20 rows"),
    (50, "50 rows"),
    (100, "100 rows"),
)


class ItemFilter(FilterSet):

    category = ChoiceFilter(
        field_name="category",
        label="Category",
        choices=[
            (0, "-- No category --"),
        ]
        + Category.objects.leaf_choices(),
        empty_label="-- All categories --",
        method="cat_filter",
    )
    archive = ChoiceFilter(
        field_name="archive",
        empty_label=None,
        choices=(("", "Stock & Archive"), ("0", "Stock only"), ("1", "Archive only")),
    )
    purchased_after = DateFilter(
        field_name="lot__purchase__date",
        label="Purchased after",
        lookup_expr="gt",
        widget=DatePicker(options={"format": "DD/MM/YYYY"}),
    )
    image = ChoiceFilter(
        field_name="image",
        empty_label=None,
        choices=(
            (
                0,
                "No filter",
            ),
            (1, "With an image"),
            (2, "Without an image"),
        ),
        method="image_filter",
    )
    per_page = PaginationFilter()

    def cat_filter(self, queryset, name, value):
        if not value:
            return queryset
        elif value == "0":
            return queryset.filter(category__isnull=True)
        return queryset.filter(category_id=value)

    def image_filter(self, queryset, name, value):
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
    first_name = CharFilter(lookup_expr="icontains")
    company = CharFilter(lookup_expr="icontains")
    address = CharFilter(lookup_expr="icontains")
    per_page = ChoiceFilter(
        field_name="id", label="Show", empty_label=None, choices=PER_PAGE_CHOICES
    )


class EnquiryFilter(FilterSet):
    state = ChoiceFilter(
        field_name="closed",
        choices=((0, "Open enquiries"), (1, "Closed enquiries"), (2, "All enquiries")),
        empty_label=None,
        method="state_filter",
        label="State",
    )

    def state_filter(self, queryset, name, value):
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
    per_page = ChoiceFilter(
        field_name="id", label="Show", empty_label=None, choices=PER_PAGE_CHOICES
    )
