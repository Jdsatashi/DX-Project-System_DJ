import traceback

from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import serializers

from account.handlers.perms import get_perm_name, get_full_permname
from account.handlers.restrict_serializer import BaseRestrictSerializer
from account.models import User, PhoneNumber, Perm, GroupPerm
from account.queries import get_user_by_permname_sql
from app.logs import app_log
from marketing.livestream.models import LiveStream, LiveStreamComment, LiveStreamStatistic, LiveStreamTracking, \
    LiveStreamPeekView, LiveStreamOfferRegister
from utils.constants import perm_actions
from utils.import_excel import get_user_list


class LiveStreamCommentSerializer(BaseRestrictSerializer):
    class Meta:
        model = LiveStreamComment
        fields = '__all__'
        read_only_fields = ('id', 'user', 'phone', 'created_at', 'updated_at')

    def create(self, validate_data):
        try:
            with transaction.atomic():
                data, perm_data = self.split_data(validate_data)

                request = self.context.get('request')
                user, phone = get_phone_from_token(request)

                comment = data.get('comment', None)
                live_stream = data.get('live_stream', None)
                # livestream = LiveStream.objects.get(id=live_stream)
                if not comment:
                    raise ValidationError('Comment must be not empty')

                # Create comment
                comment_object = LiveStreamComment.objects.create(
                    user=user,
                    phone=phone,
                    comment=comment,
                    live_stream=live_stream
                )

                # Create permission
                restrict = perm_data.get('restrict')
                if restrict:
                    self.handle_restrict(perm_data, comment_object.id, self.Meta.model)

                return comment_object
        except Exception as e:
            raise e


class LiveStreamDetailCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveStreamComment
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class ViewLiveStatistic(BaseRestrictSerializer):
    class Meta:
        model = LiveStreamStatistic
        # fields = '__all__'
        exclude = ['id', 'created_at', 'updated_at']


class LiveStreamSerializer(BaseRestrictSerializer):
    import_users = serializers.FileField(write_only=True, required=False, allow_null=True)
    class Meta:
        model = LiveStream
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def to_representation(self, instance: LiveStream):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        if (request and request.method == 'GET'
                and hasattr(request, 'resolver_match')
                and request.resolver_match.kwargs.get('pk')):
            # Get user added in price list
            perm_name = get_full_permname(self.Meta.model, 'view', instance.id)
            user_group = get_user_by_permname_sql(perm_name)
            user_manage = list(user_group)
            ret['users'] = user_manage
            groups_user = GroupPerm.objects.filter(perm__name=perm_name).values_list('display_name',
                                                                                     flat=True).distinct()
            ret['groups'] = list(groups_user)
            #
        statistic = instance.livestreamstatistic_set.first()
        ret['statistic'] = ViewLiveStatistic(statistic).data
        return ret

    def create(self, validated_data):
        data, perm_data = self.split_data(validated_data)
        try:
            with transaction.atomic():
                import_users = data.pop('import_users', None)

                livestream = LiveStream.objects.create(**data)

                user_actions = [perm_actions['view'], perm_actions['create']]
                self.handle_restrict_import_users_id(import_users, perm_data, user_actions)
                restrict = perm_data.get('restrict')

                if restrict:
                    self.handle_restrict(perm_data, livestream.id, self.Meta.model)
                return livestream
        except Exception as e:
            # raise e
            app_log.error(f"Lỗi khi tạo livestream: {e}")
            raise ValidationError({'message': e})

    def update(self, instance, validated_data):
        # Split insert data
        data, perm_data = self.split_data(validated_data)
        import_users = data.pop('import_users', None)

        try:
            with transaction.atomic():
                # Update LiveStream fields
                for attr, value in data.items():
                    setattr(instance, attr, value)
                instance.save()
                user_actions = [perm_actions['view'], perm_actions['create']]
                # Handle restrictions (if any)
                self.handle_restrict_import_users_id(import_users, perm_data, user_actions)
                restrict = perm_data.get('restrict')
                perm_name = get_perm_name(self.Meta.model)
                perm_name = perm_name + f"_{instance.id}"
                if restrict or Perm.objects.filter(name__endswith=perm_name).exists():
                    self.handle_restrict(perm_data, instance.id, self.Meta.model)

                return instance

        except Exception as e:
            tb = traceback.format_exc()
            app_log.error(f"Error when updating livestream: {e}\n{tb}")
            # raise serializers.ValidationError({'message': f'unexpected error when updating livestream {instance.id}'})
            raise e


class LiveStatistic(BaseRestrictSerializer):
    class Meta:
        model = LiveStreamStatistic
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class LiveTracking(serializers.ModelSerializer):
    class Meta:
        model = LiveStreamTracking
        fields = '__all__'
        read_only_fields = ['id', 'phone', 'time_watch', 'created_at']
        extra_kwargs = {
            'time_join': {'allow_null': True},
            'time_leave': {'allow_null': True},
            'note': {'required': False, 'allow_null': True, 'allow_blank': True}
        }

    def create(self, validate_data):
        request = self.context.get('request')
        user, phone = get_phone_from_token(request)

        time_join = validate_data.get('time_join', None)
        live_stream = validate_data.get('live_stream', None)
        time_leave = validate_data.get('time_leave', None)
        note = validate_data.get('note', None)

        # Create tracking
        tracking = LiveStreamTracking.objects.create(
            phone=phone,
            time_join=time_join,
            live_stream=live_stream,
            time_leave=time_leave,
            note=note
        )

        return tracking

    def update(self, instance, validate_data):
        validate_data.pop('live_stream')
        validate_data.pop('phone')
        for attr, value in validate_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


def get_phone_from_token(request):
    if request:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ')[1]
        else:
            raise ValidationError('Invalid token')
    else:
        raise ValidationError('Not found request')

    # Get user and phone objects from access token
    try:
        token = AccessToken(access_token)
        user = User.objects.get(id=token['user_id'])
        phone = PhoneNumber.objects.get(phone_number=token['phone_number'])
    except TokenError:
        raise ValidationError('Invalid token')
    return user, phone


class PeekViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveStreamPeekView
        fields = '__all__'
        read_only_fields = ['id']


class LiveOfferRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveStreamOfferRegister
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
