from django.apps import AppConfig


class LivestreamConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'marketing.livestream'

    def ready(self):
        import marketing.livestream.signals
