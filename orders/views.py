import datetime
import json

from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string

from carts.models import CartItem
from django_eccomerce.settings import EMAIL_HOST_USER
from orders.forms import OrderForm
from orders.models import Order, Payment, OrderProduct
from store.models import Product


def payments(request):
    current_user = request.user
    body = json.loads(request.body)
    order = Order.objects.get(user=current_user, is_ordered=False, order_number=body['order_id'])

    # store transaction details
    payment = Payment(
        user=current_user,
        payment_id=body['trans_id'],
        payment_method=body['payment_method'],
        amount_paid=order.order_total,
        status=body['status']
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    cart_items = CartItem.objects.filter(user=current_user)
    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = current_user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        # save product variations
        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()

        # reduce quantity of products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # clear a cart
    CartItem.objects.filter(user=current_user).delete()

    # send email to customer
    mail_subject = 'Thank you for your order!'
    message = render_to_string('orders/order_received_email.html', {
        'user': current_user,
        'order': order
    })
    email = current_user.email
    send_email = EmailMessage(mail_subject, message, to=[email], from_email=EMAIL_HOST_USER)
    send_email.send()

    data = {
        'order_number': order.order_number,
        'payment_id': payment.payment_id,
    }

    return JsonResponse(data)


def place_order(request, total=0, quantity=0):
    current_user = request.user

    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order_data = Order()
            order_data.user = current_user
            order_data.first_name = form.cleaned_data.get('first_name')
            order_data.last_name = form.cleaned_data.get('last_name')
            order_data.phone_number = form.cleaned_data.get('phone_number')
            order_data.email = form.cleaned_data.get('email')
            order_data.address_line_1 = form.cleaned_data.get('address_line_1')
            order_data.address_line_2 = form.cleaned_data.get('address_line_2')
            order_data.county = form.cleaned_data.get('county')
            order_data.state = form.cleaned_data.get('state')
            order_data.city = form.cleaned_data.get('city')
            order_data.order_note = form.cleaned_data.get('order_note')
            order_data.order_total = grand_total
            order_data.tax = tax
            order_data.ip = request.META.get('REMOTE_ADDR')
            order_data.save()

            # generate order number
            # TODO: refactor
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            date = datetime.date(yr, mt, dt)
            current_date = date.strftime("%Y%m%d")
            order_number = current_date + str(order_data.id)
            order_data.order_number = order_number
            order_data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total
            }
            return render(request, 'orders/payments.html', context)

    else:
        return redirect('checkout')


def order_complete(request):
    order_number = request.GET.get('order_number')
    payment_id = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity
        context = {
            'order': order,
            'ordered_products': ordered_products,
            'payment_id': payment_id,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)

    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
