from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView

from shop.forms import CategoryForm
from shop.models import Category
from shop.tables import CategoryTable
from shop.views.generic_views import FilteredTableView


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
    template_name = "generic_table.html"
    table_class = CategoryTable
    table_pagination = {"per_page": 100}
    heading = "Categories"

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
