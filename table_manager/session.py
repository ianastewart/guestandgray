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
