from django.apps import AppConfig


class SellerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Seller'


    def ready(self):
        # Import your signals to ensure the signal receivers are registered
        import Seller.signals

