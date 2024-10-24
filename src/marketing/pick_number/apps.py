from django.apps import AppConfig


class PickNumberConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'marketing.pick_number'

    def ready(self):
        import marketing.pick_number.signals
