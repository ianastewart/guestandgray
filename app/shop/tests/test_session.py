import pytest
from datetime import datetime
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import User
from mixer.backend.django import mixer
from shop.session import *
from shop.models import Address, Item, InvoiceCharge, Contact


@pytest.fixture(name="user_request", scope="session")
def user_request():
    class Request:
        def __init__(self):
            self.request = RequestFactory().get("/")
            SessionMiddleware().process_request(self.request)
            # self.request.session.save()

    return Request()


@pytest.fixture
def set_up(db):
    address1 = mixer.blend(Address, pk=1)
    mixer.blend(Contact, company="contact_one", main_address=address1, pk=1)
    address2 = mixer.blend(Address, pk=2)
    mixer.blend(Contact, company="contact_two", main_address=address2, pk=2)
    mixer.blend(Item, name="Item_one", sale_price=Decimal(100), pk=1)
    mixer.blend(Item, name="Item_two", sale_price=Decimal(200), pk=2)
    mixer.blend(Item, name="Item_three", sale_price=Decimal(300), pk=3)


class TestSessions:
    def test_session_is_empty(self, user_request):
        request = user_request.request
        cart_clear(request)
        assert len(cart_items(request)) == 0
        assert len(cart_charges(request)) == 0

    def test_add_get_remove_items(self, user_request, set_up):
        request = user_request.request
        item = Item.objects.get(pk=1)
        cart_add_item(request, item)
        assert item.state == Item.State.RESERVED
        item = Item.objects.get(pk=2)
        cart_add_item(request, item)
        item = Item.objects.get(pk=3)
        cart_add_item(request, item)
        assert len(cart_items(request)) == 3
        item = cart_get_item(request, pk=2)
        assert item.name == "Item_two"
        cart_remove_item(request, pk=2)
        assert item.state == Item.State.ON_SALE
        assert len(cart_items(request)) == 2
        item = cart_get_item(request, pk=2)
        assert item is None

    def test_add_get_remove_charges(self, user_request, db):
        request = user_request.request
        cart_clear(request)
        cart_add_charge(request, mixer.blend(InvoiceCharge, amount=Decimal(20)))
        charge = InvoiceCharge(pk=1, amount=Decimal(20))
        cart_add_charge(request, charge)
        cart_add_charge(request, mixer.blend(InvoiceCharge, amount=Decimal(20)))
        assert len(cart_charges(request)) == 3
        charge = cart_get_charge(request, pk=1)
        assert charge.amount == Decimal(20)
        cart_remove_charge(request, pk=1)
        assert len(cart_charges(request)) == 2
        charge = cart_get_charge(request, 1)
        assert charge is None

    def test_can_add_and_get_buyer(self, user_request, set_up):
        request = user_request.request
        cart_clear(request)
        buyer = Contact.objects.get(pk=1)
        cart_add_buyer(request, buyer)
        assert cart_get_buyer(request) == buyer
        buyer2 = Contact.objects.get(pk=2)
        cart_add_buyer(request, buyer2)
        assert cart_get_buyer(request) == buyer2

    def test_invoice_creation_and_reverse(self, user_request, set_up):
        request = user_request.request
        cart_clear(request)
        cart_add_item(request, Item.objects.get(pk=1))
        cart_add_item(request, Item.objects.get(pk=2))
        cart_add_item(request, Item.objects.get(pk=3))
        cart_add_charge(request, mixer.blend(InvoiceCharge, amount=Decimal(20)))
        buyer = Contact.objects.get(pk=1)
        cart_add_buyer(request, buyer)
        date = datetime(2019, 12, 19)
        inv = cart_session_to_invoice(request, date)
        assert inv.total == Decimal(620)
        assert inv.proforma == False
        assert inv.buyer == buyer
        for item in inv.item_set.all():
            assert item.state == Item.State.SOLD
        cart_invoice_to_session(request, inv)
        assert len(cart_items(request)) == 3
        assert len(cart_charges(request)) == 1
        assert cart_get_buyer(request) == buyer
