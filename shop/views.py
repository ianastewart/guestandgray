from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from .models import Object, Section, CustomImage
from .forms import ObjectForm, SectionForm


class ObjectCreateView(CreateView):
    model = Object
    form_class = ObjectForm
    template_name = "shop/bootstrap_form.html"
    success_url = reverse_lazy("object_list")


class ObjectUpdateView(UpdateView):
    model = Object
    form_class = ObjectForm
    template_name = "shop/bootstrap_form.html"
    success_url = reverse_lazy("object_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["photos"] = CustomImage.objects.filter(object_id=self.object.id)
        return context


class ObjectListView(ListView):
    model = Object
    template_name = "shop/object_list.html"

    def get_queryset(self):
        return Object.objects.all()


class SectionCreateView(CreateView):
    model = Section
    form_class = SectionForm
    template_name = "shop/bootstrap_form.html"
    success_url = reverse_lazy("section_list")


class SectionUpdateView(UpdateView):
    model = Section
    form_class = SectionForm
    template_name = "shop/bootstrap_form.html"
    success_url = reverse_lazy("section_list")


class SectionListView(ListView):
    model = Section
    template_name = "shop/section_list.html"

    def get_queryset(self):
        return Section.objects.all()


class SectionDetailView(DetailView):
    model = Section
    template_name = "shop/section_detail.html"
    context_object_name = "section"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = self.object.object_set.all()
        return context
