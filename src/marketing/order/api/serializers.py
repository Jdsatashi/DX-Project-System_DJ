from rest_framework import serializers

from account.handlers.restrict_serializer import BaseRestrictSerializer
from marketing.order.models import Order, OrderDetail
from marketing.price_list.models import ProductPrice, PointOfSeason


class OrderDetailSerializer(BaseRestrictSerializer):
    class Meta:
        model = OrderDetail
        fields = ['product_id', 'order_quantity', 'order_box', 'product_price', 'point_get']


class OrderSerializer(BaseRestrictSerializer):
    order_detail = OrderDetailSerializer(many=True)
    list_type = serializers.CharField(required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at',
                            'updated_at', 'order_point', 'order_price']

    def create(self, validated_data):
        # Split insert data
        data, perm_data = self.split_data(validated_data)
        order_details_data = data.pop('order_detail', [])
        # Create new Order
        order = Order.objects.create(**data)
        total_point = float()
        total_price = float()
        # Add product to OrderDetail
        for detail_data in order_details_data:
            # Get product price to have ratio point/box and price/item
            quantity = detail_data.get('order_quantity')
            product_id = detail_data.get('product_id')
            product_price = ProductPrice.objects.get(price_list=order.price_list_id, product=product_id)
            # Calculate price and point
            prices = float(product_price.price) * float(quantity)
            point = float(product_price.point) * float(quantity / product_price.quantity_in_box)
            # Add price and point to detail data
            detail_data['product_price'] = prices
            detail_data['point_get'] = point
            # Create new OrderDetail
            order_detail = OrderDetail.objects.create(order_id=order, **detail_data)
            # Add price and point to total
            total_point += point
            total_price += prices
        # Create perm for data
        print(f"point of this order: {total_point}")
        print(f"Price of this order: {total_price}")
        order.order_point = total_point
        order.order_price = total_price
        order.save()

        point_of_season, created = PointOfSeason.objects.get_or_create(price_list=order.price_list_id, user=order.client_id)
        point_of_season.point = (point_of_season.point or 0) + total_point
        point_of_season.total_point = (point_of_season.total_point or 0) + total_point
        point_of_season.save()

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
