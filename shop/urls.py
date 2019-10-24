from django.urls import path, re_path
from shop.views.staff_views import (
    StaffHomeView,
    ItemCreateView,
    ItemDetailView,
    ItemUpdateView,
    ItemUpdateViewAjax,
    ItemListView,
    ItemImagesView,
    CategoryCreateView,
    CategoryUpdateView,
    CategoryTreeView,
    CategoryListView,
    CategoryDetailView,
    ContactCreateView,
    ContactListView,
    ContactUpdateView,
    VendorListView,
    EnquiryListView,
    BookListView,
    BookCreateView,
    BookUpdateView,
    CompilerListView,
    CompilerCreateView,
    CompilerUpdateView,
)
from shop.views.public_views import (
    home_view,
    item_view,
    catalogue_view,
    search_view,
    ContactView,
    ContactSubmittedView,
    BibliographyView,
)
from shop.views.import_views import upload_view


staff_urls = [
    path("", StaffHomeView.as_view(), name="staff_home"),
    # Items
    path("item/create/", ItemCreateView.as_view(), name="item_create"),
    path("item/detail/<int:pk>/", ItemDetailView.as_view(), name="item_detail"),
    path("item/update/<int:pk>/", ItemUpdateView.as_view(), name="item_update"),
    path("item/list/", ItemListView.as_view(), name="item_list"),
    path(
        "item/list/update/<int:pk>/",
        ItemUpdateViewAjax.as_view(),
        name="item_update_ajax",
    ),
    path("item/list/create/", ItemCreateView.as_view(), name="item_create_json"),
    path("item/images/<int:pk>/", ItemImagesView.as_view(), name="item_images"),
    # Categories
    path("category/create/", CategoryCreateView.as_view(), name="category_create"),
    path(
        "category/update/<int:pk>/",
        CategoryUpdateView.as_view(),
        name="category_update",
    ),
    path("category/tree/", CategoryTreeView.as_view(), name="category_tree"),
    path("category/list/", CategoryListView.as_view(), name="category_list"),
    path(
        "category/detail/<int:pk>/",
        CategoryDetailView.as_view(),
        name="category_detail",
    ),
    # Contacts
    path("contact/list/", ContactListView.as_view(), name="contact_list"),
    path("contact/list/create/", ContactCreateView.as_view(), name="contact_create"),
    path(
        "contact/list/update/<int:pk>/",
        ContactUpdateView.as_view(),
        name="contact_update",
    ),
    path("vendor/list/", VendorListView.as_view(), name="vendor_list"),
    path("vendor/list/create/", ContactCreateView.as_view(), name="vendor_create"),
    path(
        "vendor/list/update/<int:pk>/",
        ContactUpdateView.as_view(),
        name="vendor_update",
    ),
    # Enquiries
    path("enquiry/list/", EnquiryListView.as_view(), name="enquiry_list"),
    # Compilers
    path("compilers/", CompilerListView.as_view(), name="compiler_list"),
    path("compilers/create/", CompilerCreateView.as_view(), name="compiler_create"),
    path(
        "compilers/update/<int:pk>/",
        CompilerUpdateView.as_view(),
        name="compiler_update",
    ),
    # Books
    path("books/", BookListView.as_view(), name="book_list"),
    path("books/create/", BookCreateView.as_view(), name="book_create"),
    path("books/update/<int:pk>/", BookUpdateView.as_view(), name="book_update"),
    # Search
    path("search/", search_view, {"public": False}, name="search"),
    # Upload
    path("upload/", upload_view, name="upload"),
]

public_urls = [
    path("", home_view, name="public_home"),
    path("search/", search_view, {"public": True}, name="codered_search"),
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
    path("contact/", ContactView.as_view(), name="public_contact"),
    path(
        "contact/submitted/",
        ContactSubmittedView.as_view(),
        name="public_contact_submitted",
    ),
    path("bibliography/", BibliographyView.as_view(), name="bibliography"),
    path(
        "pages/information/bibliography/",
        BibliographyView.as_view(),
        name="bibliography",
    ),
]
