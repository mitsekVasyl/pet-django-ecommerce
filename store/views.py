from django.shortcuts import render, get_object_or_404

from category.models import Category
from store.models import Product


def store(request, category_slug=None):
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.all().filter(category=category)
    else:
        products = Product.objects.all().filter(is_available=True)

    products_count = products.count()
    context = {
        'products': products,
        'products_count': products_count,
    }
    return render(request, 'store/store.html', context)
