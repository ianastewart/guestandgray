from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter()
def breadcrumb(node_list):
    output = '<nav aria-label="breadcrumb"><ol class="breadcrumb">'
    for node in node_list:
        if node.active:
            output += f'<li class="breadcrumb-item active" aria-current="page">{node.name}</li>'
        else:
            output += f'<li class="breadcrumb-item"><a href="{node.get_absolute_url()}">{node.name}</a></li>'
    output += "</ol>"
    return mark_safe(output)
