import time

from django.db import models, transaction
from django.db.models import F, Sum, FloatField
from rest_framework.exceptions import ValidationError

from account.models import User
from app.logs import app_log
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
        try:
            with transaction.atomic():
                start_time = time.time()
                app_log.debug(f"Start saving EventNumber")
                is_new = self._state.adding
                old_limit_repeat = None
                if not self.id or self.id == '':
                    self.id = self_id('EVN', EventNumber, 4)
                if not is_new:
                    # Lưu giá trị limit_repeat cũ trước khi cập nhật
                    old_event = EventNumber.objects.get(id=self.id)
                    old_limit_repeat = old_event.limit_repeat
                    # Validate before updating existing EventNumber
                    self.validate_update(old_limit_repeat)

                super().save(*args, **kwargs)

                if is_new:
                    self.create_number_list()
                else:
                    self.update_number_list(old_limit_repeat)
                app_log.info(f"Time complete EventNumber: {time.time() - start_time}")
        except Exception as e:
            app_log.error(f"Error in saving EventNumber: {e}")
            raise e

    def create_number_list(self):
        start_time = time.time()
        number_list = [
            NumberList(
                id=f"{self.id}_{num}",
                number=num,
                repeat_count=self.limit_repeat,
                event=self
            )
            for num in range(1, self.range_number + 1)
        ]
        NumberList.objects.bulk_create(number_list)
        app_log.info(f"Time complete create new NumberList: {time.time() - start_time}")

    def update_number_list(self, old_limit_repeat):
        start_time = time.time()
        current_numbers = NumberList.objects.filter(event=self).values_list('number', 'id', 'repeat_count')
        new_numbers = set(range(1, self.range_number + 1))

        current_numbers_dict = {num: {'id': nid, 'repeat_count': rcount} for num, nid, rcount in current_numbers}
        current_numbers_set = set(current_numbers_dict.keys())

        numbers_to_add = new_numbers - current_numbers_set
        numbers_to_remove = current_numbers_set - new_numbers

        app_log.info(f"Test number to add: {numbers_to_add}")
        app_log.info(f"Test number to remove: {numbers_to_remove}")
        start_time2 = time.time()

        # Add new numbers
        number_list_to_add = [
            NumberList(
                number=num,
                repeat_count=self.limit_repeat,
                event=self
            )
            for num in numbers_to_add
        ]
        NumberList.objects.bulk_create(number_list_to_add)
        app_log.info(f"Time For loop 1: {time.time() - start_time2}")
        app_log.info(f"Test old: {old_limit_repeat}")

        start_time2 = time.time()
        # Prepare list for bulk update
        number_list_to_update = []

        # Update existing numbers' repeat_count
        for num in current_numbers_set:
            number_list = NumberList.objects.get(id=current_numbers_dict[num]['id'])
            number_selected_count = NumberSelected.objects.filter(number=number_list).count()

            new_repeat_count = self.limit_repeat
            # Ensure repeat_count does not go below the number of times it has been selected
            if number_selected_count != 0:
                app_log.info(f'New repeat count 1: {new_repeat_count}')
                new_repeat_count = new_repeat_count - number_selected_count
                app_log.info(f"\nDebug number: {num}")
                app_log.info(f"Number selected count: {number_selected_count}")
                app_log.info(f"New repeat count: {new_repeat_count} | Old: {old_limit_repeat}")
            # if new_repeat_count + number_selected_count > old_limit_repeat:
            #     raise ValueError(
            #         f"Cannot reduce repeat_count below the number of times number {num} has been selected.")

            number_list.repeat_count = new_repeat_count
            number_list_to_update.append(number_list)

        # Bulk update existing numbers
        NumberList.objects.bulk_update(number_list_to_update, ['repeat_count'])
        app_log.info(f"Time For loop 2: {time.time() - start_time2}")

        # Validate and possibly remove numbers
        start_time2 = time.time()
        for num in numbers_to_remove:
            number_list = NumberList.objects.get(event=self, number=num)
            if NumberSelected.objects.filter(number=number_list).exists():
                raise ValueError(f"Cannot reduce range_number, number {num} is already selected.")
            number_list.delete()
        app_log.info(f"Time For loop 3: {time.time() - start_time2}")

        app_log.info(f"Time complete update NumberList: {time.time() - start_time}")

    def validate_update(self, old_limit_repeat):
        start_time = time.time()
        current_numbers = set(NumberList.objects.filter(event=self).values_list('number', flat=True))
        new_numbers = set(range(1, self.range_number + 1))

        numbers_to_remove = current_numbers - new_numbers

        # Validate that no selected number is removed
        for num in numbers_to_remove:
            number_list = NumberList.objects.get(event=self, number=num)
            if NumberSelected.objects.filter(number=number_list).exists():
                raise ValidationError(f"Cannot reduce range_number, number {num} is already selected.")

        # Validate limit_repeat
        number_selected = NumberSelected.objects.filter(user_event__event=self).values_list('number__number', flat=True)
        smallest_repeat = NumberList.objects.filter(
            event=self,
            number__in=list(number_selected)
        ).order_by('repeat_count').first()
        app_log.info(f"Test smallest repeat: {smallest_repeat.repeat_count}")
        if smallest_repeat:
            result_reduce_limit = (self.limit_repeat - (old_limit_repeat - smallest_repeat.repeat_count))
            app_log.info(f"Result reduce limit: {result_reduce_limit}")
            if result_reduce_limit < 0:
                raise ValidationError(f"Cannot reduce limit_repeat, "
                                      f"numbers {smallest_repeat.number} have higher repeat count than the new limit.")
        app_log.info(f"Time complete Validate before update: {time.time() - start_time}")


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
        if not self.id or self.id == '':
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
        if not self.id or self.id == '':
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
    app_log.info(f"Input data: {user, date_start, date_end}")
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
    app_log.info(f"Test total point: {total_points}")
    return total_points
