from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(user_signed_up)
def set_customer_role_on_social_signup(request, user, **kwargs):
    """
    When a user signs up using Google or any social login,
    automatically set their role to 'customer'.
    """
    user.role = "customer"   # force role as customer
    user.save()
    print("✔ Customer role set for social login user:", user.username)
