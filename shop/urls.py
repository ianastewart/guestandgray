from django.urls import path, re_path

from shop.views.item_views import (
    ItemCreateView,
    ItemDetailView,
    ItemUpdateView,
    ItemTableView,
    ItemCategoriseModalView,
)
from shop.views.category_views import (
    CategoryCreateView,
    CategoryUpdateView,
    CategoryTreeView,
    CategoryListView,
    CategoryDetailView,
    CategoryImagesView,
)
from shop.views.contact_views import (
    ContactCreateView,
    ContactUpdateView,
    ContactListView,
    VendorListView,
    BuyerListView,
    EnquiryListView,
    EnquiryDetailView,
    MailListView,
    contact_lookup,
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
    PurchaseLotCreateView,
    PurchaseSummaryCreateView,
    PurchaseSummaryAjaxView,
    PurchaseListView,
    PurchaseDetailModal,
    PurchaseItemAjax,
)
from shop.views.cart_views import (
    CartContentsView,
    CartPriceView,
    CartAddChargeView,
    CartBuyerView,
    CartCheckoutView,
)
from shop.views.invoice_views import InvoiceListView, InvoiceDetailView
from shop.views.staff_views import StaffHomeView, GlobalSettingsView
from shop.views.public_views import (
    home_view,
    item_view,
    catalogue_view,
    search_view,
    contact_view,
    MailListModalView,
    EnquiryModalView,
    BibliographyView,
)

from shop.views.legacy_views import legacy_view
from shop.views.import_views import upload_view
from shop.views.image_views import BasicUploadView, ItemImagesView, image_assign_view

staff_urls = [
    path("", StaffHomeView.as_view(), name="staff_home"),
    path("settings", GlobalSettingsView.as_view(), name="settings"),
    path("admin_search/", search_view, {"public": False}, name="admin_search"),
    # Items
    path("item/list/", ItemTableView.as_view(), name="item_list"),
    path("item/create/", ItemCreateView.as_view(), name="item_create"),
    path("item/detail/<int:pk>/", ItemDetailView.as_view(), name="item_detail"),
    path("item/detail/", ItemDetailView.as_view(), name="item_detail_htmx"),
    path("item/update/<int:pk>/", ItemUpdateView.as_view(), name="item_update"),
    path("item/images/<int:pk>/", ItemImagesView.as_view(), name="item_images"),
    path("image/assign/<int:image_pk>/", image_assign_view, name="image_assign"),
    path(
        "item/list/categorise/",
        ItemCategoriseModalView.as_view(),
        name="item_categorise",
    ),
    # Categories
    path("category/create/", CategoryCreateView.as_view(), name="category_create"),
    path(
        "category/update/<int:pk>/",
        CategoryUpdateView.as_view(),
        name="category_update",
    ),
    path("category/tree/", CategoryTreeView.as_view(), name="category_tree"),
    path("category/images/", CategoryImagesView.as_view(), name="category_images"),
    path("category/list/", CategoryListView.as_view(), name="category_list"),
    path(
        "category/detail/<int:pk>/",
        CategoryDetailView.as_view(),
        name="category_detail",
    ),
    # Contacts including vendors and buyers
    path("contact/list/", ContactListView.as_view(), name="contact_list"),
    path("contact/create/", ContactCreateView.as_view(), name="contact_create"),
    path(
        "contact/update/<int:pk>/", ContactUpdateView.as_view(), name="contact_update"
    ),
    path("contact/update/", ContactUpdateView.as_view(), name="contact_update_htmx"),
    path("contact/lookup/", contact_lookup, name="contact_lookup"),
    # Mail list
    path("contact/mail_list/", MailListView.as_view(), name="mail_list"),
    # Vendors
    path("vendor/lookup/", contact_lookup, name="vendor_lookup"),
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
        "purchase/detail/<int:pk>/",
        PurchaseDetailModal.as_view(),
        name="purchase_detail_modal",
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
        "purchase/create/lot/<int:index>/",
        PurchaseLotCreateView.as_view(),
        name="purchase_lot_create",
    ),
    path(
        "purchase/create/summary/<int:index>/",
        PurchaseSummaryCreateView.as_view(),
        name="purchase_summary",
    ),
    path(
        "purchase/summary/ajax/<str:ref>/",
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
    # Enquiries
    path("enquiry/list/", EnquiryListView.as_view(), name="enquiry_list"),
    path("enquiry/<int:pk>/", EnquiryDetailView.as_view(), name="enquiry_detail"),
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
    # todo upload will be redundant
    path("upload/", upload_view, name="upload"),
    path("basic-upload/", BasicUploadView.as_view(), name="basic_upload"),
    # Cart
    path("cart/contents/", CartContentsView.as_view(), name="cart_contents"),
    path("cart/price/<int:pk>/", CartPriceView.as_view(), name="cart_price"),
    path("cart/add_charge/", CartAddChargeView.as_view(), name="cart_add_charge"),
    path("cart/buyer/", CartBuyerView.as_view(), name="cart_buyer"),
    path("cart/checkout/", CartCheckoutView.as_view(), name="cart_checkout"),
]

public_urls = [
    path("", home_view, name="public_home"),
    path("search/", search_view, {"public": True}, name="crx_search"),
    path(
        "catalogue/", catalogue_view, {"archive": False}, name="public_catalogue_root"
    ),
    re_path(
        r"catalogue/(?P<slugs>[\w_/-]+)/$",
        catalogue_view,
        {"archive": False},
        name="public_catalogue",
    ),
    path("archive/", catalogue_view, {"archive": True}, name="public_archive_root"),
    re_path(
        r"archive/(?P<slugs>[\.\w_/-]+)/$",
        catalogue_view,
        {"archive": True},
        name="public_archive",
    ),
    path("item/<str:ref>/<slug:slug>/", item_view, name="public_item"),
    path("item/<str:ref>/", item_view, {"slug": ""}, name="public_item_ref"),
    path("mail_add/", MailListModalView.as_view(), name="mail_add"),
    path("enquiry/<str:ref>/", EnquiryModalView.as_view(), name="item_enquiry"),
    path("enquiry/", EnquiryModalView.as_view(), name="general_enquiry"),
    path("contact/", contact_view, name="public_contact"),
    path("bibliography/", BibliographyView.as_view(), name="bibliography"),
    path("acatalog/<str:page>/", legacy_view, name="public_legacy"),
]
