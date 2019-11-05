from django_filters import (
    Filter,
    FilterSet,
    CharFilter,
    ChoiceFilter,
    ModelChoiceFilter,
    DateFilter,
    BooleanFilter,
)
from shop.models import Item, Category, Compiler

PER_PAGE_CHOICES = (
    (10, "10 lines"),
    (15, "15 lines"),
    (20, "20 lines"),
    (50, "50 lines"),
    (100, "100 lines"),
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
    per_page = ChoiceFilter(
        field_name="id", label="Show", empty_label=None, choices=PER_PAGE_CHOICES
    )


class CompilerFilter(FilterSet):

    compiler = ModelChoiceFilter(
        queryset=Compiler.objects.order_by("name"), empty_label="All compilers"
    )


class ContactFilter(FilterSet):
    company = CharFilter(lookup_expr="icontains")


class InvoiceFilter(FilterSet):
    number = CharFilter()
