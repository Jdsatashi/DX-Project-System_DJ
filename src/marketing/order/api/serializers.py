from account.handlers.restrict_serializer import BaseRestrictSerializer
from marketing.order.models import Order, OrderDetail


class OrderSerializer(BaseRestrictSerializer):
    class Meta:
        model = Order
        fields = '__all__'


class OrderDetailSerializer(BaseRestrictSerializer):
    class Meta:
        model = OrderDetail
        fields = '__all__'
