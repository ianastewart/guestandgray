from datetime import datetime
from django.utils.timezone import now
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum
from shop.models import Invoice

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
