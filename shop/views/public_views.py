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
    context["images"] = item.images.all().exclude(id=item.image_id)
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
    child_categories = category.get_children()
    if child_categories:
        # category has sub categories
        template_name = "shop/public/category_grid.html"
        context["categories"] = child_categories #.exclude(image=None)
        counter = Counter(category, archive)
        counter.count()
    else:
        # category has objects
        template_name = "shop/public/item_grid.html"
        objects = category.item_set.filter(
            image__isnull=False, archive=archive, visible=True
        ).order_by("featured", "-price")
        context["count"] = objects.count()
        paginator = Paginator(objects, 32)
        page = request.GET.get("page")
        if paginator.num_pages >= 1 and not page:
            page = 1
        context["page_number"] = f"Page {page} of {paginator.num_pages}"
        context["items"] = paginator.get_page(page)

    return render(request, template_name, context)


class Counter:
    """ Traverse a hierarchical category tree and append the total count of items under each node """

    def __init__(
        self, root, archive=False, exclude_no_image=True, exclude_not_visible=True
    ):
        self.total = 0
        self.root = root
        self.archive = archive
        self.no_image = exclude_no_image
        self.not_visible = exclude_not_visible

    def count(self):
        return self._count(self.root)

    def _count(self, cat):
        # recursive count function
        print(f"Start {cat.name}")
        items = cat.item_set.filter(archive=self.archive)
        if self.no_image:
            items = items.filter(image__isnull=False)
        if self.not_visible:
            items = items.filter(visible=True)
        total = items.count()
        child_cats = cat.get_children()
        # if self.no_image:
        #     child_cats = child_cats.filter(image__isnull=False)
        # if self.not_visible:
        #     child_cats = child_cats.filter(visible=True)
        if child_cats:
            for cat1 in child_cats:
                total += self._count(cat1)
        cat.count = total
        cat.save()
        print(f"{cat.name} {cat.count}")
        return total


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
