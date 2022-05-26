from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect

from carts.models import Cart, CartItem
from store.models import Product


def _cart_id(request):
    session = request.session.session_key
    if not session:
        session = request.session.create()

    return session


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    try:
        cart_obj = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart_obj = Cart.objects.create(
            cart_id=_cart_id(request)
        )
        cart_obj.save()

    try:
        cart_item = CartItem.objects.get(product=product, cart=cart_obj)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart_obj
        )
        cart_item.save()

    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    try:
        cart_obj = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart_obj, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items
    }
    return render(request, 'store/cart.html', context)
