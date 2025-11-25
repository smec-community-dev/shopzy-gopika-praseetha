from User.models import CustomerNotification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def notify_order_status(order, new_status):
    status_map = {
        "processing": ("Order Processing", "Your order is now being processed."),
        "shipped": ("Order Shipped", "Your order is on the way!"),
        "delivered": ("Order Delivered", "Your order has been delivered."),
        "cancelled": ("Order Cancelled", "Your order has been cancelled."),
    }

    if new_status not in status_map:
        return

    title, message = status_map[new_status]

    # Save to DB
    CustomerNotification.objects.create(
        user=order.user,
        order=order,
        title=title,
        message=message,
        notification_type=f"order_{new_status}"
    )

    # Send through WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{order.user.id}",
        {
            "type": "send_notification",
            "message": {
                "title": title,
                "message": message,
                "order_id": order.id,
                "status": new_status,
            }
        }
    )
