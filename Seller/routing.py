# Seller/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/seller/notifications/', consumers.SellerNotificationConsumer.as_asgi()),
]