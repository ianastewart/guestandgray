from decimal import Decimal
from typing import Any, Dict
from django.views.generic import TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from shop.models import Item, InvoiceCharge
from shop.forms import CartPriceForm, InvoiceChargeForm, InvoiceDateForm
from table_manager.views import AjaxCrudView
from shop.session import (
    cart_items,
    cart_remove_item,
    cart_clear,
    cart_get_item,
    cart_charges,
    cart_add_charge,
    cart_remove_charge,
)


class CartContentsView(LoginRequiredMixin, TemplateView):
    template_name = "shop/cart_contents.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["price_path"] = reverse("cart_price", kwargs={"pk": 0})
        context["add_charge"] = reverse("cart_add_charge")
        CartContentsView.invoice_context(
            cart_items(self.request), cart_charges(self.request), context
        )
        return context

    @classmethod
    def invoice_context(cls, items, charges, context):
        """ Adds context data needed to display an invoice table"""
        total = Decimal(0)
        for item in items:
            total += item.agreed_price
        for charge in charges:
            total += charge.amount
        context["items"] = items
        context["charges"] = charges
        context["total"] = total

    def post(self, request, **kwargs):
        if "empty" in request.POST:
            cart_clear(request)
        else:
            for k in request.POST:
                if "remove" in k or "uncharge" in k:
                    bits = k.split("_")
                    if bits[0] == "remove":
                        cart_remove_item(request, bits[1])
                    else:
                        cart_remove_charge(request, bits[1])
                    break
        return redirect("cart_contents")


class CartPriceView(LoginRequiredMixin, AjaxCrudView):
    template_name = "shop/includes/partial_cart_price.html"
    form_class = CartPriceForm

    def get_form(self):
        return self.form_class(
            {
                "sale_price": self.object.sale_price,
                "agreed_price": self.object.agreed_price,
            }
        )

    def get_object(self, **kwargs):
        # get object from session
        pk = kwargs.get("pk", None)
        self.object = cart_get_item(self.request, pk)
        if not hasattr(self.object, "agreed_price"):
            self.object.agreed_price = self.object.sale_price
        return self.object

    def save_object(self, **kwargs):
        # save object to session
        pk = kwargs.get("pk", None)
        item = cart_get_item(self.request, pk)
        item.agreed_price = self.form.cleaned_data["agreed_price"]
        self.request.session.modified = True
        super().save_object(**kwargs)

    def get_context_data(self):
        context = super().get_context_data()
        context["submit_path"] = self.request.path
        return context


class CartAddChargeView(LoginRequiredMixin, AjaxCrudView):
    form_class = InvoiceChargeForm
    template_name = "shop/includes/partial_cart_charge.html"

    def save_object(self, **kwargs):
        data = self.form.cleaned_data
        charge = InvoiceCharge.objects.create(
            charge_type=data["charge_type"],
            description=data["description"],
            amount=data["amount"],
        )
        cart_add_charge(self.request, charge)

    def get_context_data(self):
        context = super().get_context_data()
        context["submit_path"] = self.request.path
        return context


class CartCheckoutView(LoginRequiredMixin, FormView):
    template_name = "shop/cart_checkout.html"
    form_class = InvoiceDateForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        CartContentsView.invoice_context(
            cart_items(self.request), cart_charges(self.request), context
        )
        context["urls"] = {
            "lookup": reverse("contact_lookup"),
            "create": reverse("contact_create"),
        }
        return context

    def post(self, request, **kwargs):
        return redirect("cart_contents")
