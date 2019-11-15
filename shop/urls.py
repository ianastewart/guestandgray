from django.urls import path, re_path
from shop.views.item_views import (
    ItemCreateView,
    ItemCreateAjax,
    ItemDetailView,
    ItemUpdateView,
    ItemUpdateAjax,
    ItemListView,
    ItemImagesView,
)
from shop.views.category_views import (
    CategoryCreateView,
    CategoryUpdateView,
    CategoryTreeView,
    CategoryListView,
    CategoryDetailView,
)
from shop.views.contact_views import (
    ContactCreateView,
    ContactUpdateView,
    ContactListView,
    VendorListView,
    BuyerListView,
    EnquiryListView,
    vendor_lookup,
)
from shop.views.book_views import (
    BookListView,
    BookCreateView,
    BookUpdateView,
    CompilerListView,
    CompilerCreateView,
    CompilerUpdateView,
)
from shop.views.purchase_views import (
    PurchaseStartView,
    PurchaseVendorView,
    PurchaseVendorCreateView,
    PurchaseDataCreateView,
    PurchaseExpenseCreateView,
    PurchaseItemCreateView,
    PurchaseSummaryCreateView,
    PurchaseSummaryAjaxView,
    PurchaseListView,
    PurchaseDetailAjax,
    PurchaseItemAjax,
)
from shop.views.staff_views import (
    StaffHomeView,
    InvoiceListView,
    InvoiceDetailView,
    InvoiceTableView,
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
        "item/list/update/<int:pk>/", ItemUpdateAjax.as_view(), name="item_update_ajax"
    ),
    path("item/list/create/", ItemCreateAjax.as_view(), name="item_create_ajax"),
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
    # Contacts including vendors and buyers
    path("contact/list/", ContactListView.as_view(), name="contact_list"),
    path("contact/list/create/", ContactCreateView.as_view(), name="contact_create"),
    path(
        "contact/list/update/<int:pk>/",
        ContactUpdateView.as_view(),
        name="contact_update",
    ),
    path("vendor/lookup/", vendor_lookup, name="vendor_lookup"),
    path("vendor/list/", VendorListView.as_view(), name="vendor_list"),
    path("vendor/list/create/", ContactCreateView.as_view(), name="vendor_create"),
    path(
        "vendor/list/update/<int:pk>/",
        ContactUpdateView.as_view(),
        name="vendor_update",
    ),
    path("buyer/list/", BuyerListView.as_view(), name="buyer_list"),
    path("buyer/list/create/", ContactCreateView.as_view(), name="buyer_create"),
    path(
        "buyer/list/update/<int:pk>/", ContactUpdateView.as_view(), name="buyer_update"
    ),
    # Purchases
    path("purchase/list/", PurchaseListView.as_view(), name="purchase_list"),
    path(
        "purchase/list/detail/<int:pk>/",
        PurchaseDetailAjax.as_view(),
        name="purchase_detail",
    ),
    path("purchase/start/", PurchaseStartView.as_view(), name="purchase_start"),
    path(
        "purchase/create/<int:index>/",
        PurchaseVendorView.as_view(),
        name="purchase_vendor",
    ),
    path(
        "purchase/create/<int:index>/vendor/",
        PurchaseVendorCreateView.as_view(),
        name="purchase_create_vendor",
    ),
    path(
        "purchase/create/data/<int:index>/",
        PurchaseDataCreateView.as_view(),
        name="purchase_data_create",
    ),
    path(
        "purchase/create/item/<int:index>/",
        PurchaseItemCreateView.as_view(),
        name="purchase_item_create",
    ),
    path(
        "purchase/create/expense/<int:index>/",
        PurchaseExpenseCreateView.as_view(),
        name="purchase_expense_create",
    ),
    path(
        "purchase/create/summary/<int:index>/",
        PurchaseSummaryCreateView.as_view(),
        name="purchase_summary",
    ),
    path(
        "purchase/summary/ajax/<int:index>/",
        PurchaseSummaryAjaxView.as_view(),
        name="purchase_summary_ajax",
    ),
    path(
        "purchase/item/ajax/<int:pk>/",
        PurchaseItemAjax.as_view(),
        name="purchase_item_ajax",
    ),
    # Invoices
    path("invoice/list/", InvoiceListView.as_view(), name="invoice_list"),
    path(
        "invoice/list/detail/<int:pk>/",
        InvoiceDetailView.as_view(),
        name="invoice_detail",
    ),
    path("invoice/table/", InvoiceTableView.as_view(), name="invoice_table"),
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
