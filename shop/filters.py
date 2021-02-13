from django_filters import (CharFilter, ChoiceFilter, DateFilter, FilterSet, ModelChoiceFilter)
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
    category = ModelChoiceFilter(
        queryset=Category.objects.filter(numchild=0).order_by("name"),
        required=None,
        label="Category",
        to_field_name="name",
        empty_label="No filter",
    )

    archive = ChoiceFilter(
        field_name="archive",
        empty_label=None,
        choices=(("", "Stock & Archive"), ("0", "Stock only"), ("1", "Archive only")),
    )
    per_page = PaginationFilter()
    # per_page = ChoiceFilter(
    #     field_name="id", label="Show", empty_label=None, choices=PER_PAGE_CHOICES
    # )


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
