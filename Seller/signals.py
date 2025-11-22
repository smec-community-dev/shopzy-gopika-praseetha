from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from Seller.models import Seller

@receiver(user_signed_up)
def set_seller_role(request, user, **kwargs):
    """
    Runs when a new user signs up via Google login.
    """
    # Set role
    user.role = "seller"
    user.save()

    # Create Seller profile
    Seller.objects.create(
        user=user,
        shop_name=user.username + "'s Shop",
        address="",
        website="",
        profile_image=""  # optional; leave blank if no profile picture from Google
    )
