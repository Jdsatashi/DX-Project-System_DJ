from django.db import models
from django.db.models import F, Sum, FloatField

from account.models import User
from marketing.order.models import OrderDetail, Order
from marketing.price_list.models import PriceList
from utils.helpers import self_id


# Create your models here.
class EventNumber(models.Model):
    id = models.CharField(max_length=16, primary_key=True, unique=True, editable=False)
    name = models.CharField(max_length=255, null=False)
    price_list = models.ForeignKey(PriceList, null=True, on_delete=models.CASCADE, related_name='event_number')
    date_start = models.DateField()
    date_close = models.DateField()
    range_number = models.IntegerField()
    limit_repeat = models.IntegerField(default=1)
    point_exchange = models.FloatField(default=1)
    status = models.CharField(max_length=24, default='active')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not self.pk:
            self.id = self_id('EVN', EventNumber, 4)
        super().save(*args, **kwargs)
        try:
            if is_new:
                for num in range(1, self.range_number + 1):

                    NumberList.objects.create(
                        number=num,
                        repeat_count=self.limit_repeat,
                        event=self
                    )
        except Exception as e:
            self.delete()


class NumberList(models.Model):
    id = models.CharField(max_length=24, primary_key=True, unique=True, editable=False)
    number = models.IntegerField()
    repeat_count = models.IntegerField()
    event = models.ForeignKey(EventNumber, on_delete=models.CASCADE, related_name='number_list')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.event} - {self.number}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.id = f"{self.event.id}_{self.number}"
        super().save(*args, **kwargs)


class UserJoinEvent(models.Model):
    id = models.CharField(max_length=32, primary_key=True, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_join_event')
    event = models.ForeignKey(EventNumber, on_delete=models.CASCADE, related_name='user_join_event')

    total_point = models.FloatField(default=0)
    used_point = models.FloatField(default=0)
    bonus_point = models.FloatField(default=0)

    turn_pick = models.IntegerField(default=0)
    turn_selected = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.event} - {self.user}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.id = f"{self.event.id}_{self.user}"
        super().save(*args, **kwargs)


class NumberSelected(models.Model):
    user_event = models.ForeignKey(UserJoinEvent, on_delete=models.CASCADE, related_name='number_selected')
    number = models.ForeignKey(NumberList, on_delete=models.CASCADE, related_name='number_selected')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_event', 'number')  # Adding unique constraint

    def save(self, *args, **kwargs):
        self.validate_unique(exclude=None)
        super().save(*args, **kwargs)


def calculate_point_query(user, date_start, date_end, price_list=None):
    print(f"Input data: {user, date_start, date_end}")
    filters = {
        'order_id__client_id': user,
        'order_id__date_get__gte': date_start,
        'order_id__date_get__lte': date_end
    }

    if price_list:
        filters['product_id__productprice__price_list'] = price_list

    total_points = OrderDetail.objects.filter(
        **filters
    ).annotate(
        order_point=F('order_quantity') * F('product_id__productprice__point') / F(
            'product_id__productprice__quantity_in_box')
    ).aggregate(total_point=Sum('order_point', output_field=FloatField()))['total_point'] or 0
    print(f"Test total point: {total_points}")
    return total_points
