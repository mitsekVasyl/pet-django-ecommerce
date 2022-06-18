from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator

from category.models import Category
from orders.models import OrderProduct
from store.forms import ReviewForm
from store.models import Product, ReviewRating

PRODUCTS_COUNT_ON_STORE_PAGE = 3


def store(request, category_slug=None):
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.all().filter(category=category).order_by('id')
    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')

    paginator = Paginator(products, PRODUCTS_COUNT_ON_STORE_PAGE)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    products_count = products.count()

    context = {
        'products': paged_products,
        'products_count': products_count,
    }
    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    single_product = Product.objects.get(slug=product_slug, category__slug=category_slug)

    try:
        orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product).exists()
    except OrderProduct.DoesNotExist:
        orderproduct = None

    # get reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    context = {
        'single_product': single_product,
        'orderproduct': orderproduct,
        'reviews': reviews,
    }
    return render(request, 'store/product_detail.html', context)


def search(request):
    products = None
    products_count = 0
    keyword = request.GET.get('keyword')
    if keyword:
        products = Product.objects.filter(product_name__icontains=keyword)
        products_count = products.count()

    context = {
        "products": products,
        'products_count': products_count,
    }
    return render(request, 'store/store.html', context)


@login_required
def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == "POST":
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated')

        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            print(form)
            print(form.cleaned_data['rating'])
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()

                messages.success(request, 'Thank you! Your review has been submitted')

        return redirect(url)
