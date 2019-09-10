import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from shop.models import Object, Category, OldCategory
from wagtail.core.models import Page
from django.http import Http404, HttpResponse

logger = logging.getLogger(__name__)

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

    template_name = "shop/public/object_detail1.html"
    obj, obj_url = get_redirected(Object, {"pk": pk}, {"slug": slug})
    if obj_url:
        return redirect(obj_url)
    context = get_host_context("catalogue")
    category = get_object_or_404(Category, id=obj.new_category_id)
    context["category"] = category
    context["breadcrumb"] = category.breadcrumb_nodes(object_view=True)
    context["object"] = obj
    context["price"] = int(obj.price / 100)
    context["images"] = obj.images.all().exclude(id=obj.image_id)
    return render(request, template_name, context)


def catalogue_view(request, slugs=None):
    slug = "catalogue"
    if slugs:
        slug += "/" + slugs
    context = get_host_context("catalogue")
    category = get_object_or_404(Category, slug=slug)
    context["category"] = category
    context["breadcrumb"] = category.breadcrumb_nodes()
    child_categories = category.get_children()
    if child_categories:
        # category has sub categories
        template_name = "shop/public/category_grid.html"
        context["categories"] = child_categories.exclude(image=None)
    else:
        # category has objects
        template_name = "shop/public/object_grid.html"
        objects = category.object_set.filter(image__isnull=False).order_by("-price")
        paginator = Paginator(objects, 16)
        page = request.GET.get("page")
        if paginator.num_pages > 1 and not page:
            page = 1
        context["page_number"] = f"Page {page} of {paginator.num_pages}"
        context["objects"] = paginator.get_page(page)
    return render(request, template_name, context)


def get_host_context(slug):
    """ Create context with wagtail host page in it. Raise 404 if slug not found """

    try:
        return {"page": Page.objects.get(slug=slug, live=True)}
    except Page.DoesNotExist:
        raise Http404
