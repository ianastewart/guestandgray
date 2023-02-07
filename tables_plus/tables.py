import itertools
import django_tables2 as tables
from django.contrib.humanize.templatetags.humanize import intcomma
from tables_plus.utils import load_columns, save_columns


class Table(tables.Table):
    pass
    # def before_render(self, request):
    #     columns = load_columns(request, self)
    #     if not columns:
    #         if hasattr(self.Meta, "default_columns"):
    #             columns = self.Meta.default_columns
    #         else:
    #             columns = self.base_columns
    #         save_columns(request, columns)
    #     for k, v in self.base_columns.items():
    #         if v.verbose_name:
    #             self.columns.show(k) if k in columns else self.columns.hide(k)
    #
    # def get_excluded_columns(self):
    #     excluded = []
    #     for k, v in self.columns.columns.items():
    #         if not v.visible:
    #             excluded.append(k)
    #     return excluded


class RightAlignedColumn(tables.Column):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not "th" in self.attrs:
            self.attrs["th"] = {}
        if not "td" in self.attrs:
            self.attrs["td"] = {}
        self.attrs["th"]["style"] = "text-align: center;"
        self.attrs["td"]["style"] = "text-align: right;"


class CenteredColumn(tables.Column):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not "th" in self.attrs:
            self.attrs["th"] = {}
        if not "td" in self.attrs:
            self.attrs["td"] = {}
        self.attrs["th"]["style"] = "text-align: center;"
        self.attrs["td"]["style"] = "text-align: center;"


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
    def __init__(self, **kwargs):
        self.integer = kwargs.pop("integer", None)
        self.prefix = kwargs.pop("prefix", "")
        self.suffix = kwargs.pop("suffix", "")
        super().__init__(**kwargs)

    def render(self, value):
        if self.integer:
            value = int(value)
        return f"{self.prefix} {intcomma(value)} {self.suffix}"


class CheckBoxColumn(tables.TemplateColumn):
    def __init__(self, **kwargs):
        kwargs["template_name"] = "tables_plus/custom_checkbox.html"
        super().__init__(**kwargs)


class SelectionColumn(tables.TemplateColumn):
    def __init__(self, **kwargs):
        kwargs["template_name"] = "tables_plus/select_checkbox.html"
        kwargs["verbose_name"] = ""
        kwargs["accessor"] = "id"
        kwargs["orderable"] = False
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
