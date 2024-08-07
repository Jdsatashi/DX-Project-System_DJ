from django.db.models.signals import post_save, pre_delete, m2m_changed
from django.dispatch import receiver

from app.logs import app_log
from marketing.order.models import Order, SeasonalStatistic, SeasonalStatisticUser
from marketing.pick_number.models import EventNumber, UserJoinEvent, calculate_point_query, NumberSelected

"""
@receiver(post_save, sender=Order)
def update_user_join_event(sender, instance, created, **kwargs):
    app_log.info(f"Signals is working")
    date_get = instance.date_get

    # Lấy tất cả các EventNumber có date_start <= date_get <= date_close
    events = EventNumber.objects.filter(date_start__lte=date_get, date_close__gte=date_get)
    if events.exists():
        app_log.info(f"Update event")
        for event in events:
            app_log.info(f"Handle calculate point for event - {event}")
            user_join = UserJoinEvent.objects.filter(event=event, user=instance.client_id).first()
            if user_join:
                app_log.info(user_join)
                total_point = calculate_point_query(user_join.user, event.date_start, event.date_close, event.price_list)
                user_join.total_point = total_point + user_join.bonus_point
                user_join.turn_pick = user_join.total_point // event.point_exchange - user_join.turn_selected
                app_log.info(f"Testing turn pick: {user_join.turn_pick}")
                user_join.save()
            else:
                continue
"""




# @receiver(post_save, sender=EventNumber)
# def update_user_eventnumber(sender, instance: EventNumber, created, **kwargs):
#     print(f"Signal update eventnumber working")
# stats_users = SeasonalStatisticUser.objects.filter(season_stats__event_number=instance)
# print(f"Check users: {stats_users}")
# for stats_user in stats_users:
#     print(f"Looping user join event: {stats_user}")
#     turn_per_point = stats_user.turn_per_point
#     turn_pick = stats_user.turn_pick
#     total_point = stats_user.total_point
#     user_event = UserJoinEvent.objects.create(
#         user=stats_user.user, event=instance, total_point=total_point, turn_pick=turn_pick, turn_per_point=turn_per_point)
#     print(user_event)

@receiver(pre_delete, sender=UserJoinEvent)
def update_repeat_count(sender, instance, **kwargs):
    app_log.info(f"Auto update repeat_count")
    number_selected = NumberSelected.objects.filter(user_event=instance)
    app_log.info(f"Check number user was selected: {number_selected}")
    for number_sel in number_selected:
        app_log.info(f"Check number user re selected: {number_sel.number.number}")
        number_list = number_sel.number
        number_list.repeat_count += 1
        number_list.save()
    number_selected.delete()
