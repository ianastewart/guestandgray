import logging
import os.path

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    TemplateView,
    CreateView,
    UpdateView,
    ListView,
    DetailView,
)
from wagtail.core.models import Collection

from shop.forms import (
    ItemForm,
    ArchiveItemForm,
    CategoryForm,
    ContactForm,
    BookForm,
    CompilerForm,
)
from shop.models import Item, Category, CustomImage, Contact, Enquiry, Book, Compiler
from shop.tables import (
    ItemTable,
    CategoryTable,
    ContactTable,
    EnquiryTable,
    BookTable,
    CompilerTable,
)
from shop.views.generic_views import FilteredTableView, JsonCrudView
from shop.filters import ItemFilter

logger = logging.getLogger(__name__)


class StaffHomeView(LoginRequiredMixin, TemplateView):
    template_name = "shop/staff_home.html"


class ItemListView(LoginRequiredMixin, FilteredTableView):
    model = Item
    template_name = "shop/generic_table.html"
    table_class = ItemTable
    filter_class = ItemFilter
    modal_class = "wide"
    allow_create = True
    allow_update = True

    def get_queryset(self):
        return Item.objects.all().order_by("ref")


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "shop/item_form.html"


class ItemPostMixin:
    """
    Common post actions used in both regular and json item update views
    Returns True if a command has been actioned ""
    """

    def post_action(self, request, object):
        category = object.category
        if "assign_category" in request.POST:
            category.image = object.image
            category.save()
            return True
        elif "assign_archive" in request.POST:
            category.archive_image = object.image
            category.save()
            return True
        return False


class ItemUpdateView(LoginRequiredMixin, UpdateView, ItemPostMixin):
    model = Item
    template_name = "shop/item_form.html"

    def get_form(self, form_class=None):
        if self.object.archive:
            return ArchiveItemForm(**self.get_form_kwargs())
        else:
            return ItemForm(**self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["photos"] = CustomImage.objects.filter(item_id=self.object.id)
        context["allow_delete"] = True
        return context

    def get_success_url(self):
        return reverse("item_detail", kwargs={"pk": self.object.pk})

    def post(self, request, *args, **kwargs):
        object = self.get_object()
        if self.post_action(request, object):
            return redirect("item_update", object.pk)
        if "delete" in request.POST:
            object.delete()
            messages.add_message(
                request, messages.INFO, f"Item ref: {object.ref} has been deleted"
            )
            return redirect("item_list")
        return super().post(request, *args, **kwargs)


class ItemUpdateViewAjax(LoginRequiredMixin, JsonCrudView, ItemPostMixin):
    model = Item
    template_name = "shop/includes/partial_item_form.html"
    update = True
    allow_delete = True

    def get_form_class(self):
        return ArchiveItemForm if self.object.archive else ItemForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["object"] = self.object.image
        context["photos"] = CustomImage.objects.filter(item_id=self.object.id)
        return context

    def post(self, request, *args, **kwargs):
        object = self.get_object(**kwargs)
        if self.post_action(request, object):
            return redirect("item_update_ajax", object.pk)
        return super().post(request, *args, **kwargs)


class ItemImagesView(LoginRequiredMixin, DetailView):
    model = Item
    template_name = "shop/item_images.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # primary image always first in list
        images = []
        exclude = 0
        if self.object.image:
            images.append(self.object.image)
            exclude = self.object.image.id
        for image in CustomImage.objects.filter(item_id=self.object.id).order_by(
            "title"
        ):
            if image.id != exclude:
                images.append(image)
        context["images"] = images
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        result = {"error": "Bad command"}
        if "action" in request.POST:
            action = request.POST["action"]
            id = request.POST["id"]
            try:
                image = CustomImage.objects.get(id=id)
            except CustomImage.DoesNotExist:
                result = {"error": "Bad image id"}
                return JsonResponse(result)

            if action == "delete":
                primary = self.object.image_id == image.id
                # Just remove the reference to the item, leaving image in the database
                image.item = None
                image.save()
                if primary:
                    # if we delete the primary, try to make first remaining image primary
                    images = CustomImage.objects.filter(item_id=self.object.id)
                    if images:
                        self.object.image = images[0]
                    else:
                        self.object.image = None
                    self.object.save()
                result = {"success": "deleted"}

            elif action == "primary":
                self.object.image = image
                self.object.save()
                result = {"success": "Made primary"}

        elif request.FILES["myfile"]:
            myfile = request.FILES["myfile"]
            names = myfile.name.split(".")
            error = ""
            if names[len(names) - 1] == "jpg":
                short_path = os.path.join("original_images", myfile.name)
                full_path = os.path.join(settings.MEDIA_ROOT, short_path)
                if os.path.exists(full_path):

                    try:
                        existing_set = CustomImage.objects.filter(file=short_path)
                        if len(existing_set) > 1:
                            error = "Multiple copies already in database."
                        elif len(existing_set) == 1:
                            existing = existing_set[0]
                            if existing.item:
                                error = "Image already in the database. "
                                if existing.item.id == self.object.id:
                                    error += "It is linked to this item."
                                else:
                                    error += f"It is linked to Ref: {existing.item.ref }, {existing.title}."
                        else:

                            os.remove(full_path)
                    except CustomImage.DoesNotExist:
                        # if file exists but is not used by a CustomImage, overwrite it
                        os.remove(full_path)
            else:
                error = "File is not an image. Please select a .jpg"
            if error:
                result = {"error": error}
            else:
                collection_id = Collection.objects.get(name="Root").id
                path = default_storage.save(full_path, myfile)
                new_image = CustomImage.objects.create(
                    file=short_path,
                    title=self.object.name,
                    collection_id=collection_id,
                    uploaded_by_user=request.user,
                    item=self.object,
                )
                result = {"success": new_image.title}
        return JsonResponse(result)


class ItemDetailView(DetailView):
    model = Item
    template_name = "shop/item_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["images"] = self.object.images.all().exclude(id=self.object.image_id)
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "shop/category_form.html"
    success_url = reverse_lazy("category_list")
    title = "Create category"


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "shop/category_form.html"
    success_url = reverse_lazy("category_list")
    title = "Update category"

    def get_initial(self):
        initial = super().get_initial()
        cat = self.object.get_parent()
        initial["parent_category"] = cat.pk
        return initial

    def form_valid(self, form):
        old_parent = self.object.get_parent()
        new_parent = form.cleaned_data["parent_category"]
        response = super().form_valid(form)
        if old_parent.id != new_parent.id:
            self.object.move(new_parent, "sorted-child")
        return response


class CategoryTreeView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "shop/category_tree.html"
    context_object_name = "categories"

    def get_queryset(self):
        root = Category.objects.get(name="Catalogue")
        return root.get_children().order_by("name")


class CategoryListView(LoginRequiredMixin, FilteredTableView):
    model = Category
    template_name = "shop/generic_table.html"
    table_class = CategoryTable
    table_pagination = {"per_page": 100}

    def get_queryset(self):
        root = Category.objects.get(name="Catalogue")
        return root.get_descendants().order_by("name")


class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = "shop/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item_list"] = self.object.item_set.all().order_by("ref")
        return context


class ContactListView(LoginRequiredMixin, FilteredTableView):
    model = Contact
    template_name = "shop/generic_table.html"
    table_class = ContactTable
    table_pagination = {"per_page": 100}
    allow_create = True
    allow_update = True

    def get_queryset(self):
        return Contact.objects.all().order_by("last_name")


class ContactCreateView(LoginRequiredMixin, JsonCrudView):
    model = Contact
    form_class = ContactForm
    template_name = "shop/includes/generic_modal_form.html"
    horizontal_form = True


class ContactUpdateView(LoginRequiredMixin, JsonCrudView):
    model = Contact
    form_class = ContactForm
    template_name = "shop/includes/generic_modal_form.html"
    horizontal_form = True
    update = True
    allow_delete = True


class EnquiryListView(LoginRequiredMixin, FilteredTableView):
    model = Enquiry
    template_name = "shop/generic_table.html"
    table_class = EnquiryTable
    table_pagination = {"per_page": 10}
    allow_update = True

    def get_queryset(self):
        return Enquiry.objects.all().order_by("-date")


class CompilerListView(LoginRequiredMixin, FilteredTableView):
    model = Compiler
    template_name = "shop/generic_table.html"
    table_class = CompilerTable
    table_pagination = {"per_page": 100}
    allow_create = True
    allow_update = True

    def get_queryset(self):
        return Compiler.objects.all().order_by("name")


class CompilerCreateView(LoginRequiredMixin, JsonCrudView):
    model = Compiler
    form_class = CompilerForm
    template_name = "shop/includes/generic_modal_form.html"


class CompilerUpdateView(CompilerCreateView):
    update = True
    allow_delete = True


class BookListView(LoginRequiredMixin, FilteredTableView):
    model = Book
    template_name = "shop/generic_table.html"
    table_class = BookTable
    table_pagination = {"per_page": 100}
    allow_create = True
    allow_update = True

    def get_queryset(self):
        return Book.objects.all().order_by("title")


class BookCreateView(LoginRequiredMixin, JsonCrudView):
    model = Book
    form_class = BookForm
    template_name = "shop/includes/generic_modal_form.html"


class BookUpdateView(BookCreateView):
    update = True
    allow_delete = True
