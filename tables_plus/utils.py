from urllib.parse import urlparse, parse_qs

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
        columns = table_class.base_columns
    save_columns(request, columns)
    return columns


def toggle_column(request, column_name, table_class):
    columns = load_columns(request, table_class)
    columns.remove(column_name) if column_name in columns else columns.append(column_name)
    save_columns(request, columns)


def save_per_page(request, value):
    key = f"per_page:{_base_key(request)}"
    request.session[key] = value


def load_per_page(request):
    key = f"per_page:{_base_key(request)}"
    if key in request.session:
        return request.session[key]
    return 0


def update_url(url, value):
    parsed = urlparse(url)
    queries = parse_qs(parsed.query)
    existing = ""
    new_per_page = f"per_page={int(value)}"
    if "per_page" in queries:
        value = queries["per_page"]
        value = int(value[0]) if value else ""
        existing = f"per_page={value}"
    elif "per_page=" in url:
        # case where there is no value is not included in queries
        existing = "per_page="
    if existing:
        url = url.replace(existing, new_per_page)
    elif queries:
        url = f"{url}&{new_per_page}"
    else:
        url = f"{url}?{new_per_page}"
    return url


def per_page_value(path):
    parsed = urlparse(path)
    queries = parse_qs(parsed.query)
    if "per_page" in queries:
        return int(queries["per_page"][0])
    return 0
