import requests
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from carts.models import Cart, CartItem
from carts.views import _cart_id
from django_eccomerce.settings import EMAIL_HOST_USER
from orders.models import Order
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            password = form.cleaned_data['password']
            username = f"{first_name[0]}{last_name}".lower()  # TODO: add username to form

            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password=password
            )
            user.phone_humber = phone_number
            user.save()

            # Create user profile
            profile = UserProfile()
            profile.user_id = user.id
            profile.save()

            # User activation
            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })
            send_email = EmailMessage(mail_subject, message, to=[email], from_email=EMAIL_HOST_USER)
            send_email.send()
            messages.success(request, "Thank you for registration. Please visit your mail box "
                                      "and activate your account.")
            return redirect('login')

    else:
        form = RegistrationForm()

    context = {
        'form': form
    }
    return render(request, 'accounts/register.html', context)


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account is activated!")
        return redirect('login')

    else:
        messages.success(request, "Invalid activation link.")
        return redirect('register')


def login(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)
        if user is not None:
            try:
                cart_obj = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exist = CartItem.objects.filter(cart=cart_obj).exists()
                if is_cart_item_exist:
                    cart_items = CartItem.objects.filter(cart=cart_obj)

                    # get product variations by car_id
                    product_variations = []
                    for item in cart_items:
                        existing_variation = item.variations.all()
                        product_variations.append(list(existing_variation))

                    # get cart items from the user
                    cart_items = CartItem.objects.filter(user=user)
                    existing_variations = []
                    ids = []
                    for item in cart_items:
                        existing_variation = item.variations.all()
                        existing_variations.append(list(existing_variation))
                        ids.append(item.id)

                    for pr in product_variations:
                        if pr in existing_variations:
                            index = existing_variations.index(pr)
                            item_id = ids[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_items = CartItem.objects.filter(cart=cart_obj)
                            for item in cart_items:
                                item.user = user
                                item.save()
            except:
                pass

            auth.login(request, user)
            messages.success(request, "You are logged in now!")
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(p.split('=') for p in query.split('&'))
                if 'next' in params:
                    next_page = params['next']
                    return redirect(next_page)

            except:
                return redirect('dashboard')

        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')

    return render(request, 'accounts/login.html')


@login_required(login_url='login')
def dashboard(request):
    orders = Order.objects.filter(user_id=request.user.id, is_ordered=True).order_by('-created_at')
    orders_count = orders.count()
    context = {
        'orders_count': orders_count
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def edit_profile(request):
    current_user = request.user
    user_profile = get_object_or_404(UserProfile, user=current_user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=current_user)
        profile_form = UserProfileForm(request.POST, instance=user_profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile has been updated.')
            return redirect('dashboard')

    else:
        user_form = UserForm(instance=current_user)
        profile_form = UserProfileForm(instance=user_profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def my_orders(request):
    orders = Order.objects.filter(user_id=request.user.id, is_ordered=True).order_by('-created_at')
    context = {
        'orders': orders
    }
    return render(request, 'accounts/my_orders.html', context)


@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, "Logged out")
    return redirect('login')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # reset password
            current_site = get_current_site(request)
            mail_subject = 'Reset your password.'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })
            send_email = EmailMessage(mail_subject, message, to=[email], from_email=EMAIL_HOST_USER)
            send_email.send()

            messages.success(request, f'Password reset email has been sent to {email}.')
            return redirect('login')

        else:
            messages.error(request, 'Account does not exists')
            return redirect('forgot_password')

    return render(request, 'accounts/forgot_password.html')


def validate_reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset you password.')
        return redirect('reset_password')

    else:
        messages.error(request, 'This link has been expired')
        return redirect('login')


def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password has been reset. You can log in now.')
            return redirect('login')

        else:
            messages.error(request, 'Password does not match.')
            return redirect('reset_password')

    return render(request, 'accounts/reset_password.html')
