from urllib.parse import urlparse, parse_qs, quote


def _base_key(request):
    return request.resolver_match.view_name


def save_columns(request, column_list):
    key = f"columns:{_base_key(request)}"
    request.session[key] = list(column_list)


def load_columns(request, table_class):
    key = f"columns:{_base_key(request)}"
    if key in request.session:
        return request.session[key]
    if hasattr(table_class, "Meta") and hasattr(table_class.Meta, "default_columns"):
        columns = table_class.Meta.default_columns
    else:
        columns = table_class.sequence
    save_columns(request, columns)
    return columns


def set_column(request, table_class, column_name, checked):
    columns = load_columns(request, table_class)
    if checked:
        if column_name not in columns:
            columns.append(column_name)
    elif column_name in columns:
        columns.remove(column_name)
    save_columns(request, columns)

def visible_columns(request, table_class):
    """ return list of visible columns in correct sequence """
    sequence = table_class(data=[]).sequence
    columns = load_columns(request, table_class)
    return [col for col in sequence if col in columns]


def save_per_page(request, value):
    key = f"per_page:{_base_key(request)}"
    request.session[key] = value


def load_per_page(request):
    key = f"per_page:{_base_key(request)}"
    if key in request.session:
        return request.session[key]
    return 0


# def update_url(url, key, value):
#     """Add or replace 'key=value' in url"""
#     # todo handle multi value filter
#     query = urlparse(url).query
#     existing = ""
#     # if isinstance(value, str):
#     #     value = quote(value)
#     new_param = f"{key}={value}"
#     s = query.find(f"{key}=")
#     if s > -1:
#         e = query.index("&", s) if "&" in query[s:] else len(query)
#         existing = query[s:e]
#     if existing:
#         url = url.replace(existing, new_param)
#     elif "?" in url:
#         url = f"{url}&{new_param}"
#     else:
#         url = f"{url}?{new_param}"
#     return url
