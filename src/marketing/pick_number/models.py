import time

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
        start_time = time.time()
        is_new = self._state.adding
        if not is_new:
            # Validate before updating existing EventNumber
            self.validate_update()

        super().save(*args, **kwargs)

        if is_new:
            self.create_number_list()
        else:
            self.update_number_list()
        print(f"Time complete EventNumber: {time.time() - start_time}")

    def create_number_list(self):
        start_time = time.time()
        for num in range(1, self.range_number + 1):
            NumberList.objects.create(
                number=num,
                repeat_count=self.limit_repeat,
                event=self
            )
        print(f"Time complete create new NumberList: {time.time() - start_time}")

    def update_number_list(self):
        start_time = time.time()
        current_numbers = set(NumberList.objects.filter(event=self).values_list('number', flat=True))
        new_numbers = set(range(1, self.range_number + 1))

        numbers_to_add = new_numbers - current_numbers
        numbers_to_remove = current_numbers - new_numbers

        # Add new numbers
        for num in numbers_to_add:
            NumberList.objects.create(
                number=num,
                repeat_count=self.limit_repeat,
                event=self
            )

        # Update existing numbers' repeat_count
        for num in current_numbers:
            number_list = NumberList.objects.get(event=self, number=num)
            number_list.repeat_count = self.limit_repeat
            number_list.save()

        # Validate and possibly remove numbers
        for num in numbers_to_remove:
            number_list = NumberList.objects.get(event=self, number=num)
            if NumberSelected.objects.filter(number=number_list).exists():
                raise ValueError(f"Cannot reduce range_number, number {num} is already selected.")
            number_list.delete()
        print(f"Time complete update NumberList: {time.time() - start_time}")

    def validate_update(self):
        start_time = time.time()
        current_numbers = set(NumberList.objects.filter(event=self).values_list('number', flat=True))
        new_numbers = set(range(1, self.range_number + 1))

        numbers_to_remove = current_numbers - new_numbers

        # Validate that no selected number is removed
        for num in numbers_to_remove:
            number_list = NumberList.objects.get(event=self, number=num)
            if NumberSelected.objects.filter(number=number_list).exists():
                raise ValueError(f"Cannot reduce range_number, number {num} is already selected.")

        # Validate limit_repeat
        number_selected = NumberSelected.objects.filter(user_event__event=self).values_list('number__number', flat=True)
        smallest_repeat = NumberList.objects.filter(
            event=self,
            number__in=list(number_selected)
        ).order_by('repeat_count').first()
        if smallest_repeat and self.limit_repeat < smallest_repeat.repeat_count:
            raise ValueError(f"Cannot reduce limit_repeat, some numbers have higher repeat count than the new limit.")
        print(f"Time complete Validate before update: {time.time() - start_time}")


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
