from coderedcms import admin_urls as coderedadmin_urls
from coderedcms import urls as codered_urls
from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from wagtail.contrib.sitemaps.sitemap_generator import Sitemap as WagtailSitemap
from wagtail.documents import urls as wagtaildocs_urls
from django.views.generic import TemplateView
from shop.sitemap import ItemSitemap
from shop.urls import public_urls, staff_urls

# from notes.urls import notes_urls


urlpatterns = [
    # Admin
    path("django-admin/", admin.site.urls),
    path("admin/", include(coderedadmin_urls)),
    # Documents
    path("docs/", include(wagtaildocs_urls)),
    path("staff/", include(staff_urls)),
    path("notes/", include("notes.urls")),
    # public
    path("", include(public_urls)),
    # sitemap and robots
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {"wagtail": WagtailSitemap, "items": ItemSitemap}},
    ),
    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="shop/robots.txt", content_type="text/plain"
        ),
    ),
    # re_path(r"^robots\.txt", include("robots.urls")),
    # For anything not caught by a more specific rule above, hand over to
    # the page serving mechanism. This should be the last pattern in the list:
    path("pages/", include(codered_urls)),
]
if settings.DEBUG_TOOLBAR:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
