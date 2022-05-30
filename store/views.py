from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator

from category.models import Category
from store.models import Product

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

    context = {
        "single_product": single_product
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
