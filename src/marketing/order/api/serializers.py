import time

from rest_framework import serializers, status
from rest_framework.response import Response

from account.handlers.restrict_serializer import BaseRestrictSerializer
from marketing.order.models import Order, OrderDetail
from marketing.price_list.models import ProductPrice, SpecialOfferProduct


class OrderDetailSerializer(BaseRestrictSerializer):
    product_name = serializers.CharField(source='product_id.name', read_only=True)

    class Meta:
        model = OrderDetail
        fields = ['product_id', 'product_name', 'order_quantity', 'order_box', 'product_price', 'point_get']


class OrderSerializer(BaseRestrictSerializer):
    order_detail = OrderDetailSerializer(many=True)
    list_type = serializers.CharField(required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'order_point', 'order_price']

    def create(self, validated_data):
        start_time = time.time()
        # Split insert data
        data, perm_data = self.split_data(validated_data)
        order_details_data = data.pop('order_detail', [])
        # Create new Order
        order = Order.objects.create(**data)
        print(f"Time split data: {time.time() - start_time}")

        # Calculate total price and point
        total_price, total_point, details = self.calculate_total_price_and_point(order, order_details_data)
        OrderDetail.objects.bulk_create(details)

        order.order_point = total_point
        order.order_price = total_price
        order.save()
        print(f"Time save data: {time.time() - start_time}")

        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, order.id, self.Meta.model)
        print(f"Time create perms: {time.time() - start_time}")
        return order

    def update(self, instance, validated_data):
        data, perm_data = self.split_data(validated_data)
        order_detail_data = data.pop('order_detail', [])

        # Update main instance Order
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()

        current_details_id = {detail.id: detail for detail in instance.order_detail.all()}
        update_details_id = set()
        total_point = float(0)
        total_price = float(0)

        # Update or create new OrderDetails
        new_details = []
        for detail_data in order_detail_data:
            product_id = detail_data.pop('product_id')
            quantity = detail_data.get('order_quantity')
            prices, point = self.calculate_price_and_point(instance, product_id, quantity)

            detail_data['product_price'] = prices
            detail_data['point_get'] = point

            if product_id in current_details_id:
                detail = current_details_id.pop(product_id)
                for attr, value in detail_data.items():
                    setattr(detail, attr, value)
                detail.save()
                update_details_id.add(detail.id)
            else:
                new_detail = OrderDetail(order_id=instance, product_id=product_id, **detail_data)
                new_details.append(new_detail)
                update_details_id.add(new_detail.id)

            total_point += point
            total_price += prices

        # Bulk create new details
        OrderDetail.objects.bulk_create(new_details)

        # Remove current OrderDetails which not in Update OrderDetail
        for detail_id in current_details_id:
            if detail_id not in update_details_id:
                current_details_id[detail_id].delete()

        instance.order_point = total_point
        instance.order_price = total_price
        instance.save()

        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, instance.id, self.Meta.model)
        return instance

    def calculate_price_and_point(self, order, product_id, quantity):
        try:
            if order.new_special_offer:
                product_price = SpecialOfferProduct.objects.get(special_offer=order.new_special_offer,
                                                                product=product_id)
                prices = float(product_price.price) * float(quantity) if product_price.price is not None else 0
                point = (float(product_price.point) * (quantity / product_price.quantity_in_box)
                         if product_price.point is not None and order.new_special_offer.count_turnover else 0)
            else:
                product_price = ProductPrice.objects.get(price_list=order.price_list_id, product=product_id)
                prices = float(product_price.price) * float(quantity) if product_price.price is not None else 0
                point = float(product_price.point) * (
                            quantity / product_price.quantity_in_box) if product_price.point is not None else 0
        except (ProductPrice.DoesNotExist, SpecialOfferProduct.DoesNotExist):
            raise serializers.ValidationError({'message': 'This product not in price list or special offer'})

        return prices, point

    def calculate_total_price_and_point(self, order, order_details_data):
        total_price = 0
        total_point = 0
        details = []

        for detail_data in order_details_data:
            quantity = detail_data.get('order_quantity')
            product_id = detail_data.pop('product_id')

            prices, point = self.calculate_price_and_point(order, product_id, quantity)

            detail_data['product_price'] = prices
            detail_data['point_get'] = point

            total_price += prices
            total_point += point

            detail = OrderDetail(order_id=order, product_id=product_id, **detail_data)
            details.append(detail)

        return total_price, total_point, details


class OldOrderSerializer(BaseRestrictSerializer):
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
            try:
                product_price = ProductPrice.objects.get(price_list=order.price_list_id, product=product_id)
            except ProductPrice.DoesNotExist:
                return Response({'message': 'This product not in price list'}, status=status.HTTP_400_BAD_REQUEST)
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
        order.order_point = total_point
        order.order_price = total_price
        order.save()

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
        total_point = float(0)
        total_price = float(0)
        # Update news OrderDetails
        for detail_data in order_detail_data:
            product_id = detail_data.pop('product_id')
            detail, created = instance.order_detail.get_or_create(product_id=product_id, defaults=detail_data)
            update_details_id.append(detail.id)
            if not created:
                for attr, value in detail_data.items():
                    setattr(detail, attr, value)
                detail.save()

            update_details_id.append(detail.id)

            # Calculate price and point for each order detail
            quantity = detail_data.get('order_quantity')
            try:
                product_price = ProductPrice.objects.get(price_list=instance.price_list_id, product=product_id)
            except ProductPrice.DoesNotExist:
                return Response({'message': 'This product not in price list'}, status=status.HTTP_400_BAD_REQUEST)

            prices = float(product_price.price) * float(quantity)
            point = float(product_price.point) * float(quantity / product_price.quantity_in_box)

            # Add price and point to detail data
            detail.product_price = prices
            detail.point_get = point
            detail.save()

            # Add price and point to total
            total_point += point
            total_price += prices
        # Remove current OrderDetails which not in Update OrderDetail
        for detail_id in current_details_id:
            if detail_id not in update_details_id:
                instance.order_detail.filter(id=detail_id).delete()
        instance.order_point = total_point
        instance.order_price = total_price
        instance.save()
        # Update perm for data
        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, instance.id, self.Meta.model)
        return instance


# class ProductStatisticsSerializer(serializers.Serializer):
#     product_id = serializers.CharField()
#     total_quantity = serializers.IntegerField()
#     total_point = serializers.FloatField()
#     total_price = serializers.IntegerField()

class ProductStatisticsSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    product_name = serializers.CharField()
    current = serializers.DictField(required=False)
    one_year_ago = serializers.DictField(required=False)
