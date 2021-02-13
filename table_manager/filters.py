from django_filters import ChoiceFilter

ROW_CHOICES = (
    (10, "10 rows"),
    (15, "15 rows"),
    (20, "20 rows"),
    (50, "50 rows"),
    (100, "100 rows"),
)

class PaginationFilter(ChoiceFilter):

    def __init__(self, *args, **kwargs):
        kwargs['field_name'] = "id"
        kwargs['empty_label']= None
        kwargs['choices'] = ROW_CHOICES
        super().__init__(*args, **kwargs)