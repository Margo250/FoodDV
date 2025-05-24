from django.contrib import admin
from .models import Category, Product
from .models import Order, OrderItem

admin.site.register(Category)
admin.site.register(Product)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'created_at', 'total']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'user__username', 'phone', 'address']
    inlines = [OrderItemInline]

admin.site.register(OrderItem)
