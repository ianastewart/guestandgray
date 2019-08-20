from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.views.generic import View, TemplateView, CreateView, UpdateView, ListView, DetailView
from .models import Object, Category, CustomImage
from .forms import ObjectForm, CategoryForm
from .import_data import load_image

class StaffHomeView(TemplateView):
    template_name = "shop/staff_home.html"


class ObjectClearView(View):
    """ Clears all objects from the database """
    def get(self, request):
        #Object.objects.all().delete()
        messages.add_message(request, messages.INFO, "All objects cleared")
        return redirect('staff_home')


class ObjectCreateView(CreateView):
    model = Object
    form_class = ObjectForm
    template_name = "shop/object_form.html"
    success_url = reverse_lazy("object_list")

    def post(self, request, *args, **kwargs):
        result = super().post(request, *args, **kwargs)
        if 'load' in request.POST:
            pass
        return result


class ObjectUpdateView(UpdateView):
    model = Object
    form_class = ObjectForm
    template_name = "shop/object_form.html"
    success_url = reverse_lazy("object_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["photos"] = CustomImage.objects.filter(object_id=self.object.id)
        return context

    def post(self, request, *args, **kwargs):
        result = super().post(request, *args, **kwargs)
        if 'load' in request.POST:
            load_image(self.object)
        return result


class ObjectListView(ListView):
    model = Object
    template_name = "shop/object_list.html"

    def get_queryset(self):
        return Object.objects.all()


class CategoryClearView(View):
    """ Clears all objects from the database """

    def get(self, request):
        Category.objects.all().delete()
        messages.add_message(request, messages.INFO, "All categories cleared")
        return redirect('staff_home')

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
        return Category.objects.all()


class CategoryDetailView(DetailView):
    model = Category
    template_name = "shop/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = self.object.object_set.all()
        return context
