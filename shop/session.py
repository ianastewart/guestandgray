from django.shortcuts import redirect

# During the application process we store data posted from each of the forms
# in session variables

from datetime import datetime


def clear_data(request):
    """ Clear session variables """
    request.session["posts"] = []


def update_data(index, request, form):
    """
    Save cleaned data in session at index
    """
    posts = request.session["posts"]
    cleaned_data = form.cleaned_data
    cleaned_data["path"] = request.path
    cleaned_data["form_class"] = form.__class__.__name__
    if index >= len(posts):
        posts.append(cleaned_data)
    else:
        # Don't override the orignal path if doing an ajax update
        cleaned_data["path"] = posts[index]["path"]
        posts[index] = cleaned_data
    request.session["posts"] = posts


def get_data(index, request):
    """
    Return cleaned_data for index else None
    """
    posts = request.session.get("posts", None)
    if posts:
        if index >= 0 and index < len(posts):
            if not (
                posts[index].get("invalid", False) or posts[index].get("deleted", False)
            ):
                return posts[index]
    return None


def delete_data(index, request):
    """
    Delete post data for index
    """
    posts = request.session["posts"]
    if index < len(posts):
        posts[index]["deleted"] = True
        index += 1
        request.session.modified = True


def invalidate_data(index, request):
    """
    Invalidate post data for index
    Used when child profile is changed to adult profile or vice versa
    """
    posts = request.session["posts"]
    if index < len(posts):
        posts[index]["invalid"] = True
        request.session.modified = True


def last_index(request):
    """
    return the last used index
    """
    return len(request.session["posts"]) - 1


def next_index(index, request):
    """
    Return next index, skipping deleted records, but not invalid records because we overwrite those
    """
    posts = request.session["posts"]
    i = index
    while i + 1 < len(posts):
        i += 1
        if not posts[i].get("deleted", False):
            return i
    return len(posts)


def back(index, request):
    """
    Return previous path, skipping deleted and invalid records
    """
    posts = request.session["posts"]
    while index > 0:
        index -= 1
        if is_valid(posts[index]):
            return posts[index]["path"]
    return posts[0]["path"]


def is_valid(data):
    return (
        None
        if not data
        else not (data.get("deleted", False) or data.get("invalid", False))
    )


def update_kwargs(view, kwargs):
    """
    Update the forms kwargs with stored POST data if it exists
    """
    data = post_data(view)
    if data:
        kwargs.update({"data": data})
    return kwargs


def post_data(view):
    """ Return POST data if it exists for a view"""
    if view.request.method == "GET":
        return get_data(view.index, view.request)
    return None


def redirect_next(index, request, default):
    """ Redirect to next page form if data exists for it else to the default """
    posts = request.session["posts"]
    max_index = len(posts) - 1
    i = index
    while i < max_index:
        i += 1
        if is_valid(posts[i]):
            return redirect(posts[i]["path"])
    return redirect(default, i + 1)


# Stack handling for ajax calls


def new_stack(request):
    request.session["stack"] = []
    request.session.modified = True


def push(request, url):
    stack = request.session.get("stack", None)
    if stack is None:
        stack = []
    stack.append(url)
    request.session["stack"] = stack
    request.session.modified = True


def pop(request):
    try:
        value = request.session["stack"].pop()
        request.session.modified = True
    except IndexError:
        value = None
    return value
