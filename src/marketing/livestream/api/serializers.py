from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import serializers

from account.handlers.restrict_serializer import BaseRestrictSerializer
from account.models import User, PhoneNumber
from marketing.livestream.models import LiveStream, LiveStreamComment, LiveStreamProductList, LiveStreamProduct, \
    LiveStreamStatistic, LiveStreamTracking


class LiveStreamSerializer(BaseRestrictSerializer):
    class Meta:
        model = LiveStream
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class LiveStreamCommentSerializer(BaseRestrictSerializer):
    class Meta:
        model = LiveStreamComment
        fields = '__all__'
        read_only_fields = ('id', 'user', 'phone', 'created_at', 'updated_at')

    def create(self, validate_data):
        data, perm_data = self.split_data(validate_data)

        request = self.context.get('request')
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
            return Response({'message': 'Invalid token'}, status=401)

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


class LiveProduct(BaseRestrictSerializer):
    class Meta:
        model = LiveStreamProduct
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class LiveProductList(BaseRestrictSerializer):
    class Meta:
        model = LiveStreamProductList
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class LiveStatistic(BaseRestrictSerializer):
    class Meta:
        model = LiveStreamStatistic
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class LiveTracking(BaseRestrictSerializer):
    class Meta:
        model = LiveStreamTracking
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
