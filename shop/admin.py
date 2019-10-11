from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from shop.models import Category, Item, Contact, Enquiry


class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(Category)


admin.site.register(Category, CategoryAdmin)
admin.site.register(Item)
admin.site.register(Contact)
admin.site.register(Enquiry)
