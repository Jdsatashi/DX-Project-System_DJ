from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import SeasonalStatisticUser, update_season_stats_users, SeasonalStatistic
from ..pick_number.models import UserJoinEvent


@receiver(post_save, sender=SeasonalStatisticUser)
def update_stats_user(sender, instance, created, **kwargs):
    print(f"Signal SeasonalStatisticUser working")
    if created:
        print("A new SeasonalStatisticUser has been created!")
        # Thực hiện bất kỳ logic nào bạn cần tại đây
        update_instance = update_season_stats_users(instance)
        update_instance.save()
    user_join_events = UserJoinEvent.objects.filter(user=instance.user, event__table_point=instance.season_stats)
    print(f"Test user join events: {user_join_events}")
    for user_join_event in user_join_events:
        print(f"Loop user join event: {user_join_event}")
        user_join_event.turn_per_point = instance.turn_per_point if instance.turn_per_point else user_join_event.turn_per_point
        user_join_event.turn_pick = instance.turn_pick if instance.turn_pick else user_join_event.turn_pick
        user_join_event.total_point = instance.total_point if instance.total_point else user_join_event.total_point
        user_join_event.save()


@receiver(m2m_changed, sender=SeasonalStatistic.users.through)
def handle_user_perm_change(sender, instance: SeasonalStatistic, action, reverse, model, pk_set, **kwargs):
    stats_users = SeasonalStatisticUser.objects.filter(season_stats=instance)
    for stats_user in stats_users:
        user_join_event = UserJoinEvent.objects.filter(user=stats_user.user, event__table_point=instance)
        user_join_event.turn_per_point = stats_user.turn_per_point
        user_join_event.turn_pick = stats_user.turn_pick
        user_join_event.total_point = stats_user.total_point
        user_join_event.save()
    user_ids = stats_users.values_list('user_id', flat=True).distinct()
    UserJoinEvent.objects.filter(event__table_point=instance).exclude(user_id__in=user_ids).delete()


# @receiver(post_save, sender=SeasonalStatisticUser)
# def update_event_number(sender, instance: SeasonalStatisticUser, created, **kwargs):
#
