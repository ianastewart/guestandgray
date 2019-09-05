from django.urls import path, re_path
from shop.views.staff_views import (
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
from shop.views.public_views import home_view, object_view, catalogue_view
from shop.views.import_views import (
    import_objects_view,
    import_process_view,
    import_progress_view,
    import_images_view,
    # import_images_progress_view,
    set_category_images_view,
)

staff_urls = [
    path("", StaffHomeView.as_view(), name="staff_home"),
    path("object/clear/", ObjectClearView.as_view(), name="object_clear"),
    path("object/create/", ObjectCreateView.as_view(), name="object_create"),
    path("object/update/<int:pk>/", ObjectUpdateView.as_view(), name="object_update"),
    path("object/list/", ObjectListView.as_view(), name="object_list"),
    path("import/", import_objects_view, name="import_objects"),
    path("import/categories/", import_process_view, name="import_categories"),
    path("import/progress/", import_progress_view, name="import_progress"),
    path("import/images/", import_images_view, name="import_images"),
    path(
        "import/category-images/",
        set_category_images_view,
        name="import_category_images",
    ),
    path("category/create/", CategoryClearView.as_view(), name="category_clear"),
    path("category/create/", CategoryCreateView.as_view(), name="category_create"),
    path(
        "category/update/<int:pk>/",
        CategoryUpdateView.as_view(),
        name="category_update",
    ),
    path("category/list/", CategoryListView.as_view(), name="category_list"),
    path(
        "category/detail/<int:pk>/",
        CategoryDetailView.as_view(),
        name="category_detail",
    ),
]

public_urls = [
    path("", home_view, name="public_home"),
    path("catalogue/", catalogue_view, name="public_catalogue_root"),
    re_path(
        r"catalogue/(?P<slugs>[\w_/-]+)/$", catalogue_view, name="public_catalogue"
    ),
    path("object/<slug:slug>,<int:pk>/", object_view, name="public_object"),
]
