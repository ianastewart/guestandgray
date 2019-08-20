from django.urls import path
from shop.views import (
    StaffHomeView,
    ObjectClearView,
    ObjectCreateView,
    ObjectUpdateView,
    ObjectListView,
    CategoryClearView,
    CategoryCreateView,
    CategoryUpdateView,
    CategoryListView,
    CategoryDetailView,
)
from shop.import_data import import_objects_view, import_progress_view, import_images_view, import_images_progress_view

staff_urls = [
    path("", StaffHomeView.as_view(), name="staff_home"),
    path("object/clear/", ObjectClearView.as_view(), name="object_clear"),
    path("object/create/", ObjectCreateView.as_view(), name="object_create"),
    path("object/update/<int:pk>/", ObjectUpdateView.as_view(), name="object_update"),
    path("object/list/", ObjectListView.as_view(), name="object_list"),
    path("import/", import_objects_view, name="import_objects"),
    path("import/progress/", import_progress_view, name="import_progress"),
    path("import/images/", import_images_view, name="import_images"),
    path("import/images/progress/", import_images_progress_view, name="import_images_progress"),

    path("category/create/", CategoryClearView.as_view(), name="category_clear"),
    path("category/create/", CategoryCreateView.as_view(), name="category_create"),
    path("category/update/<int:pk>/", CategoryUpdateView.as_view(), name="category_update"),
    path("category/list/", CategoryListView.as_view(), name="category_list"),
    path("category/detail/<int:pk>/", CategoryDetailView.as_view(), name="category_detail"),
]
