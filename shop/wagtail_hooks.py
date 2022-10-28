from django.urls import path
from wagtail.admin.menu import MenuItem
from wagtail import hooks
from shop.views.staff_views import StaffHomeView


@hooks.register("register_admin_menu_item")
def register_main_site():
    return MenuItem("Guest & Gray", "/", icon_name="home", order=200000)
