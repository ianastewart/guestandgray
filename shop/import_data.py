from django.shortcuts import render
from import_export import resources
from import_export.fields import Field
from tablib import Dataset
from .models import Object, Section


class ObjectResource(resources.ModelResource):
    class Meta:
        model = Object
        fields = ("id", "name", "description", "price", "image_file", "section")

    name = Field(attribute="name", column_name="Short Description")
    description = Field(attribute="description", column_name="Full Description")
    price = Field(attribute="price", column_name="Price")
    image_file = Field(attribute="image_file", column_name="Image filename")
    section_text = Field(attribute="section_text", column_name="Section Text")


class SectionResource(resources.ModelResource):
    class Meta:
        model = Section
        fields = ("id", "name")


def import_objects_view(request):
    template_name = "shop/import.html"
    context = {"type": "Objects"}
    if request.method == "POST":
        object_resource = ObjectResource()
        dataset = Dataset()
        new_objects = request.FILES["myfile"]
        imported_data = dataset.load(new_objects.read())

        result = object_resource.import_data(dataset, dry_run=True)  # Test the data import

        if result.has_errors():
            context["result"] = "Errors"
        else:
            object_resource.import_data(dataset, dry_run=False)  # Actually import now
            context["result"] = f"Success {result.total_rows} rows"

    return render(request, template_name, context=context)


def import_sections_view(request):
    template_name = "shop/import.html"
    context = {"type": "Sections"}
    if request.method == "POST":
        object_resource = SectionResource()
        dataset = Dataset()
        csv_data = request.FILES["myfile"]
        dataset.load(csv_data.read())
        result = object_resource.import_data(dataset, dry_run=True)  # Test the data import
        if result.has_errors():
            context["result"] = "Errors"
        else:
            object_resource.import_data(dataset, dry_run=False)  # Actually import now
            context["result"] = "Success"
    return render(request, template_name, context=context)


def index_objects_view(request):
    template_name = "shop/index.html"
    context = {}
    if request.method == "POST":
        objects = Object.objects.all()
        count = 0
        errors = 0
        empty = 0
        for item in objects:
            if item.section_text:
                sep = item.section_text.find("|")
                if sep > 0:
                    key = item.section_text[0:sep]
                else:
                    key = item.section_text
                section = Section.objects.filter(name=key)
                if section:
                    count += 1
                    item.section_id = section[0].id
                    item.save()
                else:
                    errors += 1
            else:
                empty += 1
        context["count"] = count
        context["errors"] = errors
        context["empty"] = empty
    return render(request, template_name, context=context)
