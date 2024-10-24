from django.apps import AppConfig


class OrderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'marketing.order'

    def ready(self):
        import marketing.order.signals
