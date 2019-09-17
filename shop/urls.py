from django.urls import path, re_path
from shop.views.staff_views import (
    StaffHomeView,
    ItemCreateView,
    ItemDetailView,
    ItemUpdateView,
    ItemListView,
    ItemImagesView,
    CategoryClearView,
    CategoryCreateView,
    CategoryUpdateView,
    CategoryListView,
    CategoryDetailView,
)
from shop.views.public_views import home_view, item_view, catalogue_view, search_view
from shop.views.import_views import (
    import_objects_view,
    import_progress_view,
    import_images_view,
    # import_images_progress_view,
    set_category_images_view,
)

staff_urls = [
    path("", StaffHomeView.as_view(), name="staff_home"),
    path("item/create/", ItemCreateView.as_view(), name="item_create"),
    path("item/detail/<int:pk>/", ItemDetailView.as_view(), name="item_detail"),
    path("item/update/<int:pk>/", ItemUpdateView.as_view(), name="item_update"),
    path("item/list/", ItemListView.as_view(), name="item_list"),
    path("item/images/<int:pk>/", ItemImagesView.as_view(), name="item_images"),
    path("import/", import_objects_view, name="import_objects"),
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
    path("search/", search_view, name="codered_search"),
    path(
        "catalogue/", catalogue_view, {"archive": False}, name="public_catalogue_root"
    ),
    re_path(
        r"catalogue/(?P<slugs>[\w_/-]+)/$",
        catalogue_view,
        {"archive": False},
        name="public_catalogue",
    ),
    path("archive/", catalogue_view, {"archive": True}, name="public_catalogue_root"),
    re_path(
        r"archive/(?P<slugs>[\w_/-]+)/$",
        catalogue_view,
        {"archive": True},
        name="public_catalogue",
    ),
    path("item/<slug:slug>,<int:pk>/", item_view, name="public_item"),
]
