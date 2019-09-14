from django_filters import (
    Filter,
    FilterSet,
    CharFilter,
    ChoiceFilter,
    ModelChoiceFilter,
    DateFilter,
    BooleanFilter,
)
from shop.models import Item, Category

PER_PAGE_CHOICES = (
    (10, "10"),
    (15, "15"),
    (20, "20"),
    (50, "50"),
    (100, "100"),
    (500, "500"),
    (100000, "All"),
)


class ItemFilter(FilterSet):

    category = ModelChoiceFilter(
        queryset=Category.objects.filter(numchild=0).order_by("name"),
        required=None,
        label="Category",
        to_field_name="name",
        empty_label="No filter",
    )
    per_page = ChoiceFilter(
        field_name="id",
        label="Lines per page",
        empty_label=None,
        choices=PER_PAGE_CHOICES,
    )
