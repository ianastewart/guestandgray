from django.urls import path
from shop.views import (
    ObjectCreateView,
    ObjectUpdateView,
    ObjectListView,
    SectionCreateView,
    SectionUpdateView,
    SectionListView,
    SectionDetailView,
)
from shop.import_data import import_objects_view, import_sections_view, index_objects_view

object_urls = [
    path("create/", ObjectCreateView.as_view(), name="object_create"),
    path("update/<int:pk>/", ObjectUpdateView.as_view(), name="object_update"),
    path("list/", ObjectListView.as_view(), name="object_list"),
    path("import/", import_objects_view, name="object_import"),
    path("index/", index_objects_view, name="object_index"),
]

section_urls = [
    path("create/", SectionCreateView.as_view(), name="section_create"),
    path("update/<int:pk>/", SectionUpdateView.as_view(), name="section_update"),
    path("list/", SectionListView.as_view(), name="section_list"),
    path("import/", import_sections_view, name="section_import"),
    path("detail/<int:pk>/", SectionDetailView.as_view(), name="section_detail"),
]
