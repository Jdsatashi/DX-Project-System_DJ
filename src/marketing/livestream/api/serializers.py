from account.handlers.restrict_serializer import BaseRestrictSerializer
from marketing.livestream.models import LiveStream, LiveStreamComment


class LiveStreamSerializer(BaseRestrictSerializer):
    class Meta:
        model = LiveStream
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class LiveStreamCommentSerializer(BaseRestrictSerializer):
    class Meta:
        model = LiveStreamComment
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
