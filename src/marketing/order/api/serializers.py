from rest_framework import serializers

from account.handlers.restrict_serializer import BaseRestrictSerializer
from marketing.order.models import Order, OrderDetail


class OrderDetailSerializer(BaseRestrictSerializer):
    product_name = serializers.ReadOnlyField(source='product_id.name')

    class Meta:
        model = OrderDetail
        fields = ['product_id', 'product_name', 'order_quantity', 'order_box']


class OrderSerializer(BaseRestrictSerializer):
    order_detail = OrderDetailSerializer(many=True)
    list_type = serializers.CharField(required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', ]

    def create(self, validated_data):
        # Split insert data
        data, perm_data = self.split_data(validated_data)
        order_details_data = data.pop('order_detail', [])
        # Create new Order
        order = Order.objects.create(**data)
        # Add product to OrderDetail
        for detail_data in order_details_data:
            order_detail = OrderDetail.objects.create(order_id=order, **detail_data)
        # Create perm for data
        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, order.id, self.Meta.model)
        return order

    def update(self, instance, validated_data):
        # Split insert data
        data, perm_data = self.split_data(validated_data)
        order_detail_data = data.pop('order_detail', [])
        # Update main instance Order
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()
        # Get current OrderDetails
        current_details_id = [detail.id for detail in instance.order_detail.all()]
        update_details_id = []
        # Update news OrderDetails
        for detail_data in order_detail_data:
            product_id = detail_data.pop('product_id')
            detail, exist = instance.order_detail.get_or_create(product_id=product_id, defaults=detail_data)
            update_details_id.append(detail.id)
        # Remove current OrderDetails which not in Update OrderDetail
        for detail_id in current_details_id:
            if detail_id not in update_details_id:
                instance.order_detail.filter(id=detail_id).delete()
        # Update perm for data
        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, instance.id, self.Meta.model)
        return instance
