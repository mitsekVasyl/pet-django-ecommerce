from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from carts.models import Cart, CartItem
from store.models import Product, Variation


def _cart_id(request):
    session = request.session.session_key
    if not session:
        session = request.session.create()

    return session


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variations = []

    if request.method == 'POST':
        for variation_category, variation_value in request.POST.items():
            try:
                variation = Variation.objects.get(product=product,
                                                  variation_category__iexact=variation_category,
                                                  variation_value__iexact=variation_value)
                product_variations.append(variation)
            except ObjectDoesNotExist:
                pass

    try:
        cart_obj = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart_obj = Cart.objects.create(
            cart_id=_cart_id(request)
        )
        cart_obj.save()

    is_cart_item_exist = CartItem.objects.filter(product=product, cart=cart_obj).exists()
    if is_cart_item_exist:
        cart_items = CartItem.objects.filter(product=product, cart=cart_obj)

        existing_variations = []
        ids = []
        for item in cart_items:
            existing_variation = item.variations.all()
            existing_variations.append(list(existing_variation))
            ids.append(item.id)

        if product_variations in existing_variations:
            index = existing_variations.index(product_variations)
            item_id = ids[index]
            item = CartItem.objects.get(product=product, id=item_id)
            item.quantity += 1
            item.save()
        else:
            item = CartItem.objects.create(product=product, quantity=1, cart=cart_obj)
            if len(product_variations) > 0:
                item.variations.clear()
                item.variations.add(*product_variations)
            # cart_item.quantity += 1
            item.save()
    else:
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart_obj
        )
        if len(product_variations) > 0:
            cart_item.variations.clear()
            cart_item.variations.add(*product_variations)
        cart_item.save()

    return redirect('cart')


def remove_cart(request, product_id, cart_item_id):
    cart_obj = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart_obj, id=cart_item_id)

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass

    return redirect('cart')


def remove_cart_item(request, product_id, cart_item_id):
    cart_obj = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart_obj, id=cart_item_id)
    cart_item.delete()

    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    tax = None
    grand_total = None

    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart_obj = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart_obj[:1])

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


@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
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
    return render(request, 'store/checkout.html', context)
