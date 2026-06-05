import logging
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import reverse
from django.utils.timezone import now
from django.views.generic import TemplateView, UpdateView

from shop.forms import GlobalSettingsForm
from shop.models import Invoice, GlobalSettings

logger = logging.getLogger(__name__)


class StaffHomeView(LoginRequiredMixin, TemplateView):
    template_name = "shop/staff_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        proforma = Invoice.objects.filter(proforma=True)
        context["count_proforma"] = proforma.count()
        context["value_proforma"] = proforma.aggregate(Sum("total"))["total__sum"]
        unpaid = Invoice.objects.filter(proforma=False, paid=False)
        context["count_unpaid"] = unpaid.count()
        context["value_unpaid"] = unpaid.aggregate(Sum("total"))["total__sum"]
        today = now()
        y = today.year
        m = today.month
        d = today.day
        if m < 4 or (m == 4 and d <= 5):
            y = y - 1
        current_year = datetime(y, m, 5)
        last_year = datetime(y - 1, m, 5)
        sales_this = Invoice.objects.filter(
            proforma=False, date__gte=current_year, date__lte=today
        )
        context["count_this"] = sales_this.count()
        context["value_this"] = sales_this.aggregate(Sum("total"))["total__sum"]
        sales_last = Invoice.objects.filter(
            proforma=False, date__gte=last_year, date__lt=current_year
        )
        context["count_last"] = sales_last.count()
        context["value_last"] = sales_last.aggregate(Sum("total"))["total__sum"]
        return context


class GlobalSettingsView(UpdateView):
    template_name = "shop/global_settings.html"
    form_class = GlobalSettingsForm

    def get_object(self):
        return GlobalSettings.record()

    def get_success_url(self) -> str:
        return reverse("staff_home")
