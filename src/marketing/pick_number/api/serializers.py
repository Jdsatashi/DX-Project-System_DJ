import time

from django.db import transaction
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from account.handlers.perms import get_perm_name
from account.handlers.restrict_serializer import BaseRestrictSerializer
from account.models import User, PhoneNumber
from app.logs import app_log
from app.settings import pusher_client
from marketing.order.models import SeasonalStatisticUser
from marketing.pick_number.models import UserJoinEvent, NumberList, EventNumber, NumberSelected, \
    PrizeEvent, AwardNumber, PickNumberLog
from utils.constants import perm_actions


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
    # number_selected = serializers.ListField(
    #     child=serializers.IntegerField(), write_only=True
    # )

    class Meta:
        model = UserJoinEvent
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'total_point',
                            'bonus_point', 'turn_per_point', 'turn_pick', 'turn_selected')

    def to_representation(self, instance):
        """Convert `number_selected` field from IDs to actual numbers."""
        representation = super().to_representation(instance)
        numbers = instance.number_selected.order_by('number__number').values_list('number__number', flat=True)
        representation['number_selected'] = list(numbers)
        return representation

    def create(self, validated_data):
        number_selected_data = validated_data.pop('number_selected', [])
        with transaction.atomic():
            user_join_event = super().create(validated_data)
            # self.update_number_selected(user_join_event, number_selected_data)
            return user_join_event

    def update(self, instance, validated_data):
        number_selected_data = validated_data.pop('number_selected', [])
        user_join_event = super().update(instance, validated_data)
        # self.update_number_selected(user_join_event, number_selected_data)
        return user_join_event

    # @staticmethod
    # def update_number_selected(user_join_event, number_selected_data):
    #     current_numbers = set(user_join_event.number_selected.values_list('number__number', flat=True))
    #     new_numbers = set(number_selected_data)
    #
    #     numbers_to_add = new_numbers - current_numbers
    #     numbers_to_remove = current_numbers - new_numbers
    #     if user_join_event.turn_pick < len(numbers_to_add):
    #         return Response({'message': 'Số đã chọn vượt quá số lượt chọn.'}, status=400)
    #
    #     # Add new numbers and update repeat_count
    #     for number_id in numbers_to_add:
    #         number = NumberList.objects.filter(number=number_id).first()
    #         if not number:
    #             return Response({'message': f'Số cung cấp không hợp lệ'})
    #         # Check if number is available
    #         if number.repeat_count > 0:
    #             # If not exist user selected number, create new one and minus 1 repeat
    #             if not NumberSelected.objects.filter(user_event=user_join_event, number=number).exists():
    #                 app_log.info(f"Number object existing")
    #                 NumberSelected.objects.create(user_event=user_join_event, number=number)
    #                 number.repeat_count -= 1
    #                 number.save()
    #             continue
    #         else:
    #             return Response({'message': f'Tem số {number.number} đã hết'})
    #     # Update turn_selected and used_point with new numbers
    #     user_join_event.turn_selected = len(numbers_to_add)
    #     user_join_event.turn_pick = user_join_event.turn_pick - user_join_event.turn_selected
    #     # user_join_event.used_point = len(numbers_to_add) * int(user_join_event.event.point_exchange)
    #     user_join_event.save()
    #     # Remove numbers and update repeat_count
    #     for number_id in numbers_to_remove:
    #         NumberSelected.objects.filter(user_event=user_join_event, number__number=number_id).delete()
    #         number = NumberList.objects.get(number=number_id, event=user_join_event.event)
    #         number.repeat_count += 1
    #         number.save()


class UserJoinEventNumberSerializer(serializers.ModelSerializer):
    number_picked = serializers.IntegerField(write_only=True)

    class Meta:
        model = UserJoinEvent
        fields = ['id', 'event', 'user', 'number_picked', 'total_point', 'turn_pick', 'turn_selected']
        read_only_fields = ('id', 'event', 'user', 'total_point', 'turn_pick', 'turn_selected')

    def to_representation(self, instance):
        """Convert `number_selected` field from IDs to actual numbers."""
        representation = super().to_representation(instance)
        numbers = instance.number_selected.order_by('number__number').values_list('number__number', flat=True)
        representation['number_selected'] = list(numbers)
        return representation

    def update(self, instance: UserJoinEvent, validated_data):
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
            if instance.turn_pick <= instance.turn_selected:
                raise ValidationError({'message': 'không đủ tem'})
            number_list = NumberList.objects.filter(number=number_picked, event=instance.event).first()
            number_selected = NumberSelected.objects.filter(number=number_list)
            if not number_list:
                raise ValidationError({'message': 'Số cung cấp không hợp lệ'})
            if number_list.repeat_count > 0 and number_selected.count() > 0:
                number_list.repeat_count -= 1
                number_list.save()
                NumberSelected.objects.create(user_event=instance, number=number_list)

            else:
                raise ValidationError({'message': f'Tem số {number_picked} đã hết'})
        data = {'number': number_picked, 'action': _type}
        self.add_action_log(instance.event, data, instance.user)
        start_time_2 = time.time()
        pus_data = {'type': _type, 'number': int(number_picked),
                    'event_id': instance.event.id, 'user_id': instance.user.id}
        try:
            app_log.info(f"-- Test pusher --")
            pus_event = 'pick_number'
            app_log.info(f"Message: {pus_data}")
            app_log.info(f"Event: {pus_event}")
            # list_user = instance.event.user_join_event.filter().exclude(user=instance.user)
            # app_log.info(f"{list_user}")
            chanel = f"event_{instance.event.id}"
            app_log.info(f"Channel: {chanel}")
            pusher_client.trigger(chanel, pus_event, pus_data)
            # list_chanel = [f'user_{user.user.id}' for user in list_user if user is not None]
            # # for user in list_user:
            # #     chanel = f'user_{user.user.id}'
            # #     app_log.info(f"Chanel: {chanel}")
            # #     list_chanel.append(chanel)
            # max_item = 100
            # for i in range(0, len(list_chanel), max_item):
            #     chunk = list_chanel[i:i+max_item]
            #     app_log.info(f"Test chunk: {len(chunk)}")
            #     pusher_client.trigger(chunk, pus_event, pus_data)

        except Exception as e:
            app_log.info(f"Pusher error")
            raise e
        app_log.info(f"Time handle Pusher: {time.time() - start_time_2}")
        # Update turn_selected and used_point with new numbers
        instance.turn_selected = instance.number_selected.count()
        # instance.turn_pick = instance.total_point // instance.event.point_exchange - instance.turn_selected
        # instance.used_point = instance.turn_selected * instance.event.point_exchange
        instance.save()

        return instance

    def add_action_log(self, event, data, user):
        print(f"Test log data: {data}")
        request = self.context.get('request')

        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                # Get access token from headers
                access_token = auth_header.split(' ')[1]
                token = AccessToken(str(access_token))
                # Get user object from user id in access token
                try:
                    phone = PhoneNumber.objects.get(phone_number=token.get('phone_number'))
                except PhoneNumber.DoesNotExist:
                    phone = None
            else:
                phone = None
        except TokenError:
            # raise e
            raise ValidationError({'message': 'Token không hợp lệ hoặc đã hết hạn'})
        print(f"Get phone: {phone}")
        if phone is None:
            pick_log = PickNumberLog.objects.create(user=user, event=event, **data)
        else:
            pick_log = PickNumberLog.objects.create(user=user, phone=phone, event=event, **data)
        print(f"Pick log: {pick_log}")


# serializers.py

class AwardNumberSerializer(BaseRestrictSerializer):
    class Meta:
        model = AwardNumber
        fields = '__all__'


class UserDetailSerializer(serializers.ModelSerializer):
    register_name = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    nvtt = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'register_name', 'address', 'nvtt')

    def get_nvtt(self, obj):
        nvtt_id = obj.clientprofile.nvtt_id
        if nvtt_id:
            nvtt = User.objects.filter(id=nvtt_id).first()
            if nvtt:
                return {
                    "id": nvtt.id,
                    "name": nvtt.employeeprofile.register_name
                }
        return None

    def get_register_name(self, obj: User):
        if obj.user_type != 'employee':
            return obj.clientprofile.register_name
        return None

    def get_address(self, obj: User):
        if obj.user_type != 'employee':
            return obj.clientprofile.address
        return None


class PrizeEventReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrizeEvent
        fields = ('id', 'prize_name', 'reward_value')


class AwardUserSerializer(serializers.ModelSerializer):
    event = serializers.SerializerMethodField()
    reward = PrizeEventReadSerializer(source='prize', read_only=True)

    # award_users = serializers.SerializerMethodField()

    class Meta:
        model = AwardNumber
        fields = '__all__'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        number_award = instance.number
        user_selected_number = (UserJoinEvent.objects.filter(
            number_selected__number__number=number_award, event=instance.prize.event)
                                .select_related('user').values_list('user__id', flat=True))

        if (request and request.method == 'GET'
                and hasattr(request, 'resolver_match')
                and request.resolver_match.kwargs.get('pk')):

            users = User.objects.filter(id__in=user_selected_number)
            ret['award_users'] = UserDetailSerializer(users, many=True).data
        else:
            number_award = instance.number
            user_selected_number = (UserJoinEvent.objects.filter(
                number_selected__number__number=number_award, event=instance.prize.event)
                                    .select_related('user').values_list('user__id', flat=True))

            ret['award_users_number'] = user_selected_number.count()
        return ret

    def get_award_users2(self, obj: AwardNumber):
        number_award = obj.number
        # user_selected_number = NumberSelected.objects.filter(
        #     number__number=number_award, user_event__event=obj.prize.event)
        user_selected_number = UserJoinEvent.objects.filter(number_selected__number__number=number_award,
                                                            event=obj.prize.event).select_related('user').values_list(
            'user__id', flat=True)

        users = User.objects.filter(id__in=user_selected_number)
        print(f"Test user selected: {users}")
        return UserDetailSerializer(users, many=True).data

    def get_event(self, obj: AwardNumber):
        event = obj.prize.event
        return {
            'id': event.id,
            'name': event.name
        }


class PrizeEventSerializer(serializers.ModelSerializer):
    award_number = serializers.ListField(child=serializers.IntegerField(), allow_null=True, write_only=True,
                                         required=False)

    class Meta:
        model = PrizeEvent
        fields = '__all__'
        extra_kwargs = {
            'event': {'required': False},
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        numbers = AwardNumber.objects.filter(prize=instance).values_list('number', flat=True)
        representation['award_number'] = list(numbers)
        return representation

    def create(self, validated_data):
        award_number_ids = validated_data.pop('award_number', None)
        prize_event = super().create(validated_data)
        if award_number_ids is not None:
            self.update_award_numbers(prize_event, award_number_ids)
        return prize_event

    def update(self, instance, validated_data):
        award_number_ids = validated_data.pop('award_number', None)
        prize_event = super().update(instance, validated_data)
        if award_number_ids is not None:
            self.update_award_numbers(prize_event, award_number_ids)
        return prize_event

    def update_award_numbers(self, prize_event, award_number_ids):
        if not award_number_ids:
            return

        # Get event prize
        event_number = prize_event.event
        if event_number is None:
            raise ValidationError("PrizeEvent must be linked to an EventNumber to validate award numbers.")
        # Get range numbers
        range_number = event_number.range_number
        # Get all number was used
        used_numbers = set(AwardNumber.objects
                           .filter(prize__event=event_number)
                           .exclude(prize=prize_event)
                           .values_list('number', flat=True)
                           .distinct())
        current_numbers = set(prize_event.award_number.values_list('number', flat=True))
        new_numbers = set(award_number_ids)

        # Determine numbers to be removed and to be added
        numbers_to_remove = current_numbers - new_numbers
        numbers_to_add = new_numbers - current_numbers - used_numbers

        # Validate the new numbers
        for number_id in numbers_to_add:
            if number_id > range_number or number_id < 1:
                raise ValidationError(f"Number {number_id} is out of the allowed range (1 to {range_number}).")
            if number_id in used_numbers:
                raise ValueError(f"Number {number_id} is already used in another PrizeEvent of this EventNumber.")

        # Remove old numbers no longer needed
        if numbers_to_remove:
            AwardNumber.objects.filter(prize=prize_event, number__in=numbers_to_remove).delete()

        # Create new award numbers
        new_award_numbers = [AwardNumber(prize=prize_event, number=number) for number in numbers_to_add]
        AwardNumber.objects.bulk_create(new_award_numbers)


class EventNumberSerializer(BaseRestrictSerializer):
    users = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    prize_event = PrizeEventSerializer(many=True, required=False)

    class Meta:
        model = EventNumber
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user_ids = UserJoinEvent.objects.filter(event=instance).values_list('user_id', flat=True)
        user_ids = list(set(user_ids))
        representation['users'] = user_ids
        return representation

    def create(self, validated_data):
        data, perm_data = self.split_data(validated_data)
        users = data.pop('users', [])
        prize_events = data.pop('prize_event', [])
        with transaction.atomic():
            event_number = super().create(data)
            self._manage_prize_events(event_number, prize_events)
            self._add_users_to_event(event_number, users)
            add_user = self._add_users_to_event(event_number, users)
            if perm_data['restrict']:
                perm_data['allow_actions'] = perm_actions['self']
                perm_data['allow_users'] = add_user
                self.handle_restrict(perm_data, event_number.id, self.Meta.model)
            return event_number

    def update(self, instance, validated_data):
        data, perm_data = self.split_data(validated_data)
        users = data.pop('users', [])
        prize_events = data.pop('prize_event', [])
        with transaction.atomic():
            event_number = super().update(instance, data)
            instance.prize_event.all().delete()
            self._manage_prize_events(event_number, prize_events)
            add_user = self._add_users_to_event(event_number, users)
            if perm_data['restrict']:
                perm_data['allow_actions'] = perm_actions['self']
                perm_data['allow_users'] = add_user
                self.handle_restrict(perm_data, instance.id, self.Meta.model)
            return event_number

    @staticmethod
    def _manage_prize_events(event, prize_events_data):
        for prize_data in prize_events_data:
            prize_serializer = PrizeEventSerializer(data={**prize_data, "event": event.id})
            if prize_serializer.is_valid(raise_exception=True):
                prize_serializer.save()
            else:
                raise ValidationError({'message': "prize data is invalid"})

    @staticmethod
    def _add_users_to_event(event: EventNumber, user_ids):
        stats_users = SeasonalStatisticUser.objects.filter(season_stats__event_number=event)
        print(f"Check users: {stats_users}")
        added_id = list()

        for stats_user in stats_users:
            print(f"Looping user join event: {stats_user}")
            turn_per_point = stats_user.turn_per_point
            turn_pick = stats_user.turn_pick
            total_point = stats_user.total_point or 0
            print(f"Test data: {[turn_per_point, turn_pick, total_point]}")
            user_event = UserJoinEvent.objects.filter(
                user=stats_user.user, event=event)
            if user_event.exists():
                user_event = user_event.first()
                user_event.turn_per_point = turn_per_point
                user_event.turn_pick = turn_pick
                user_event.total_point = total_point
                user_event.save()
            else:
                user_event = UserJoinEvent.objects.create(
                    user=stats_user.user, event=event, total_point=total_point, turn_pick=turn_pick,
                    turn_per_point=turn_per_point)

            added_id.append(user_event.id)
        UserJoinEvent.objects.filter(event=event).exclude(id__in=added_id).delete()
        return stats_users.values_list('user_id', flat=True).distinct()

    #     current_user_ids = set(UserJoinEvent.objects.filter(event=event).values_list('user_id', flat=True))
    #     new_user_ids = set(user_ids)
    #
    #     users_to_add = new_user_ids - current_user_ids
    #     for user_id in users_to_add:
    #         user_join = UserJoinEvent.objects.filter(event=event, user_id=user_id).first()
    #         if user_join is None:
    #             user_join = UserJoinEvent.objects.create(event=event, user_id=user_id)
    #         total_point = calculate_point_query(user_join.user, event.date_start, event.date_close, event.price_list)
    #         user_join.total_point = total_point + user_join.bonus_point
    #         # user_join.turn_pick = user_join.total_point // event.point_exchange - user_join.turn_selected
    #         user_join.save()
    #     users_to_remove = current_user_ids - new_user_ids
    #     UserJoinEvent.objects.filter(event=event, user_id__in=users_to_remove).delete()


class PickNumberLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PickNumberLog
        fields = '__all__'
