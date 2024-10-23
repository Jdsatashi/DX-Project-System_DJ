from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from app.logs import app_log
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


from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import Order, OrderDetail, OrderDelete, OrderDetailDelete


@receiver(pre_delete, sender=Order)
def backup_order(sender, instance: Order, **kwargs):
    app_log.info(f"backup delete order: {instance.id}")
    try:
        # Backup the Order instance
        order_backup = OrderDelete(
            order_id=instance.id,
            date_get=instance.date_get,
            date_company_get=instance.date_company_get,
            client_id=instance.client_id_id,  # Save the ForeignKey relationship by ID
            date_delay=instance.date_delay,
            list_type=instance.list_type,
            price_list_id=str(instance.price_list_id_id),
            is_so=instance.is_so,
            count_turnover=instance.count_turnover,
            minus_so_box=instance.minus_so_box,
            new_special_offer=str(instance.new_special_offer_id) if instance.new_special_offer else None,
            order_point=instance.order_point,
            order_price=instance.order_price,
            nvtt_id=instance.nvtt_id,
            npp_id=instance.npp_id,
            created_by=instance.created_by,
            note=instance.note,
            status=instance.status,
            created_at=instance.created_at
        )
        order_backup.save()
    except Exception as e:
        app_log.error(f"Error when backup order: {e}")


@receiver(pre_delete, sender=OrderDetail)
def backup_order(sender, instance: OrderDetail, **kwargs):
    app_log.info(f"backup delete order detail: {instance.id}")
    try:
        # Backup the Order instance
        detail_backup = OrderDetailDelete(
            order_id=instance.order_id_id,
            product_id=str(instance.product_id_id),
            order_quantity=instance.order_quantity,
            order_box=instance.order_box,
            price_so=instance.price_so,
            note=instance.note,
            product_price=instance.product_price,
            point_get=instance.point_get
        )
        detail_backup.save()
    except Exception as e:
        app_log.error(f"Error when backup order detail: {e}")
# Connect the signal
# pre_delete.connect(backup_order, sender=Order)

# @receiver(post_save, sender=SeasonalStatisticUser)
# def update_event_number(sender, instance: SeasonalStatisticUser, created, **kwargs):
#
