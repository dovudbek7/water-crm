from django.contrib import admin

from core.models import ActionLog, Employee, Order, OrderItem, Product, Shop, ShopDeposit, UserProfile


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


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_primary', 'phone_secondary', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_primary', 'phone_secondary')


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('actor_name', 'employee', 'action_type', 'target_model', 'object_label', 'created_at')
    list_filter = ('action_type', 'created_at')
    search_fields = ('employee__user__username', 'actor_name', 'message', 'object_label')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_primary', 'phone_secondary', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_primary', 'phone_secondary')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'order_date', 'order_type', 'delivery_status', 'total_amount', 'paid_amount', 'created_by', 'courier')
    list_filter = ('order_date', 'shop', 'order_type', 'delivery_status')
    search_fields = ('shop__name', 'note', 'delivery_note')
    inlines = [OrderItemInline]
