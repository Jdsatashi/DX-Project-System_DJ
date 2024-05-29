from rest_framework.response import Response

from account.handlers.restrict_serializer import BaseRestrictSerializer
from marketing.pick_number.models import UserJoinEvent, NumberList, EventNumber, NumberSelected
from rest_framework import serializers


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
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'number_selected_read': {'source': 'number_selected'}
        }

    def to_representation(self, instance):
        """Convert `number_selected` field from IDs to actual numbers."""
        representation = super().to_representation(instance)
        numbers = instance.number_selected.values_list('number__number', flat=True)
        representation['number_selected'] = list(numbers)
        return representation

    def create(self, validated_data):
        number_selected_data = validated_data.pop('number_selected', [])
        user_join_event = super().create(validated_data)
        self._update_number_selected(user_join_event, number_selected_data)
        return user_join_event

    def update(self, instance, validated_data):
        number_selected_data = validated_data.pop('number_selected', [])
        user_join_event = super().update(instance, validated_data)
        self._update_number_selected(user_join_event, number_selected_data)
        return user_join_event

    def _update_number_selected(self, user_join_event, number_selected_data):
        print(f"Input number: {number_selected_data}")
        current_numbers = set(user_join_event.number_selected.values_list('number__number', flat=True))
        new_numbers = set(number_selected_data)

        numbers_to_add = new_numbers - current_numbers
        numbers_to_remove = current_numbers - new_numbers

        print(f"Test number to add: {numbers_to_add}")
        print(f"Test number to remove: {numbers_to_remove}")

        # Add new numbers and update repeat_count
        for number_id in numbers_to_add:
            number = NumberList.objects.get(number=number_id)
            if number.repeat_count > 0:
                print(f"Testing number: {number}")
                if not NumberSelected.objects.filter(user_event=user_join_event, number=number).exists():
                    print(f"Number adding {number.number}")
                    NumberSelected.objects.create(user_event=user_join_event, number=number)
                    number.repeat_count -= 1
                    number.save()
                continue
            return Response({'message': f'Tem số {number.number} đã hết'})

        # Remove numbers and update repeat_count
        for number_id in numbers_to_remove:
            print(f"Testing number remove: {number_id}")
            NumberSelected.objects.filter(user_event=user_join_event, number__number=number_id).delete()
            number = NumberList.objects.get(number=number_id)
            number.repeat_count += 1
            number.save()


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
        print(f"Test user id: {user_ids}")
        event_number = super().update(instance, validated_data)

        # Add users to UserJoinEvent
        self._add_users_to_event(event_number, user_ids)

        return event_number

    @staticmethod
    def _add_users_to_event(event, user_ids):
        current_user_ids = set(UserJoinEvent.objects.filter(event=event).values_list('user_id', flat=True))
        new_user_ids = set(user_ids)
        print(f"Testing about")
        users_to_add = new_user_ids - current_user_ids
        for user_id in users_to_add:
            UserJoinEvent.objects.create(event=event, user_id=user_id)

        users_to_remove = current_user_ids - new_user_ids
        UserJoinEvent.objects.filter(event=event, user_id__in=users_to_remove).delete()
