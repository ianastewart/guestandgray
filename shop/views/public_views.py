import logging
from itertools import chain

from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, InvalidPage, EmptyPage, PageNotAnInteger
from django.views.generic import FormView, TemplateView, ListView
from django.urls import reverse_lazy

from wagtail.core.models import Page
from wagtail.search.backends import db, get_search_backend
from wagtail.search.models import Query

from coderedcms.forms import SearchForm
from coderedcms.models import CoderedPage, get_page_models, GeneralSettings

from shop.models import Item, Category, Contact, Enquiry, Book, Compiler
from shop.forms import EnquiryForm
from shop.tables import BookTable
from shop.filters import CompilerFilter
from shop.cat_tree import Counter

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
    if item.category_id:
        category = get_object_or_404(Category, id=item.category_id)
        context["breadcrumb"] = category.breadcrumb_nodes(item_view=True)
        context["category"] = category
    context["item"] = item
    # context["price"] = int(item.sale_price)
    images = [item.image]
    ims = item.images.filter(show=True).exclude(id=item.image_id)
    if len(ims) > 1:
        for im in ims:
            images.append(im)
    context["images"] = images
    if len(context["images"]) == 1:
        context["images"] == None
    form = EnquiryForm()
    form.fields["subject"].initial = f"{item.name} ({item.ref})"
    context["form"] = form
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
    child_categories = category.get_children().filter(hidden=False)
    if child_categories:
        # category has sub categories
        template_name = "shop/public/category_grid.html"
        counter = Counter(category, archive)
        counter.count()
        # need to reload after the count
        context["categories"] = category.get_children().filter(
            hidden=False, count__gt=0
        )
    else:
        # category has objects
        template_name = "shop/public/item_grid.html"
        objects = category.item_set.filter(
            image__isnull=False, archive=archive, visible=True
        ).order_by("featured", "rank", "-sale_price")
        context["count"] = objects.count()
        paginator = Paginator(objects, 32)
        page = request.GET.get("page")
        if paginator.num_pages >= 1 and not page:
            page = 1
        context["page_number"] = f"Page {page} of {paginator.num_pages}"
        context["items"] = paginator.get_page(page)

    return render(request, template_name, context)


def get_host_context(slug):
    """ Create context with wagtail host page in it. Raise 404 if slug not found """
    context = {}
    return add_page_context(context, slug)


def add_page_context(context, slug):
    """ add wagtail host page to context. Raise 404 if slug not found """
    try:
        page = Page.objects.get(slug=slug, live=True)
    except Page.DoesNotExist:
        raise Http404
    context["page"] = page
    return context


def search_view(request, public):
    """
    Searches pages across the entire site.
    Replaces the codered search view
    Also used for staff search if public=False
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

        # paginate results
        if results:
            paginator = Paginator(
                results, GeneralSettings.for_request(request).search_num_results
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
    template = "shop/public/search.html" if public else "shop/search.html"

    return render(
        request,
        template,
        {
            "request": request,
            "pagetypes": pagetypes,
            "form": search_form,
            "results": results,
            "results_paginated": results_paginated,
        },
    )


class ContactView(FormView):
    form_class = EnquiryForm
    template_name = "shop/public/contact_form.html"
    success_url = reverse_lazy("public_contact_submitted")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return add_page_context(context, "contact")

    def form_valid(self, form):

        contacts = Contact.objects.filter(email=form.cleaned_data["email"])
        count = len(contacts)
        if count == 0:
            contact = form.save()
        else:
            contact = contacts[0]
        enquiry = Enquiry.objects.create(
            subject=form.cleaned_data["subject"],
            message=form.cleaned_data["message"],
            contact=contact,
        )
        self.request.session["enquiry_pk"] = enquiry.pk
        return redirect(self.success_url)


class ContactSubmittedView(TemplateView):
    template_name = "shop/public/contact_submitted.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["enquiry"] = Enquiry.objects.get(pk=self.request.session["enquiry_pk"])
        return context


class BibliographyView(ListView):
    model = Book
    template_name = "shop/public/book_list.html"
    table_class = BookTable
    filter_class = CompilerFilter
    table_pagination = {"per_page": 100}

    def get_queryset(self):
        return Book.objects.all().order_by("title").select_related("compiler")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading"] = "Bibiliography"
        context["filter"] = CompilerFilter(
            self.request.GET, queryset=self.get_queryset()
        )
        context["compilers"] = Compiler.objects.order_by("name")
        context = add_page_context(context, "bibliography")
        return context
