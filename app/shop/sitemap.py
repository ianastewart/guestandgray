import datetime

from django.contrib.sitemaps import Sitemap

from shop.models import Item


class ItemSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return Item.objects.filter(visible=True, image__isnull=False).select_related(
            "image"
        )

    def lastmod(self, item):
        return item.updated

    def location(self, item):
        return item.get_absolute_url()

    # copied from django Sitemap
    def __get(self, name, obj, default=None):
        try:
            attr = getattr(self, name)
        except AttributeError:
            return default
        if callable(attr):
            return attr(obj)
        return attr

    # override the standard django code to include image
    def _urls(self, page, protocol, domain):
        urls = []
        latest_lastmod = None
        all_items_lastmod = True  # track if all items have a lastmod
        for item in self.paginator.page(page).object_list:
            loc = "%s://%s%s" % (protocol, domain, self.__get("location", item))
            priority = self.__get("priority", item)
            lastmod = self.__get("lastmod", item)
            if all_items_lastmod:
                all_items_lastmod = lastmod is not None
                if all_items_lastmod and (
                    latest_lastmod is None or lastmod > latest_lastmod
                ):
                    latest_lastmod = lastmod
            # images code
            image = item.image
            image.location = "%s://%s%s" % (protocol, domain, image.file.url)
            image.title = item.name  # replace existing title so no ref at front
            url_info = {
                "item": item,
                "location": loc,
                "lastmod": lastmod,
                "changefreq": self.__get("changefreq", item),
                "priority": str(priority if priority is not None else ""),
                "image": image,
            }
            #
            urls.append(url_info)
        if all_items_lastmod and latest_lastmod:
            self.latest_lastmod = latest_lastmod
        return urls
