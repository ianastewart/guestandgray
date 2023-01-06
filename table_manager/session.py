from django.utils.timezone import now
from django.shortcuts import redirect
from decimal import Decimal

# Stack handling for ajax calls

STACK_DEBUG = True


def new_stack(request):
    request.session["stack"] = []
    request.session.modified = True
    if STACK_DEBUG:
        debug_stack(request)


def push(request, url, is_ajax):
    stack = request.session.get("stack", None)
    entry = (url, is_ajax)
    if stack is None:
        stack = []
    if STACK_DEBUG:
        print("Stack push:", entry)
    stack.append(entry)
    request.session["stack"] = stack
    request.session.modified = True
    if STACK_DEBUG:
        debug_stack(request)


def pop(request):
    try:
        value = request.session["stack"].pop()
        request.session.modified = True
    except IndexError:
        raise IndexError("when popping stack")
        value = None
    if STACK_DEBUG:
        print("Stack popped:", value)
        debug_stack(request)
    return value[0], value[1]


def debug_stack(request):
    stack = request.session.get("stack")
    if stack is None:
        print("No Stack")
    else:
        print("Stack:")
        for entry in stack:
            print(entry)


def save_columns(request, column_list):
    key = f"columns:{request.user.username}:{request.resolver_match.view_name}"
    request.session[key] = list(column_list)


def load_columns(request):
    key = f"columns:{request.user.username}:{request.resolver_match.view_name}"
    if key in request.session:
        return request.session[key]
    return []


def toggle_column(request, column_name):
    columns = load_columns(request)
    columns.remove(column_name) if column_name in columns else columns.append(column_name)
    save_columns(request, columns)
