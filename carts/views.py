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


def cart(request):
    return render(request, 'store/cart.html')
