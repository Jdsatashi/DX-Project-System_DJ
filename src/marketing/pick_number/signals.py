from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from marketing.order.models import Order
from marketing.pick_number.models import EventNumber, UserJoinEvent, calculate_point_query, NumberSelected


@receiver(post_save, sender=Order)
def update_user_join_event(sender, instance, created, **kwargs):
    print(f"Signals is working")
    date_get = instance.date_get

    # Lấy tất cả các EventNumber có date_start <= date_get <= date_close
    events = EventNumber.objects.filter(date_start__lte=date_get, date_close__gte=date_get)
    if events.exists():
        for event in events:
            user_join = UserJoinEvent.objects.filter(event=event, user=instance.client_id).first()

            print(user_join)
            total_point = calculate_point_query(user_join.user, event.date_start, event.date_close, event.price_list)
            user_join.total_point = total_point + user_join.bonus_point
            user_join.turn_pick = user_join.total_point // event.point_exchange - user_join.turn_selected
            print(f"Testing turn pick: {user_join.turn_pick}")
            user_join.save()


@receiver(pre_delete, sender=UserJoinEvent)
def update_repeat_count(sender, instance, **kwargs):
    number_selected = NumberSelected.objects.filter(user_event=instance)
    for number_sel in number_selected:
        number_list = number_sel.number
        number_list.repeat_count += 1
        number_list.save()
    number_selected.delete()
