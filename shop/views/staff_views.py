import logging
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.views.generic import (
    View,
    TemplateView,
    CreateView,
    UpdateView,
    ListView,
    DetailView,
)
from shop.models import Object, Category, CustomImage
from shop.forms import ObjectForm, CategoryForm

logger = logging.getLogger(__name__)


class StaffHomeView(TemplateView):
    template_name = "shop/staff_home.html"


class ObjectClearView(View):
    """ Clears all objects from the database """

    def get(self, request):
        # Object.objects.all().delete()
        messages.add_message(request, messages.INFO, "All objects cleared")
        return redirect("staff_home")


class ObjectCreateView(CreateView):
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


class ObjectUpdateView(UpdateView):
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
            self.object.category.image = CustomImage.objects.filter(
                object_id=self.object.id
            )[0]
            self.object.category.save()
            return redirect("category_detail", pk=self.object.category.pk)
        return result

    def get_success_url(self):
        return reverse("category_detail", kwargs={"pk": self.object.category.id})


class ObjectListView(ListView):
    model = Object
    template_name = "shop/object_list.html"

    def get_queryset(self):
        return Object.objects.all().order_by("name")


class CategoryClearView(View):
    """ Clears all objects from the database """

    def get(self, request):
        Category.objects.all().delete()
        messages.add_message(request, messages.INFO, "All categories cleared")
        return redirect("staff_home")


class CategoryCreateView(CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "shop/bootstrap_form.html"
    success_url = reverse_lazy("category_list")


class CategoryUpdateView(UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "shop/bootstrap_form.html"
    success_url = reverse_lazy("category_list")


class CategoryListView(ListView):
    model = Category
    template_name = "shop/category_list.html"

    def get_queryset(self):
        return Category.objects.all().order_by("name")


class CategoryDetailView(DetailView):
    model = Category
    template_name = "shop/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = self.object.object_set.all().order_by("name")
        return context
