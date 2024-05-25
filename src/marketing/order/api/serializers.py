import time

from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response

from account.handlers.restrict_serializer import BaseRestrictSerializer
from account.models import PhoneNumber
from marketing.livestream.api.serializers import get_phone_from_token
from marketing.livestream.models import LiveStreamOfferRegister
from marketing.order.models import Order, OrderDetail, update_sale_statistics_for_user
from marketing.price_list.models import ProductPrice, SpecialOfferProduct
from marketing.sale_statistic.models import SaleStatistic, SaleTarget


class OrderDetailSerializer(BaseRestrictSerializer):
    product_name = serializers.CharField(source='product_id.name', read_only=True)

    class Meta:
        model = OrderDetail
        fields = ['product_id', 'product_name', 'order_quantity', 'order_box', 'product_price', 'point_get']


class OrderSerializer(BaseRestrictSerializer):
    order_detail = OrderDetailSerializer(many=True)
    list_type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    status = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'order_point', 'order_price']

    def create(self, validated_data):
        # Split insert data
        data, perm_data = self.split_data(validated_data)
        # Get order detail data
        order_details_data = data.pop('order_detail', [])
        # Validate product order details
        user_sale_statistic = self.validate_special_offer(data, order_details_data)

        # Create new Order
        order = Order.objects.create(**data)

        # Calculate total price and point
        details = self.calculate_total_price_and_point(order, order_details_data)
        OrderDetail.objects.bulk_create(details)
        # Get total point and price from query
        total_price = OrderDetail.objects.filter(order_id=order).aggregate(total_price=Sum('product_price'))[
            'total_price']
        total_point = OrderDetail.objects.filter(order_id=order).aggregate(total_point=Sum('point_get'))['total_point']
        # Add to order
        order.order_point = total_point
        order.order_price = total_price
        order.save()

        self.update_sale_statistic(order, user_sale_statistic)

        # Create perms
        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, order.id, self.Meta.model)
        return order

    def update(self, instance, validated_data):
        # Split insert data
        data, perm_data = self.split_data(validated_data)
        # Get details data
        order_details_data = data.pop('order_detail', [])

        user_sale_statistic = self.validate_special_offer(data, order_details_data)

        # Update Order fields
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update OrderDetail
        current_details_id = [detail.id for detail in instance.order_detail.all()]
        new_details_id = []
        total_point = float(0)
        total_price = float(0)

        for detail_data in order_details_data:
            detail_id = detail_data.get('id')
            product_id = detail_data.get('product_id')
            quantity = detail_data.get('order_quantity')

            if detail_id:
                detail = OrderDetail.objects.get(id=detail_id, order_id=instance)
                for attr, value in detail_data.items():
                    setattr(detail, attr, value)
                detail.save()
            else:
                prices, point = self.calculate_price_and_point(instance, product_id, quantity)
                detail_data['product_price'] = prices
                detail_data['point_get'] = point
                detail = OrderDetail(order_id=instance, **detail_data)
                detail.save()
                detail_id = detail.id

            new_details_id.append(detail_id)
            total_point += detail.point_get
            total_price += detail.product_price

        # Remove OrderDetails not included in the update
        for detail_id in current_details_id:
            if detail_id not in new_details_id:
                OrderDetail.objects.filter(id=detail_id).delete()

        # Update order point and price
        instance.order_point = total_point
        instance.order_price = total_price
        instance.save()

        self.update_sale_statistic(instance, user_sale_statistic)

        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, instance.id, self.Meta.model)

        return instance

    def validate_special_offer(self, data, order_details_data):
        # Get user and phone from token
        user = data.get('client_id')
        # Get special offer
        special_offer = data.get('new_special_offer')
        # Validate Order if it was special_offer
        if special_offer:
            phones = PhoneNumber.objects.filter(user=user)
            # Check if SpecialOffer of livestream
            if (special_offer.live_stream is not None and
                    not LiveStreamOfferRegister.objects.filter(phone__in=phones, register=True).exists()):
                raise serializers.ValidationError({'message': 'Phone number not registered for LiveStream offer'})
            # Get current SaleStatistic of user
            today = timezone.now().date()
            first_day_of_month = today.replace(day=1)
            user_sale_statistic = SaleStatistic.objects.filter(user=user, month=first_day_of_month).first()
            # When user not have SaleStatistic, create new one
            if user_sale_statistic is None:
                user_sale_statistic = update_sale_statistics_for_user(user)
            print(f"Testing statistic: {user_sale_statistic.total_turnover}")
            # Calculate max box can buy
            number_box_can_buy = user_sale_statistic.available_turnover // special_offer.target
            # Validate each OrderDetail
            for detail_data in order_details_data:
                product_id = detail_data.get('product_id')
                order_box = detail_data.get('order_box')

                # Check if product is in SpecialOfferProduct
                if not SpecialOfferProduct.objects.filter(special_offer=special_offer, product_id=product_id).exists():
                    raise serializers.ValidationError(
                        {'message': f'Product {product_id} is not in the SpecialOfferProduct'})

                # Check if order_box is less than max_order_box
                special_offer_product = SpecialOfferProduct.objects.get(special_offer=special_offer,
                                                                        product_id=product_id)
                if special_offer_product.max_order_box and order_box > special_offer_product.max_order_box:
                    raise serializers.ValidationError({
                        'message': f'Order box {order_box} exceeds max order box {special_offer_product.max_order_box} for product {product_id}'})
            total_order_box = sum(item['order_box'] for item in order_details_data)

            if number_box_can_buy < total_order_box:
                raise serializers.ValidationError(
                    {'message': 'Not enough turnover', 'box_can_buy': str(number_box_can_buy)})
            return user_sale_statistic
        return None

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
        details = []
        for detail_data in order_details_data:
            quantity = detail_data.get('order_quantity')
            product_id = detail_data.pop('product_id')

            prices, point = self.calculate_price_and_point(order, product_id, quantity)

            detail_data['product_price'] = prices
            detail_data['point_get'] = point
            detail = OrderDetail(order_id=order, product_id=product_id, **detail_data)
            details.append(detail)
        return details

    @staticmethod
    def update_sale_statistic(order, user_sale_statistic):
        if user_sale_statistic:
            # Calculate used turnover based on SaleTarget for the month of order.created_at
            order_month = order.created_at.replace(day=1)
            sale_target = SaleTarget.objects.filter(month=order_month).first()

            if not sale_target:
                raise serializers.ValidationError({'message': f'No SaleTarget found for the month {order_month}'})

            used_turnover = sum(
                detail.order_box * sale_target.month_target
                for detail in order.order_detail.all()
            )

            user_sale_statistic.used_turnover += used_turnover
            user_sale_statistic.available_turnover = user_sale_statistic.total_turnover - user_sale_statistic.used_turnover
            user_sale_statistic.save()


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
    total_cashback = serializers.IntegerField(required=False)
