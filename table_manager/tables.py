import django_tables2 as tables
from django.contrib.humanize.templatetags.humanize import intcomma


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
    def render(self, value):
        return "£" + intcomma(value)
