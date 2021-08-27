from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import title
from shop.session import cart_items
from shop.cat_tree import tree
from django.contrib import humanize

register = template.Library()


@register.simple_tag(takes_context=False)
def breadcrumb(node_list, archive=False):
    output = '<nav aria-label="breadcrumb"><ol class="breadcrumb my-0">'
    for node in node_list:
        name = (
            node.name + node.page_number if hasattr(node, "page_number") else node.name
        )
        if node.active:
            output += (
                f'<li class="breadcrumb-item active" aria-current="page">{name}</li>'
            )
        else:
            url = node.get_archive_url() if archive else node.get_absolute_url()
            output += f'<li class="breadcrumb-item"><a href="{url}">{name}</a></li>'
    output += "</ol>"
    if archive:
        output = output.replace("Catalogue", "Archive")
    return mark_safe(output)


@register.simple_tag(takes_context=True)
def shop_is_active_page(context, page, link):
    # special handling for catalogue and archive menu items, because they are a link, not a page
    # returns True if on catalogue or archive page
    current_url = context["request"].path
    if page:
        return current_url == page.get_url(context["request"])
    return link in current_url


@register.simple_tag(takes_context=False)
def is_catalogue_menu(value):
    if "link" in value:
        return value["link"] in ["/catalogue"]
    return False


@register.simple_tag(takes_context=False)
def is_archive_menu(value):
    if "link" in value:
        return value["link"] in ["/archive"]
    return False


@register.simple_tag(takes_context=False)
def catalogue_tree(root):
    return tree(root=root, archive=False)


@register.simple_tag(takes_context=False)
def archive_tree(root):
    return tree(root=root, archive=True)


@register.simple_tag(takes_context=False)
def checkbox(box):
    checked = "checked" if box.initial else ""
    output = f'<div class="custom-control custom-checkbox">\
    <input type="checkbox" class="custom-control-input" id="{box.auto_id}" name="{box.html_name}" {checked}>\
    <label class="custom-control-label" for="{box.auto_id}">{box.label}</label></div>'
    return mark_safe(output)


@register.filter(name="titler")
def titler(value):
    text = title(value)
    for t in [" A ", " An ", " And ", " With ", " In ", " On ", " The ", " Of "]:
        if t in text:
            text = text.replace(t, t.lower())
    return mark_safe(text)


@register.filter(name="currency")
def currency(value):
    return f"£ {value}"


@register.simple_tag(takes_context=False)
def currency_input(
    field,
    label="",
    layout="",
    disabled=False,
    label_class="col-md-6",
    field_class="col-md-6",
):
    if not label:
        label = field.label
    invalid = ""
    feedback = ""
    val = field.initial if field.initial else ""
    readonly = ""
    if "readonly" in field.subwidgets[0].parent_widget.attrs:
        readonly = "readonly"
    dis = "disabled" if disabled else ""
    if field.errors:
        invalid = "is-invalid"
        feedback = f'<div class="invalid-feedback">{field.errors[0]}</div>'
    if layout == "horizontal":
        output = f'\
        <div class="form-group row">\
        <label class="col-md-6 col-form-label" for="{field.auto_id}">{label}</label>\
        <div class="col-md-6">\
        <div class="input-group">\
        <div class="input-group-prepend">\
        <span class="input-group-text">£</span>\
        </div>\
        <input type="number" name="{field.html_name}" value="{val}" step="0.01" class="form-control {invalid} text-right" id="{field.auto_id}" title {dis} {readonly}>\
        {feedback}\
        </div></div></div>'
    else:
        output = f'\
        <div class="form-group">\
        <label class="col-form-label" for="id_{field.auto_id}">{label}</label>\
        <div class="input-group">\
        <div class="input-group-prepend"> <span class="input-group-text">£</span></div>\
        <input type="number" name="{field.html_name}" value="{val}" step="0.01" class="form-control {invalid} text-right" id="{field.auto_id} title {dis}">\
        {feedback}\
        </div></div>'
    return mark_safe(output.replace("        ", ""))


@register.simple_tag(takes_context=True)
def cart_count(context):
    request = context["request"]
    if cart_items(request):
        output = f'<span class ="cart-badge">{len(cart_items(request))}</span>'
        return mark_safe(output)
    return ""


@register.filter(name="integer")
def integer(value):
    return int(value)
