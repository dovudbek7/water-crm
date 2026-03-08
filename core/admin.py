from django.contrib import admin

from core.models import Order, OrderItem, Product, Shop, ShopDeposit


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'created_at')
    search_fields = ('name',)


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_primary', 'phone_secondary', 'created_at')
    search_fields = ('name', 'address', 'phone_primary', 'phone_secondary', 'note')


@admin.register(ShopDeposit)
class ShopDepositAdmin(admin.ModelAdmin):
    list_display = ('shop', 'date', 'amount', 'note', 'created_at')
    list_filter = ('date', 'shop')
    search_fields = ('shop__name', 'note')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'order_date', 'total_amount', 'paid_amount', 'created_by')
    list_filter = ('order_date', 'shop')
    search_fields = ('shop__name', 'note')
    inlines = [OrderItemInline]
