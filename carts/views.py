from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from carts.models import Cart, CartItem
from store.models import Product, Variation


def _cart_id(request):
    session = request.session.session_key
    if not session:
        session = request.session.create()

    return session


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variation = []

    if request.method == 'POST':
        for variation_category, variation_value in request.POST.items():
            try:
                variation = Variation.objects.get(product=product,
                                                  variation_category__iexact=variation_category,
                                                  variation_value__iexact=variation_value)
                product_variation.append(variation)
            except ObjectDoesNotExist:
                pass

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


def remove_cart(request, product_id):
    cart_obj = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart_obj)

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')


def remove_cart_item(request, product_id):
    cart_obj = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart_obj)
    cart_item.delete()

    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    tax = None
    grand_total = None

    try:
        cart_obj = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart_obj, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        tax = (2 * total) / 100
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)
