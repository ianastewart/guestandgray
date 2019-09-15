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


@register.simple_tag(takes_context=True)
def shop_is_active_page(context, curr_page, other_page):
    # special handling for catalogue menu item, because it is a link, not a page
    if (
        hasattr(curr_page, "slug")
        and curr_page.slug == "catalogue"
        and other_page == ""
    ):
        return True
    if hasattr(curr_page, "get_url") and hasattr(other_page, "get_url"):
        curr_url = curr_page.get_url(context["request"])
        other_url = other_page.get_url(context["request"])
        return curr_url == other_url
    return False
