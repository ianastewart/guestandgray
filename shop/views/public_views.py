import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from shop.models import Object, Category
from wagtail.core.models import Page
from django.http import Http404, HttpResponse

# Url structure from https://wellfire.co/learn/fast-and-beautiful-urls-with-django/


def get_redirected(queryset_or_class, lookups, validators):
    """
    Calls get_object_or_404 and conditionally builds redirect URL
    """
    obj = get_object_or_404(queryset_or_class, **lookups)
    for key, value in validators.items():
        if value != getattr(obj, key):
            return obj, obj.get_absolute_url()
    return obj, None


def home_view(request):
    return redirect("/pages/")


def object_view(request, slug, pk):
    """ Public view of a single object """

    template_name = "shop/public/object_detail.html"
    context = get_host_context("catalogue")
    obj, obj_url = get_redirected(Object, {"pk": pk}, {"slug": slug})
    if obj_url:
        return redirect(obj_url)
    context["object"] = obj
    context["price"] = int(obj.price / 100)
    context["images"] = obj.images.all()
    return render(request, template_name, context)


def category_view(request, pk):
    """ Public view of all objects in a category """

    template_name = "shop/public/category_grid.html"
    context = get_host_context("catalogue")
    category = get_object_or_404(Category, pk=pk)
    objects = category.object_set.filter(image__isnull=False).order_by("-price")
    paginator = Paginator(objects, 8)
    page = request.GET.get("page")
    if paginator.num_pages > 1 and not page:
        page = 1
    context["page_number"] = f"Page {page} of {paginator.num_pages}"
    context["category"] = category
    context["objects"] = paginator.get_page(page)
    return render(request, template_name, context)


def catalogue_view(request):
    """ Public view of all categories in a catalogue """

    template_name = "shop/public/catalogue_grid.html"
    context = get_host_context("catalogue")
    context["categories"] = Category.objects.all().exclude(image=None)
    return render(request, template_name, context)


def get_host_context(slug):
    """ Create context with wagtail host page in it. Raise 404 if slug not found """

    try:
        context = {}
        context["page"] = Page.objects.get(slug=slug, live=True)
        return context
    except Page.DoesNotExist:
        raise Http404
