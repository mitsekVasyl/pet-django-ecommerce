from django.contrib import admin

from store.models import Product, Variation, ReviewRating


class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('product_name',)}
    list_display = ('product_name', 'price', 'stock', 'category', 'modified_date', 'is_available')


class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active', 'create_date')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'variation_value', 'is_active')


class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'subject', 'rating', 'review', 'created_at', 'updated_at', 'status')
    list_editable = ('status',)
    list_filter = ('rating', 'created_at', 'updated_at', 'status')


admin.site.register(Product, ProductAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(ReviewRating, ReviewRatingAdmin)
