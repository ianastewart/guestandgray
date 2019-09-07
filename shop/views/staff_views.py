import logging
import os.path
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage
from django.views.generic import (
    View,
    TemplateView,
    CreateView,
    UpdateView,
    ListView,
    DetailView,
)
from wagtail.core.models import Collection
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
    template_name = "shop/object_update.html"

    def post(self, request, *args, **kwargs):
        result = super().post(request, *args, **kwargs)
        if "load" in request.POST:
            pass
        return result

    def get_success_url(self):
        return reverse("object_detail", kwargs={"pk": self.object.pk})


class ObjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Object
    form_class = ObjectForm
    template_name = "shop/object_update.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["photos"] = CustomImage.objects.filter(object_id=self.object.id)
        return context

    def get_success_url(self):
        return reverse("object_detail", kwargs={"pk": self.object.pk})


class ObjectImagesView(LoginRequiredMixin, DetailView):
    model = Object
    template_name = "shop/object_images.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["images"] = CustomImage.objects.filter(object_id=self.object.id)
        return context

    def post(self, request, *args, **kwargs):
        # Ajax response to upload request
        if request.FILES["myfile"]:
            obj = self.get_object()
            myfile = request.FILES["myfile"]
            names = myfile.name.split(".")
            error = ""
            if names[1] != "jpg":
                error = "File is not a jpg"
            media_path = os.path.join(
                settings.MEDIA_ROOT, "original_images", myfile.name
            )
            if os.path.exists(media_path):
                error = "Image already exists"
            if error:
                return JsonResponse({"error": error})
            collection_id = Collection.objects.get(name="Root").id
            path = default_storage.save(media_path, myfile)
            new_image = CustomImage.objects.create(
                file="original_images/" + myfile.name,
                title=obj.name,
                collection_id=collection_id,
                uploaded_by_user=request.user,
                object=obj,
            )
            return JsonResponse({"success": new_image.title})
        return JsonResponse({"error": "No file"})


class ObjectDetailView(DetailView):
    model = Object
    template_name = "shop/object_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["price"] = int(self.object.price / 100)
        context["photos"] = CustomImage.objects.filter(object_id=self.object.id)
        return context


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
