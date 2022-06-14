import datetime

from django.shortcuts import render, redirect

from carts.models import CartItem
from orders.forms import OrderForm
from orders.models import Order


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
            return redirect('checkout')

    else:
        return redirect('checkout')
