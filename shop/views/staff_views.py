import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


class StaffHomeView(LoginRequiredMixin, TemplateView):
    template_name = "shop/staff_home.html"
