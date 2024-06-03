import time

from rest_framework import serializers
from rest_framework.response import Response

from account.handlers.restrict_serializer import BaseRestrictSerializer
from app.logs import app_log
from app.settings import pusher_client
from marketing.pick_number.models import UserJoinEvent, NumberList, EventNumber, NumberSelected, calculate_point_query


class ReadNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = NumberList
        fields = ['number', 'repeat_count']


class ReadNumberSelectedSerializer(serializers.ModelSerializer):
    class Meta:
        model = NumberSelected
        fields = ['number']


class NumberSelectedSerializer(BaseRestrictSerializer):
    class Meta:
        model = NumberSelected
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class NumberListSerializer(BaseRestrictSerializer):
    class Meta:
        model = NumberList
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class UserJoinEventSerializer(BaseRestrictSerializer):
    number_selected = serializers.ListField(
        child=serializers.IntegerField(), write_only=True
    )

    class Meta:
        model = UserJoinEvent
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'total_point', 'turn_pick', 'used_point', 'turn_selected')

    def to_representation(self, instance):
        """Convert `number_selected` field from IDs to actual numbers."""
        representation = super().to_representation(instance)
        numbers = instance.number_selected.values_list('number__number', flat=True)
        representation['number_selected'] = list(numbers)
        return representation

    def create(self, validated_data):
        number_selected_data = validated_data.pop('number_selected', [])
        user_join_event = super().create(validated_data)
        self.update_number_selected(user_join_event, number_selected_data)
        return user_join_event

    def update(self, instance, validated_data):
        number_selected_data = validated_data.pop('number_selected', [])
        user_join_event = super().update(instance, validated_data)
        self.update_number_selected(user_join_event, number_selected_data)
        return user_join_event

    @staticmethod
    def update_number_selected(user_join_event, number_selected_data):
        current_numbers = set(user_join_event.number_selected.values_list('number__number', flat=True))
        new_numbers = set(number_selected_data)

        numbers_to_add = new_numbers - current_numbers
        numbers_to_remove = current_numbers - new_numbers
        if user_join_event.turn_pick < len(numbers_to_add):
            return Response({'message': 'Số đã chọn vượt quá số lượt chọn.'}, status=400)

        # Add new numbers and update repeat_count
        for number_id in numbers_to_add:
            number = NumberList.objects.filter(number=number_id).first()
            if not number:
                return Response({'message': f'Số cung cấp không hợp lệ'})
            # Check if number is available
            if number.repeat_count > 0:
                # If not exist user selected number, create new one and minus 1 repeat
                if not NumberSelected.objects.filter(user_event=user_join_event, number=number).exists():
                    app_log.info(f"Number object existing")
                    NumberSelected.objects.create(user_event=user_join_event, number=number)
                    number.repeat_count -= 1
                    number.save()
                continue
            else:
                return Response({'message': f'Tem số {number.number} đã hết'})
        # Update turn_selected and used_point with new numbers
        user_join_event.turn_selected = len(numbers_to_add)
        user_join_event.turn_pick = user_join_event.turn_pick - user_join_event.turn_selected
        user_join_event.used_point = len(numbers_to_add) * int(user_join_event.event.point_exchange)
        user_join_event.save()
        # Remove numbers and update repeat_count
        for number_id in numbers_to_remove:
            NumberSelected.objects.filter(user_event=user_join_event, number__number=number_id).delete()
            number = NumberList.objects.get(number=number_id, event=user_join_event.event)
            number.repeat_count += 1
            number.save()


class UserJoinEventNumberSerializer(serializers.ModelSerializer):
    number_picked = serializers.IntegerField(write_only=True)

    class Meta:
        model = UserJoinEvent
        fields = ['id', 'event', 'user', 'number_picked', 'total_point', 'turn_pick', 'used_point', 'turn_selected']
        read_only_fields = ('id', 'event', 'user', 'total_point', 'turn_pick', 'used_point', 'turn_selected')

    def to_representation(self, instance):
        """Convert `number_selected` field from IDs to actual numbers."""
        representation = super().to_representation(instance)
        numbers = instance.number_selected.values_list('number__number', flat=True)
        representation['number_selected'] = list(numbers)
        return representation

    def update(self, instance, validated_data):
        number_picked = validated_data.pop('number_picked')

        # Check if the number is already selected
        existing_selection = NumberSelected.objects.filter(user_event=instance, number__number=number_picked).first()

        if existing_selection:
            # Unpick the number
            _type = 'unpick'
            number_list = existing_selection.number
            number_list.repeat_count += 1
            number_list.save()
            existing_selection.delete()
        else:
            # Pick the number
            _type = 'pick'
            number_list = NumberList.objects.filter(number=number_picked, event=instance.event).first()
            if not number_list:
                return Response({'message': 'Số cung cấp không hợp lệ'}, status=400)
            if number_list.repeat_count > 0:
                NumberSelected.objects.create(user_event=instance, number=number_list)
                number_list.repeat_count -= 1
                number_list.save()
            else:
                return Response({'message': f'Tem số {number_picked} đã hết'}, status=400)
        start_time_2 = time.time()
        pus_data = {'type': _type, 'number': int(number_picked), 'event_id': instance.event.id}
        try:
            app_log.info(f"-- Test pusher --")
            pus_event = 'pick_number'
            app_log.info(f"Message: {pus_data}")
            app_log.info(f"Event: {pus_event}")
            list_user = instance.event.user_join_event.filter().exclude(user=instance.user)
            app_log.info(f"{list_user}")
            for user in instance.event.user_join_event.filter().exclude(user=instance.user):
                chanel = f'user_{user.user.id}'
                app_log.info(f"Chanel: {chanel}")
                pusher_client.trigger(chanel, pus_event, pus_data)

        except Exception as e:
            app_log.info(f"Pusher error")
            raise e
        app_log.info(f"Time handle Pusher: {time.time() - start_time_2}")
        # Update turn_selected and used_point with new numbers
        instance.turn_selected = instance.number_selected.count()
        instance.turn_pick = instance.total_point // instance.event.point_exchange - instance.turn_selected
        instance.used_point = instance.turn_selected * instance.event.point_exchange
        instance.save()

        return instance


class EventNumberSerializer(BaseRestrictSerializer):
    users = serializers.ListField(child=serializers.CharField(), write_only=True)

    class Meta:
        model = EventNumber
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def to_representation(self, instance):
        """Convert `users` field from IDs to actual user representations."""
        representation = super().to_representation(instance)
        user_ids = UserJoinEvent.objects.filter(event=instance).values_list('user_id', flat=True)
        user_ids = list(set(user_ids))
        representation['users'] = user_ids
        return representation

    def create(self, validated_data):
        user_ids = validated_data.pop('users', [])
        event_number = super().create(validated_data)

        # Add users to UserJoinEvent
        self._add_users_to_event(event_number, user_ids)

        return event_number

    def update(self, instance, validated_data):
        user_ids = validated_data.pop('users', [])
        app_log.info(f"Test user id: {user_ids}")
        event_number = super().update(instance, validated_data)

        # Add users to UserJoinEvent
        self._add_users_to_event(event_number, user_ids)

        return event_number

    @staticmethod
    def _add_users_to_event(event, user_ids):
        current_user_ids = set(UserJoinEvent.objects.filter(event=event).values_list('user_id', flat=True))
        new_user_ids = set(user_ids)

        users_to_add = new_user_ids - current_user_ids
        for user_id in users_to_add:
            user_join = UserJoinEvent.objects.filter(event=event, user_id=user_id).first()
            if user_join is None:
                user_join = UserJoinEvent.objects.create(event=event, user_id=user_id)
            # analysis_point(event, user_join)
            total_point = calculate_point_query(user_join.user, event.date_start, event.date_close, event.price_list)
            user_join.total_point = total_point + user_join.bonus_point
            user_join.turn_pick = user_join.total_point // event.point_exchange - user_join.turn_selected
            user_join.save()
        users_to_remove = current_user_ids - new_user_ids
        UserJoinEvent.objects.filter(event=event, user_id__in=users_to_remove).delete()
        # for user_id in users_to_remove:
        #     user_join = UserJoinEvent.objects.get(event=event, user_id=user_id)
        #     numbers_selected = NumberSelected.objects.filter(user_event=user_join)
        #     for number_sel in numbers_selected:
        #         number_list = number_sel.number
        #         number_list.repeat_count += 1
        #         number_list.save()
        #     numbers_selected.delete()
        #     user_join.delete()
