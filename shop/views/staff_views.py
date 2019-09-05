import logging
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import FileSystemStorage
from django.views.generic import (
    View,
    TemplateView,
    CreateView,
    UpdateView,
    ListView,
    DetailView,
)
from wagtail.images.views.chooser import chooser
from shop.models import Object, Category, CustomImage
from shop.forms import ObjectForm, CategoryForm

logger = logging.getLogger(__name__)


class StaffHomeView(LoginRequiredMixin, TemplateView):
    template_name = "shop/staff_home.html"


class ObjectClearView(LoginRequiredMixin, View):
    """ Clears all objects from the database """

    def get(self, request):
        # Object.objects.all().delete()
        messages.add_message(request, messages.INFO, "All objects cleared")
        return redirect("staff_home")


class ObjectCreateView(LoginRequiredMixin, CreateView):
    model = Object
    form_class = ObjectForm
    template_name = "shop/object_form.html"

    def post(self, request, *args, **kwargs):
        result = super().post(request, *args, **kwargs)
        if "load" in request.POST:
            pass
        return result

    def get_success_url(self):
        return reverse("category_detail", kwargs={"pk": self.object.category.id})


class ObjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Object
    form_class = ObjectForm
    template_name = "shop/object_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["photos"] = CustomImage.objects.filter(object_id=self.object.id)
        return context

    def post(self, request, *args, **kwargs):
        result = super().post(request, *args, **kwargs)
        if "view" in request.POST:
            return redirect("public_object", slug=self.object.slug, pk=self.object.id)
        if "category_image" in request.POST:
            category = self.object.new_category
            category.image = CustomImage.objects.filter(object_id=self.object.id)[0]
            category.save()
            return redirect("category_detail", pk=category.pk)
        elif request.FILES["myfile"]:
            obj = self.get_object()
            # myfile = request.FILES["myfile"]
            # fs = FileSystemStorage()
            # temp_filename = fs.save(myfile.name, myfile)
            # filename = temp_filename.split(".")[0] + ".jpg"
            # images_path = "images/" + filename
            # media_path = "media/original_images/" + filename
            # new_image = CustomImage.objects.create(
            #     file="original_images/" + filename,
            #     title=obj.name,
            #     collection_id=collection_id,
            #     uploaded_by_user=request.user,
            #     object=obj,
            # )
            # uploaded_file_url = fs.url(filename)
        return result

    def get_success_url(self):
        return reverse("category_detail", kwargs={"pk": self.object.new_category.id})


class ObjectListView(LoginRequiredMixin, ListView):
    model = Object
    template_name = "shop/object_list.html"

    def get_queryset(self):
        return Object.objects.all().order_by("name")


class CategoryClearView(LoginRequiredMixin, View):
    """ Clears all objects from the database """

    def get(self, request):
        Category.objects.all().delete()
        messages.add_message(request, messages.INFO, "All categories cleared")
        return redirect("staff_home")


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


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "shop/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        root = Category.objects.get(name="Catalogue")
        return root.get_children().order_by("name")


class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = "shop/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = self.object.object_set.all().order_by("name")
        return context
