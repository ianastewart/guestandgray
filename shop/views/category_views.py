from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect, reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView, View

from shop.cat_tree import tree_json, tree_move
from shop.forms import CategoryForm
from shop.models import Category, Item
from shop.tables import CategoryTable
from table_manager.views import FilteredTableView


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
        cat = self.object
        self.parent = cat.get_parent()
        if self.parent:
            initial["parent_category"] = self.parent.pk
        if cat.image:
            initial["category_ref"] = cat.image.item.ref
        if cat.archive_image:
            initial["archive_ref"] = cat.archive_image.item.ref
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["images_url"] = reverse("category_images")
        context["is_root"] = self.parent is None
        return context

    def form_valid(self, form):
        old_parent = self.object.get_parent()
        new_parent = form.cleaned_data["parent_category"]
        response = super().form_valid(form)
        if old_parent and old_parent.id != new_parent.id:
            self.object.move(new_parent, "sorted-child")
        return response

    def form_invalid(self, form):
        pass


class CategoryTreeView(LoginRequiredMixin, TemplateView):

    template_name = "shop/category_tree.html"

    def get(self, request):
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
            return JsonResponse(tree_json(), safe=False)
        else:
            return super().get(request)

    def post(self, request):
        p = request.POST
        tree_move(p["node"], p["target"], p["previous"], p["position"] == "inside")
        return JsonResponse("OK", safe=False)


class CategoryListView(LoginRequiredMixin, FilteredTableView):
    model = Category
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
        context["images_url"] = reverse("category_images")
        return context

    def post(self, request, **kwargs):
        if "delete" in request.POST:
            self.get_object().delete()
        return redirect("category_list")


class CategoryImagesView(View):
    def get(self, request, *args, **kwargs):
        ref = request.GET.get("ref", None)
        target = request.GET.get("target", None)
        cat = request.GET.get("category", None)
        archive = "archive" in request.GET.get("target")
        data = {}
        if ref and target and cat:
            try:
                item = Item.objects.get(ref=ref)
                category = Category.objects.get(id=cat)
                if item.image is not None:
                    if archive:
                        category.archive_image = item.image
                    else:
                        category.image = item.image
                    category.save()
                    data["image"] = item.image.file.url
                else:
                    data["error"] = f"Item {ref} has no image"

            except Item.DoesNotExist:
                data["error"] = f"There is no item with reference {ref}"
        return JsonResponse(data)
