from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect, reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView, View
from django.templatetags.static import static
from shop.cat_tree import tree_json, tree_move
from shop.forms import CategoryForm
from shop.models import Category, Item
from shop.tables import CategoryTable
from table_manager.views import FilteredTableView


class StackMixin:
    def clear_stack(self, request):
        request.session["call_stack"] = []

    def get(self, request, *args, **kwargs):
        """ get pushes any return path on to the stack """
        return_path = request.GET.get("return", None)
        if return_path:
            stack = request.session.get("call_stack", [])
            stack.append((request.path, return_path))
            request.session["call_stack"] = stack
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """ Add the current path as the return path to the context """
        context = super().get_context_data(**kwargs)
        context["return"] = f"?return={self.request.path}"
        return context

    def get_success_url(self):
        stack = self.request.session.get("call_stack", None)
        if stack:
            entry = stack.pop()
            while entry:
                if entry[0] == self.request.path:
                    self.request.session["call_stack"] = stack
                    return entry[1]
                else:
                    entry = stack.pop()
        self.request.session["call_stack"] = []
        return "/"


class CategoryCreateView(LoginRequiredMixin, StackMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "shop/category_form.html"
    title = "Create category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["images_url"] = reverse("category_images")
        return context

    def form_valid(self, form):
        d = form.cleaned_data
        parent = Category.objects.get(id=d["parent_category"])
        node = parent.add_child(name=d["name"], description=d["description"])
        node.post_save()
        ref = d.get("category_ref", None)
        if ref:
            item = Item.objects.get(ref=ref)
            node.image = item.image
        ref = d.get("archive_ref", None)
        if ref:
            item = Item.objects.get(ref=ref)
            node.archive_image = item.image
        node.save()
        return redirect(self.get_success_url())


class CategoryUpdateView(LoginRequiredMixin, StackMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "shop/category_form.html"
    title = "Edit category"

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
        d = form.cleaned_data
        ref = d.get("category_ref", None)
        if ref:
            item = Item.objects.get(ref=ref)
            self.object.image = item.image
        ref = d.get("archive_ref", None)
        if ref:
            item = Item.objects.get(ref=ref)
            self.object.archive_image = item.image
        old_parent = self.object.get_parent()
        new_parent = Category.objects.get(id=d["parent_category"])
        response = super().form_valid(form)
        if old_parent and old_parent.id != new_parent.id:
            self.object.move(new_parent, "sorted-child")
        new_parent.post_save()
        return response


class CategoryTreeView(LoginRequiredMixin, StackMixin, TemplateView):
    template_name = "shop/category_tree.html"

    def get(self, request):
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
            return JsonResponse(tree_json(), safe=False)
        else:
            self.clear_stack(request)
            return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        a, b, c, d, e = Category.find_problems()
        context["errors"] = a or b or c or d or e
        return context

    def post(self, request):
        if "fix" in request.POST:
            Category.fix_tree()
            return redirect("category_tree")
        # Ajax response to move node
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


class CategoryDetailView(LoginRequiredMixin, StackMixin, DetailView):
    model = Category
    template_name = "shop/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["shop_items"] = self.object.shop_items()
        context["archive_items"] = self.object.archive_items()
        context["images_url"] = reverse("category_images")
        return context

    def post(self, request, **kwargs):
        if "return" in request.POST:
            pass
        elif "delete" in request.POST:
            self.get_object().delete()
        return redirect(self.get_success_url())


class CategoryImagesView(View):
    def get(self, request, *args, **kwargs):
        ref = request.GET.get("ref", None)
        target = request.GET.get("target", None)
        data = {}
        if ref and target:
            try:
                item = Item.objects.get(ref=ref)
                if item.image is not None:
                    data["image"] = item.image.file.url
                else:
                    data["error"] = f"Item {ref} has no image"
            except Item.DoesNotExist:
                data["error"] = f"There is no item with reference {ref}"
        else:
            data["image"] = static("/shop/images/no_image.png")
        return JsonResponse(data)
