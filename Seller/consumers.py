# Seller/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Seller

User = get_user_model()

class SellerNotificationConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def get_seller_id(self, user):
        """Get seller ID from user"""
        if user.is_anonymous:
            return None
        try:
            return user.seller_profile.id
        except Seller.DoesNotExist:
            return None

    async def connect(self):
        user = self.scope["user"]
        seller_id = await self.get_seller_id(user)

        if seller_id:
            self.seller_id = seller_id
            self.room_group_name = f'seller_{self.seller_id}'

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
            print(f"Seller {self.seller_id} connected to notifications")
        else:
            await self.close()

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        print(f"Seller {getattr(self, 'seller_id', 'unknown')} disconnected")

    # Receive message from room group
    async def send_notification(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'id': event['id'],
            'message': event['message'],
            'notification_type': event['notification_type'],
            'data': event['data']
        }))