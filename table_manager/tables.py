import itertools
import django_tables2 as tables
from django.contrib.humanize.templatetags.humanize import intcomma
from table_manager.session import load_columns, save_columns


class Table(tables.Table):
    def before_render(self, request):
        columns = load_columns(request, self)
        if not columns:
            if hasattr(self.Meta, "default_columns"):
                columns = self.Meta.default_columns
            else:
                columns = self.base_columns
            save_columns(request, columns)
        for k, v in self.base_columns.items():
            if v.verbose_name:
                self.columns.show(k) if k in columns else self.columns.hide(k)


class RightAlignedColumn(tables.Column):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.attrs = {"th": {"style": "text-align: right;"}, "td": {"align": "right"}}


class CenteredColumn(tables.Column):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.attrs = {"th": {"style": "text-align: center;"}, "td": {"align": "center"}}


class CenteredTrueColumn(CenteredColumn):
    def render(self, value):
        if value:
            return "\u2705"
        return ""


class CenteredTrueFalseColumn(CenteredColumn):
    def render(self, value):
        if value:
            return "\u2705"
        return "\u274c"


class CurrencyColumn(RightAlignedColumn):
    integer = False

    def __init__(self, **kwargs):
        self.integer = kwargs.pop("integer", None)
        super().__init__(**kwargs)

    def render(self, value):
        if self.integer:
            value=int(value)
        return "£ " + intcomma(value)


class CheckBoxColumn(tables.TemplateColumn):
    def __init__(self, **kwargs):
        kwargs["template_name"] = "table_manager/custom_checkbox.html"
        super().__init__(**kwargs)


class SelectionColumn(CheckBoxColumn):
    def __init__(self, **kwargs):
        kwargs["verbose_name"] = ""
        kwargs["accessor"] = "id"
        super().__init__(**kwargs)


class CounterColumn(tables.Column):
    row_counter = None

    def __init__(self, **kwargs):
        kwargs["orderable"] = False
        kwargs["empty_values"] = ()
        kwargs["verbose_name"] = ""
        super().__init__(**kwargs)

    def render(self, value):
        if not self.row_counter:
            self.row_counter = itertools.count()
        return next(self.row_counter) + 1
