import json
import logging
from datetime import datetime
from itertools import chain

import requests
from coderedcms.forms import SearchForm
from coderedcms.models import LayoutSettings
from django.conf import settings
from django.core.mail import EmailMessage, get_connection, send_mail
from django.core.paginator import EmptyPage, InvalidPage, PageNotAnInteger, Paginator
from django.http import Http404, HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import FormView, ListView
from wagtail.models import Page, Site
from wagtail.search.backends import get_search_backend
from wagtail.contrib.search_promotions.models import Query
from wagtailseo.utils import StructDataEncoder, get_struct_data_images

from shop.cat_tree import Counter
from shop.filters import CompilerFilter
from shop.forms import EnquiryForm, MailListForm
from shop.models import (
    Address,
    Book,
    Category,
    Compiler,
    Contact,
    Enquiry,
    HostPage,
    Item,
    GlobalSettings,
    ContactOptions,
)
from shop.tables import BookTable
from shop.templatetags.shop_tags import unmarkdown
from shop.truncater import truncate
from shop.views.legacy_views import legacy_view

logger = logging.getLogger(__name__)


def home_view(request):
    clear_bad_ip(request)
    if "page_id" in request.GET:
        return legacy_view(request, request.GET["page_id"])
    return redirect("/pages/")


def item_view(request, ref, slug):
    """Public view of a single object"""
    template_name = "shop/public/item_detail.html"
    # item = get_object_or_404(Item, ref=ref)
    item = Item.objects.filter(ref=ref).first()
    if not item:
        raise Http404
    if not slug and item.slug:
        return redirect("public_item", ref=ref, slug=item.slug)
    if not item.description:
        item.description = "No description available"
    clean_description = unmarkdown(item.description).replace("\n", " ")
    context = add_page_context(
        request,
        context={},
        path=request.path,
        title=item.name,
        description=truncate(clean_description, 200),
    )
    page = context["page"]
    context["item"] = item
    images, _ = item.visible_images()
    if images:
        image = images[0]
        context["images"] = images
    else:
        image = None
    if item.category_id:
        category = get_object_or_404(Category, id=item.category_id)
        context["breadcrumb"] = category.breadcrumb_nodes(item_view=True)
        context["category"] = category
        page.title = f"{category.seo_prefix()} {item.ref}"
        # SEO data when category and image exist
        if image:
            sd_dict = {
                "@context": "https://schema.org/",
                "@type": "Product",
                "category": category.name,
                "name": item.name,
                "description": clean_description,
                "image": get_struct_data_images(
                    site=Site.find_for_request(request), image=image
                ),
            }
            page.structured_data = json.dumps(sd_dict, cls=StructDataEncoder)
            page.og_image = image
    form = EnquiryForm()
    form.fields["subject"].initial = f"Enquiry about {item.ref}"
    context["form"] = form
    return render(request, template_name, context)


def catalogue_view(request, slugs=None, archive=False):
    clear_bad_ip(request)
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
    """add wagtail host page to context. Raise 404 if slug not found"""
    clear_bad_ip(request)
    if not title:
        title = "Guest and Gray"
    if not description:
        description = ""
    try:
        page = HostPage.objects.filter(live=True).first()
    except HostPage.DoesNotExist:
        raise Http404
    # page.cover_image = None
    page.title = title
    page.canonical_url = page.get_full_url().replace("/pages/host-page/", path)
    page.search_description = description
    context["page"] = page
    context["self"] = page
    return context


def contact_view(request):
    template_name = "shop/public/contact_page.html"
    context = add_page_context(
        request,
        context={
            "send_message": GlobalSettings.record().contact_options
            != ContactOptions.NO_CONTACT_EMAIL
        },
        path=request.path,
        title="Contact Guest and Gray",
        description="Contact Guest and Gray",
    )
    return render(request, template_name, context)


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

        # # get all codered models
        # pagemodels = sorted(get_page_models(), key=lambda k: k.search_name)
        # # get filterable models
        # for model in pagemodels:
        #     if model.search_filterable:
        #         pagetypes.append(model)

        # get backend
        backend = get_search_backend()

        # Custom search code
        items_1 = Item.objects.filter(image__isnull=False, archive=False)
        items_3 = Item.objects.filter(image__isnull=False, archive=True)
        items_2 = Item.objects.filter(image__isnull=True, archive=False)
        items_4 = Item.objects.filter(image__isnull=True, archive=True)
        if public:
            items_1 = items_1.filter(visible=True)
            items_2 = items_2.filter(visible=True)
            items_3 = items_3.filter(visible=True)
            items_4 = items_4.filter(visible=True)
        results_1 = backend.search(search_query, items_1)
        results_2 = backend.search(search_query, items_2)
        results_3 = backend.search(search_query, items_3)
        results_4 = backend.search(search_query, items_4)
        results_page = backend.search(search_query, Page)
        results = list(chain(results_1, results_2, results_3, results_4, results_page))
        # paginate results
        if results:
            paginator = Paginator(
                results, LayoutSettings.for_request(request).search_num_results
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
            "public": public,
        },
    )


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


class CaptchaHoneyPotMixin:
    """Support captchas and honeypot in modal forms"""

    global_settings = None

    def dispatch(self, request, *args, **kwargs):
        if not request.htmx:
            return HttpResponseBadRequest("HTMX expected")
        self.global_settings = GlobalSettings.record()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Explicit handling of honeypot instead of @method_decorator(check_honeypot, name="post")
        field = settings.HONEYPOT_FIELD_NAME
        if field not in request.POST or request.POST[field] != "":
            return HttpResponse("Thanks for nothing")
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        global_settings = self.global_settings.record()
        context["recaptcha_site"] = settings.GOOGLE_RECAPTCHA_SITE_KEY
        context["hcaptcha_site"] = settings.HCAPTCHA_SITE_KEY
        context["hcaptcha"] = (
            global_settings.contact_options == ContactOptions.USE_HCAPTCHA
        )
        context["recaptcha"] = (
            global_settings.contact_options == ContactOptions.USE_RECAPTCHA
        )
        return context

    def is_captcha_valid(self):
        option = self.global_settings.record().contact_options
        if option == ContactOptions.USE_HCAPTCHA:
            values = {
                "secret": settings.HCAPTCHA_SECRET_KEY,
                "response": self.request.POST.get("h-captcha-response"),
            }
            url = "https://hcaptcha.com/siteverify"
        elif option == ContactOptions.USE_RECAPTCHA:
            values = {
                "secret": settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                "response": self.request.POST.get("g-recaptcha-response"),
            }
            url = "https://www.google.com/recaptcha/api/siteverify"
        if option in (ContactOptions.USE_HCAPTCHA, ContactOptions.USE_RECAPTCHA):
            return requests.post(url, values).json()["success"]
        return True

    def captcha_invalid(self, form):
        """Allow only 1 retry for omitted captcha"""
        if is_same_bad_ip(self.request):
            return HttpResponse("failed")
        save_bad_ip(self.request)
        context = self.get_context_data(form=form)
        context["captcha_error"] = True
        return self.render_to_response(context)


class MailListModalView(CaptchaHoneyPotMixin, FormView):
    # Add to mail list on footer
    form_class = MailListForm
    template_name = "shop/public/mail_list_modal.html"

    def form_valid(self, form):
        if not self.is_captcha_valid():
            return self.captcha_invalid(form)
        process_contact_response(self.request, form.cleaned_data, mail_list=True)
        return render(self.request, "shop/public/mail_list_added_modal.html")


class EnquiryModalView(CaptchaHoneyPotMixin, FormView):
    # Handles enquiry on item page and general enquiry on contact page
    form_class = EnquiryForm
    subject = ""
    ref = ""

    def dispatch(self, request, *args, **kwargs):
        self.ref = self.kwargs.get("ref", None)
        if self.ref:
            self.subject = f"Enquiry re item {self.ref}"
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        if GlobalSettings.record().contact_options == ContactOptions.NO_CONTACT_EMAIL:
            return ["shop/public/enquiry_phone.html"]
        return ["shop/public/enquiry_form.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subject"] = self.subject
        context["ref"] = self.ref
        return context

    def form_valid(self, form):
        if not self.is_captcha_valid():
            return self.captcha_invalid(form)
        enquiry = process_contact_response(
            self.request, form.cleaned_data, mail_list=False
        )
        return render(
            self.request,
            "shop/public/contact_submitted_modal.html",
            {"enquiry": enquiry},
        )


# ==== All following code is support logic for enquiries ====
def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def clear_bad_ip(request):
    if request.session.get("bad_ip", None):
        del request.session["bad_ip"]


def save_bad_ip(request):
    request.session["bad_ip"] = get_client_ip(request)


def is_same_bad_ip(request):
    client_ip = get_client_ip(request)
    bad_ip = request.session.get("bad_ip", None)
    return client_ip == bad_ip


def process_contact_response(request, data, mail_list):
    """Mail list is True if it is just a request to add to the mail list"""
    clear_bad_ip(request)
    contact = Contact.objects.filter(main_address__email=data["email"]).first()
    if not "phone" in data.keys():
        data["phone"] = ""
    if contact and data["phone"]:
        if not (
            contact.main_address.work_phone == data["phone"]
            or contact.main_address.mobile_phone == data["phone"]
        ):
            contact = None
    if not contact:
        contact = Contact.objects.create(
            first_name=data["first_name"],
            last_name=data["last_name"],
        )
        address = Address.objects.create(
            mobile_phone=data["phone"], email=data["email"], contact=contact
        )
        contact.main_address = address
    if data.get("mail_consent"):
        contact.mail_consent = True
        contact.consent_date = datetime.now().date()
    contact.save()
    if mail_list:
        # Confirm to customer
        send_mail(
            "Confirmation from chinese-porcelain-art.com",
            "You have been added to our mail list",
            settings.DEFAULT_FROM_EMAIL,
            [contact.main_address.email],
            fail_silently=False,
        )
        return None
    # item enquiry or general message
    item = None
    if "ref" in request.POST:
        item = Item.objects.filter(ref=request.POST["ref"]).first()
        if item:
            data["subject"] += f" about {item.ref}"
    enquiry = Enquiry.objects.create(
        subject=data["subject"], message=data["message"], contact=contact, item=item
    )
    # Inform staff
    send_mail(
        f"{data['subject']}",
        f"From {data['email']}\n{data['message']}",
        settings.DEFAULT_FROM_EMAIL,
        [settings.INFORM_EMAIL],
        fail_silently=False,
    )
    # connection = get_connection(
    #     fail_silently=False,
    # )
    # email = EmailMessage(
    #     subject=data["subject"],
    #     body=data["message"],
    #     from_email=data["email"],
    #     to=[settings.INFORM_EMAIL],
    #     reply_to=[data["email"]],
    #     connection=connection,
    # )
    # email.send(fail_silently=False)

    message = "Thank you for your enquiry. We will respond as soon as possible."
    if data["mail_consent"]:
        message += "\nYou have been added to our mail list."
    # Confirm to customer
    send_mail(
        "Confirmation from chinese-porcelain-art.com",
        message,
        settings.DEFAULT_FROM_EMAIL,
        [contact.main_address.email],
        fail_silently=False,
    )
    return enquiry
