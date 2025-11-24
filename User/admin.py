from django.contrib import admin


from User.models import Order, OrderItem, Customer, Review, ReviewImage, Cart, Address

admin.site.register(Customer)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Address)
admin.site.register(Review)
admin.register(ReviewImage)

