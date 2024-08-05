from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SeasonalStatisticUser, update_season_stats_users


@receiver(post_save, sender=SeasonalStatisticUser)
def my_custom_function(sender, instance, created, **kwargs):
    if created:
        print("A new SeasonalStatisticUser has been created!")
        # Thực hiện bất kỳ logic nào bạn cần tại đây
        update_instance = update_season_stats_users(instance)
        update_instance.save()
