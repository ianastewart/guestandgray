from django_filters import (
    Filter,
    FilterSet,
    CharFilter,
    ChoiceFilter,
    ModelChoiceFilter,
    DateFilter,
    BooleanFilter,
)
from shop.models import Item, Category, Book

PER_PAGE_CHOICES = ((10, "10"), (15, "15"), (20, "20"), (50, "50"), (100, "100"))


class ItemFilter(FilterSet):

    category = ModelChoiceFilter(
        queryset=Category.objects.filter(numchild=0).order_by("name"),
        required=None,
        label="Category",
        to_field_name="name",
        empty_label="No filter",
    )
    archive = BooleanFilter(field_name="archive")

    archive = ChoiceFilter(
        field_name="archive",
        empty_label=None,
        choices=(("", "Stock & Archive"), ("0", "Stock only"), ("1", "Archive only")),
    )
    per_page = ChoiceFilter(
        field_name="id",
        label="Lines per page",
        empty_label=None,
        choices=PER_PAGE_CHOICES,
    )


# def compilers():
#     return [
#         (c, c)
#         for c in Book.objects.values_list("compiler", flat=True)
#         .order_by("compiler")
#         .distinct()
#     ]


class BookCompilerFilter(FilterSet):
    pass
    # compiler = ChoiceFilter(
    #     choices=compilers(),
    #     label="Compiler",
    #     field_name="compiler",
    #     empty_label="All compilers",
    # )
