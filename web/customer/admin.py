from django.contrib import admin
from .models import Customer, Address, Cart, OrderItem, Payment, Order,CartItem

# Register the models in the admin site
admin.site.register(Customer)
admin.site.register(Address)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Payment)
admin.site.register(Order)
admin.site.register(OrderItem)