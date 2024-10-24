from django.apps import AppConfig


class SaleStatisticConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'marketing.sale_statistic'

    def ready(self):
        import marketing.sale_statistic.signals
