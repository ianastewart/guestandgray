import json
import logging
import urllib
from datetime import datetime
from itertools import chain

from coderedcms.forms import SearchForm
from coderedcms.models import GeneralSettings, get_page_models
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage, get_connection, send_mail
from django.core.paginator import EmptyPage, InvalidPage, PageNotAnInteger, Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView
from wagtail.core.models import Page, Site
from wagtail.search.backends import get_search_backend
from wagtail.search.models import Query
from wagtailseo.utils import StructDataEncoder, get_struct_data_images

from shop.cat_tree import Counter
from shop.filters import CompilerFilter
from shop.forms import EnquiryForm
from shop.models import (
    Address,
    Book,
    Category,
    Compiler,
    Contact,
    CustomImage,
    Enquiry,
    HostPage,
    Item,
)
from shop.tables import BookTable
from shop.truncater import truncate
from shop.views.legacy_views import legacy_view

logger = logging.getLogger(__name__)


def home_view(request):
    if "page_id" in request.GET:
        return legacy_view(request, request.GET["page_id"])
    return redirect("/pages/")


def item_view(request, ref, slug):
    """ Public view of a single object """
    template_name = "shop/public/item_detail.html"
    # item = get_object_or_404(Item, ref=ref)
    item = Item.objects.filter(ref=ref).first()
    if not item:
        raise Http404
    if not slug and item.slug:
        return redirect("public_item", ref=ref, slug=item.slug)
    if not item.description:
        item.description = "No description available"
    context = add_page_context(
        request,
        context={},
        path=request.path,
        title=item.name,
        description=truncate(item.description, 200),
    )
    page = context["page"]
    page.og_image = item.image if item.image else None
    if item.category_id:
        category = get_object_or_404(Category, id=item.category_id)
        context["breadcrumb"] = category.breadcrumb_nodes(item_view=True)
        context["category"] = category
        page.title = f"{category.seo_prefix()} {item.ref}"
    context["item"] = item
    # context["price"] = int(item.sale_price)
    images = []
    extra_images = CustomImage.objects.filter(item_id=item.id, show=True).order_by(
        "position", "title"
    )
    if item.image and len(extra_images) > 1:
        images.append(item.image)
    for image in extra_images:
        if item.image:
            if image.id != item.image.id:
                images.append(image)
        else:
            #  missing image case
            item.image = image
            item.save()
            images.append(image)
    context["images"] = images
    # Structured data
    if item.category_id:
        sd_dict = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "category": category.name,
            "name": item.name,
            "description": item.description,
        }
        if item.image:
            sd_dict["image"] = get_struct_data_images(
                site=Site.find_for_request(request), image=item.image
            )
        page.structured_data = json.dumps(sd_dict, cls=StructDataEncoder)
    form = EnquiryForm()
    form.fields["subject"].initial = f"Enquiry about {item.ref}"
    context["form"] = form
    return render(request, template_name, context)


def catalogue_view(request, slugs=None, archive=False):
    slug = "catalogue"
    if slugs:
        slug += "/" + slugs

    category = get_object_or_404(Category, slug=slug)
    context = add_page_context(
        request,
        context={},
        path=request.path,
        title=category.name,
        description=category.seo_description
        if category.seo_description
        else truncate(category.description, 70),
    )
    page = context["page"]
    prefix = "Archive of" if archive else "Catalogue of"
    page.title = f"{prefix} {category.seo_prefix()}"
    page.og_image = category.image if category.image else None
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
        objects = category.archive_items() if archive else category.shop_items()
        context["count"] = objects.count()
        paginator = Paginator(objects, 36)
        page_no = request.GET.get("page", 1)
        try:
            page_no = int(page_no)
        except ValueError:
            raise Http404
        if page_no > paginator.num_pages:
            page_no = paginator.num_pages
        context["page_number"] = f"Page {page_no} of {paginator.num_pages}"
        # Canonical for the first page never has a page query string'
        if paginator.num_pages >= 1 and int(page_no) > 1:
            page.canonical_url = page.seo_canonical_url + f"?page={page_no}"
            context["breadcrumb"][-1].page_number = f" Page {page_no}"
        context["items"] = paginator.get_page(page_no)

    return render(request, template_name, context)


def add_page_context(request, context, path, title="", description=""):
    """ add wagtail host page to context. Raise 404 if slug not found """
    if not title:
        title = "Guest and Gray"
    if not description:
        description = ""
    try:
        page = HostPage.objects.filter(live=True).first()
    except HostPage.DoesNotExist:
        raise Http404
    # page.cover_image = None
    page.path = path
    page.title = title
    page.search_description = description
    context["page"] = page
    context["self"] = page
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

        # Custom search code
        items_1 = Item.objects.filter(image__isnull=False, archive=False)
        items_3 = Item.objects.filter(image__isnull=False, archive=True)
        items_2 = Item.objects.filter(image__isnull=True, archive=False)
        items_4 = Item.objects.filter(image__isnull=True, archive=True)
        results_1 = backend.search(search_query, items_1)
        results_2 = backend.search(search_query, items_2)
        results_3 = backend.search(search_query, items_3)
        results_4 = backend.search(search_query, items_4)
        results_page = backend.search(search_query, Page)
        results = list(chain(results_1, results_2, results_3, results_4, results_page))
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


class EnquiryView(FormView):
    """
    Handles mailing list form in footer, enquiry on an item and general contact page
    """

    form_class = EnquiryForm
    template_name = "shop/public/contact_form.html"
    success_url = reverse_lazy("public_contact_submitted")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["captcha_site"] = settings.GOOGLE_RECAPTCHA_SITE_KEY
        return add_page_context(
            self.request,
            context,
            path=self.request.path,
            title="Enquiry",
            description="Enquiry form",
        )

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        recaptcha_response = self.request.POST.get("g-recaptcha-response")
        url = "https://www.google.com/recaptcha/api/siteverify"
        values = {
            "secret": settings.GOOGLE_RECAPTCHA_SECRET_KEY,
            "response": recaptcha_response,
        }
        data = urllib.parse.urlencode(values).encode()
        req = urllib.request.Request(url, data=data)
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        if not result["success"]:
            messages.error(self.request, "Invalid reCAPTCHA. Please try again.")
            return self.form_invalid(form)
        # Recaptcha is valid
        d = form.cleaned_data
        item = None
        mail_list = True if d["ref"] == "mail_list" else False
        if not mail_list and "ref" in self.request.POST:
            item = Item.objects.filter(ref=self.request.POST["ref"]).first()
        contact = Contact.objects.filter(
            main_address__email=form.cleaned_data["email"]
        ).first()
        if not "phone" in d.keys():
            d["phone"] = ""
        if contact and d["phone"]:
            if not (
                contact.main_address.work_phone == d["phone"]
                or contact.main_address.mobile_phone == d["phone"]
            ):
                contact = None
        if not contact:
            contact = Contact.objects.create(
                first_name=d["first_name"],
                last_name=d["last_name"],
            )
            address = Address.objects.create(
                mobile_phone=d["phone"], email=d["email"], contact=contact
            )
            contact.main_address = address
        if d["mail_consent"]:
            contact.mail_consent = True
            contact.consent_date = datetime.now().date()
        contact.save()
        enquiry = Enquiry.objects.create(
            subject=d["subject"], message=d["message"], contact=contact, item=item
        )
        # Inform staff
        send_mail(
            d["subject"],
            d["message"],
            d["email"],
            [settings.INFORM_EMAIL],
            fail_silently=False,
        )
        connection = get_connection(
            fail_silently=False,
        )
        email = EmailMessage(
            subject=d["subject"],
            body=d["message"],
            from_email=d["email"],
            to=[settings.INFORM_EMAIL],
            reply_to=[d["email"]],
            connection=connection,
        )
        email.send(fail_silently=False)

        message = (
            "You have been added to our mail list."
            if mail_list
            else "Thank you for your enquiry. We will respond as soon as possible."
        )
        # Confirm to customer
        send_mail(
            "Confirmation from chinese-porcelain-art.com",
            message,
            settings.DEFAULT_FROM_EMAIL,
            [contact.main_address.email],
            fail_silently=False,
        )
        context = {
            "enquiry": enquiry,
            "email": (
                enquiry.contact.address_set.filter(email__isnull=False).first().email
            ),
        }
        return render(self.request, "shop/public/contact_submitted.html", context)


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
        context = add_page_context(
            self.request,
            context,
            path=self.request.path,
            title="Bibliography",
            description="Recommended books",
        )
        page = context["page"]
        page.title = "Guest and Gray Bibliography"
        page.seo_title = page.title
        page.search_description = "List of reference books on antique Chinese porcelain"
        page.og_image = None
        return context
