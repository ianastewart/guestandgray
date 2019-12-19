from django.utils.timezone import now
from django.shortcuts import redirect
from decimal import Decimal
from shop.models import Invoice, Item, InvoiceCharge, Contact

# Purchase creation functions


def clear_data(request):
    """ Clear session variables """
    request.session["posts"] = []


def update_data(index, request, form):
    """
    Save cleaned data in session at index
    """
    posts = request.session["posts"]
    cleaned_data = form.cleaned_data
    cleaned_data["path"] = request.path
    cleaned_data["form_class"] = form.__class__.__name__
    if index >= len(posts):
        posts.append(cleaned_data)
    else:
        # Don't override the orignal path if doing an ajax update
        cleaned_data["path"] = posts[index]["path"]
        posts[index] = cleaned_data
    request.session["posts"] = posts


def get_data(index, request):
    """
    Return cleaned_data for index else None
    """
    posts = request.session.get("posts", None)
    if posts:
        if 0 <= index < len(posts):
            if not (
                posts[index].get("invalid", False) or posts[index].get("deleted", False)
            ):
                return posts[index]
    return None


def delete_data(index, request):
    """
    Delete post data for index
    """
    posts = request.session["posts"]
    if index < len(posts):
        posts[index]["deleted"] = True
        index += 1
        request.session.modified = True


def invalidate_data(index, request):
    """
    Invalidate post data for index
    Used when child profile is changed to adult profile or vice versa
    """
    posts = request.session["posts"]
    if index < len(posts):
        posts[index]["invalid"] = True
        request.session.modified = True


def last_index(request):
    """
    return the last used index
    """
    return len(request.session["posts"]) - 1


def next_index(index, request):
    """
    Return next index, skipping deleted records, but not invalid records because we overwrite those
    """
    posts = request.session["posts"]
    i = index
    while i + 1 < len(posts):
        i += 1
        if not posts[i].get("deleted", False):
            return i
    return len(posts)


def back(index, request):
    """
    Return previous path, skipping deleted and invalid records
    """
    posts = request.session["posts"]
    while index > 0:
        index -= 1
        if is_valid(posts[index]):
            return posts[index]["path"]
    return posts[0]["path"]


def is_valid(data):
    return (
        None
        if not data
        else not (data.get("deleted", False) or data.get("invalid", False))
    )


def update_kwargs(view, kwargs):
    """
    Update the forms kwargs with stored POST data if it exists
    """
    data = post_data(view)
    if data:
        kwargs.update({"data": data})
    return kwargs


def post_data(view):
    """ Return POST data if it exists for a view"""
    if view.request.method == "GET":
        return get_data(view.index, view.request)
    return None


def redirect_next(index, request, default):
    """ Redirect to next page form if data exists for it else to the default """
    posts = request.session["posts"]
    max_index = len(posts) - 1
    i = index
    while i < max_index:
        i += 1
        if is_valid(posts[i]):
            return redirect(posts[i]["path"])
    return redirect(default, i + 1)


# Stack handling for ajax calls


def new_stack(request):
    request.session["stack"] = []
    request.session.modified = True


def push(request, url):
    stack = request.session.get("stack", None)
    if stack is None:
        stack = []
    stack.append(url)
    request.session["stack"] = stack
    request.session.modified = True


def pop(request):
    try:
        value = request.session["stack"].pop()
        request.session.modified = True
    except IndexError:
        value = None
    return value


# Cart handling
# cart can contain a list of items, invoicecharges and a single buyer (contact)
# the price of items in the list can be updated but changes are not saved in the database


def cart_clear(request):
    request.session["cart"] = []
    request.session.modified = True


def cart_empty(request):
    """ Restore state of any items in cart then clear it """
    cart = request.session.get("cart")
    if cart:
        items = cart_items(request)
        for item in items:
            item.state = Item.State.ON_SALE
            item.save()
    cart_clear(request)


def cart_add_item(request, item):
    if not cart_get_item(request, item.pk):
        item.agreed_price = Decimal(0)
        if item.sale_price is not None:
            item.agreed_price = item.sale_price
        else:
            item.sale_price = Decimal(0)
        item.state = Item.State.RESERVED
        item.save()
        cart = _cart(request)
        cart.append(item)
        request.session["cart"] = cart
        request.session.modified = True


def cart_get_item(request, pk):
    return _cart_get_object(request, pk, Item)


def cart_remove_item(request, pk):
    item = cart_get_item(request, pk)
    if item:
        _cart(request).remove(item)
        item.state = Item.State.ON_SALE
        item.save()
        request.session.modified = True


def cart_items(request):
    return _cart_contents(request, Item)


def cart_add_charge(request, charge):
    if not cart_get_charge(request, charge.pk):
        cart = _cart(request)
        cart.append(charge)
        request.session["cart"] = cart
        request.session.modified = True


def cart_get_charge(request, pk):
    return _cart_get_object(request, pk, InvoiceCharge)


def cart_remove_charge(request, pk):
    charge = cart_get_charge(request, pk)
    if charge:
        _cart(request).remove(charge)
        request.session.modified = True


def cart_charges(request):
    return _cart_contents(request, InvoiceCharge)


def cart_add_buyer(request, contact):
    existing = cart_get_buyer(request)
    if existing:
        _cart(request).remove(existing)
    _cart(request).append(contact)
    request.session.modified = True


def cart_get_buyer(request):
    count = 0
    for thing in _cart(request):
        if thing._meta.object_name == Contact._meta.object_name:
            count += 1
            result = thing
    if count:
        if count > 1:
            raise ValueError("Muliple buyers stored in session")
        return result
    return None


def cart_session_to_invoice(request, date=None):
    """
    Create an invoice from cart session data
    If date is none, its a proforma invoice
    """

    if date:
        proforma = False
        number = Invoice.next_number()
    else:
        date = now()
        proforma = True
        number = 0
    invoice = Invoice(date=date, proforma=proforma, number=number)
    invoice.buyer = cart_get_buyer(request)
    invoice.address = invoice.buyer.main_address
    invoice.save()
    total = Decimal(0)
    for item in cart_items(request):
        total += item.agreed_price
        item.sale_price = item.agreed_price
        item.state = Item.State.SOLD
        item.invoice = invoice
        item.archive = True
        item.save()
    for charge in cart_charges(request):
        total += charge.amount
        charge.invoice = invoice
        charge.save()
    invoice.total = total
    invoice.save()
    cart_clear(request)
    return invoice


def cart_invoice_to_session(request, invoice):
    """
    Create session representation of a proforma invoice
    Then delete the invoice and charges
    """
    cart_clear(request)
    for item in invoice.item_set.all():
        cart_add_item(request, item)
    for charge in invoice.invoicecharge_set.all():
        cart_add_charge(request, charge)
        charge.delete()
    cart_add_buyer(request, invoice.buyer)
    invoice.delete()


# private support code
def _cart(request):
    cart = request.session.get("cart", None)
    if cart is None:
        cart = cart_clear(request)
    return cart


def _cart_get_object(request, pk, cls):
    pk = int(pk)
    cart = _cart(request)
    if cart:
        for thing in cart:
            if thing.pk == pk and thing._meta.object_name == cls._meta.object_name:
                return thing
    return None


def _cart_contents(request, cls):
    return [
        obj for obj in _cart(request) if obj._meta.object_name == cls._meta.object_name
    ]
