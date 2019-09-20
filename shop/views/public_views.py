import logging
from itertools import chain

from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, InvalidPage, EmptyPage, PageNotAnInteger

from wagtail.core.models import Page
from wagtail.search.backends import db, get_search_backend
from wagtail.search.models import Query

from coderedcms.forms import SearchForm
from coderedcms.models import CoderedPage, get_page_models, GeneralSettings

from shop.models import Item, Category

logger = logging.getLogger(__name__)


# Url structure from https://wellfire.co/learn/fast-and-beautiful-urls-with-django/


def get_redirected(queryset_or_class, lookups, validators):
    """
    Calls get_object_or_404 and conditionally builds redirect URL
    """
    item = get_object_or_404(queryset_or_class, **lookups)
    for key, value in validators.items():
        if value != getattr(item, key):
            return item, item.get_absolute_url()
    return item, None


def home_view(request):
    return redirect("/pages/")


def item_view(request, slug, pk):
    """ Public view of a single object """

    template_name = "shop/public/item_detail.html"
    item, item_url = get_redirected(Item, {"pk": pk}, {"slug": slug})
    if item_url:
        return redirect(item_url)
    context = get_host_context("catalogue")
    category = get_object_or_404(Category, id=item.category_id)
    context["category"] = category
    context["breadcrumb"] = category.breadcrumb_nodes(item_view=True)
    context["item"] = item
    context["price"] = int(item.price / 100)
    context["images"] = item.images.all().exclude(id=item.image_id)
    return render(request, template_name, context)


def catalogue_view(request, slugs=None, archive=False):
    slug = "catalogue"
    if slugs:
        slug += "/" + slugs
    context = get_host_context("catalogue")
    category = get_object_or_404(Category, slug=slug)
    context["category"] = category
    context["archive"] = archive
    context["breadcrumb"] = category.breadcrumb_nodes()
    child_categories = category.get_children()
    if child_categories:
        # category has sub categories
        template_name = "shop/public/category_grid.html"
        context["categories"] = child_categories.exclude(image=None)
        for cat in context["categories"]:
            cat.count = cat.item_set.filter(
                image__isnull=False, archive=archive
            ).count()
    else:
        # category has objects
        template_name = "shop/public/item_grid.html"
        context["count"] = category.item_set.filter(
            image__isnull=False, archive=archive
        ).count()
        objects = category.item_set.filter(
            image__isnull=False, archive=archive
        ).order_by("-price")
        paginator = Paginator(objects, 32)
        page = request.GET.get("page")
        if paginator.num_pages >= 1 and not page:
            page = 1
        context["page_number"] = f"Page {page} of {paginator.num_pages}"
        context["items"] = paginator.get_page(page)

    return render(request, template_name, context)


def get_host_context(slug):
    """ Create context with wagtail host page in it. Raise 404 if slug not found """

    try:
        return {"page": Page.objects.get(slug=slug, live=True)}
    except Page.DoesNotExist:
        raise Http404


def search_view(request):
    """
    Searches pages across the entire site.
    Replaces the codered serach view
    """
    search_form = SearchForm(request.GET)
    pagetypes = []
    results = None
    results_paginated = None

    if search_form.is_valid():
        search_query = search_form.cleaned_data["s"]
        search_model = search_form.cleaned_data["t"]

        # get all codered models
        pagemodels = sorted(get_page_models(), key=lambda k: k.search_name)
        # get filterable models
        for model in pagemodels:
            if model.search_filterable:
                pagetypes.append(model)

        # get backend
        backend = get_search_backend()

        # DB search. Since this backend can't handle inheritance or scoring,
        # search specified page types in the desired order and chain the results together.
        # This provides better search results than simply searching limited fields on CoderedPage.
        db_models = []
        if backend.__class__ == db.SearchBackend:
            for model in get_page_models():
                if model.search_db_include:
                    db_models.append(model)
            db_models = sorted(db_models, reverse=True, key=lambda k: k.search_db_boost)

        if backend.__class__ == db.SearchBackend and db_models:
            for model in db_models:
                # if search_model is provided, only search on that model
                if (
                    not search_model
                    or search_model == ContentType.objects.get_for_model(model).model
                ):  # noqa
                    curr_results = model.objects.live().search(search_query)
                    if results:
                        results = list(chain(results, curr_results))
                    else:
                        results = curr_results

        # Fallback for any other search backend
        else:
            if search_model:
                try:
                    model = ContentType.objects.get(model=search_model).model_class()
                    results = model.objects.live().search(search_query)
                except search_model.DoesNotExist:
                    results = None
            else:
                # Custom code for shop
                results = backend.search(search_query, Item)

                # results = (
                #     CoderedPage.objects.live()
                #     .order_by("-last_published_at")
                #     .search(search_query)
                # )  # noqa

        # paginate results
        if results:
            paginator = Paginator(
                results, GeneralSettings.for_site(request.site).search_num_results
            )
            page = request.GET.get("p", 1)
            try:
                results_paginated = paginator.page(page)
            except PageNotAnInteger:
                results_paginated = paginator.page(1)
            except EmptyPage:
                results_paginated = paginator.page(1)
            except InvalidPage:
                results_paginated = paginator.page(1)

        # Log the query so Wagtail can suggest promoted results
        Query.get(search_query).add_hit()

    # Render template
    return render(
        request,
        "shop/public/search.html",
        {
            "request": request,
            "pagetypes": pagetypes,
            "form": search_form,
            "results": results,
            "results_paginated": results_paginated,
        },
    )
