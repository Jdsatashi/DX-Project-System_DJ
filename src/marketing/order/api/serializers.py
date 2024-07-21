from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import AccessToken

from account.handlers.restrict_serializer import BaseRestrictSerializer
from account.handlers.validate_perm import ValidatePermRest
from account.models import PhoneNumber, User
from app.logs import app_log
from marketing.livestream.models import LiveStreamOfferRegister
from marketing.order.models import Order, OrderDetail
from marketing.price_list.models import ProductPrice, SpecialOfferProduct
from marketing.sale_statistic.models import SaleStatistic, SaleTarget
from user_system.client_profile.models import ClientProfile


class OrderDetailSerializer(BaseRestrictSerializer):
    product_name = serializers.CharField(source='product_id.name', read_only=True)

    class Meta:
        model = OrderDetail
        fields = ['product_id', 'product_name', 'order_quantity', 'order_box', 'product_price', 'point_get',
                  'price_list_so']


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
        user_sale_statistic, is_so, is_consider = self.validate_special_offer(data, order_details_data)
        try:
            with transaction.atomic():
                price_list_id = data.get('price_list_id', None)
                if price_list_id is None:
                    raise ValidationError({'message': 'toa yêu cầu bảng giá'})
                if price_list_id.status == 'deactivate':
                    raise ValidationError({'message': 'bảng giá không hoạt động'})
                order = Order.objects.create(**data)
                order_by = self.update_order_by()
                if order_by:
                    order.created_by = order_by
                    order.save()
                # Calculate total price and point
                details = self.calculate_total_price_and_point(order, order_details_data)
                if details:
                    OrderDetail.objects.bulk_create(details)
                    # Check if order details were created
                    created_details_count = OrderDetail.objects.filter(order_id=order).count()
                    if created_details_count == 0:
                        order.delete()
                        raise ValidationError(
                            {'message': 'toa yêu cầu chi tiết danh sách sản phẩm, số lượng sản phẩm'}
                        )

                    # Get total point and price from query
                    total_price = OrderDetail.objects.filter(order_id=order).aggregate(
                        total_price=Sum('product_price'))['total_price']
                    total_point = OrderDetail.objects.filter(order_id=order).aggregate(
                        total_point=Sum('point_get'))['total_point']
                    # Add to order
                    order.order_point = total_point
                    order.order_price = total_price
                    order.save()

                    # Deactivate when user used
                    if is_consider:
                        special_offer = data.get('new_special_offer')
                        special_offer.status = 'deactivate'
                        special_offer.save()

                    app_log.info(f"Testing user sale statistic: {user_sale_statistic}")
                    self.update_sale_statistic(order, user_sale_statistic, order.order_price, is_so, is_consider)

                    # Create perms
                    restrict = perm_data.get('restrict')
                    if restrict:
                        self.handle_restrict(perm_data, order.id, self.Meta.model)
                else:
                    raise ValidationError(
                        {'message': 'toa yêu cầu chi tiết danh sách sản phẩm, số lượng sản phẩm'},
                    )
            return order
        except Exception as e:
            app_log.error(f"Error when create order: {e}")
            raise serializers.ValidationError({'message': 'unexpected error'})

    def update(self, instance, validated_data):
        # Split insert data
        data, perm_data = self.split_data(validated_data)
        # Get order detail data
        order_details_data = data.pop('order_detail', [])

        user_sale_statistic, is_so, is_consider = self.validate_special_offer(data, order_details_data)

        with transaction.atomic():
            # Update Order fields
            for attr, value in data.items():
                setattr(instance, attr, value)
            instance.save()
            order_by = self.update_order_by()
            if order_by:
                instance.created_by = instance.created_by + f"|{order_by}"
                instance.save()

            # Update OrderDetail
            current_details_id = [detail.id for detail in instance.order_detail.all()]
            new_details_id = []
            total_point = float(0)
            total_price = float(0)

            # Update order details
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
            app_log.info(f"Testing user sale statistic: {user_sale_statistic}")
            self.update_sale_statistic(instance, user_sale_statistic, instance.order_price, is_so, is_consider)

            restrict = perm_data.get('restrict')
            if restrict:
                self.handle_restrict(perm_data, instance.id, self.Meta.model)

        return instance

    def validate_special_offer(self, data, order_details_data):
        # Get user and phone from token
        user = data.get('client_id')
        # Get special offer
        special_offer = data.get('new_special_offer')
        # Get current SaleStatistic of user
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        user_sale_statistic, _ = SaleStatistic.objects.get_or_create(user=user, month=first_day_of_month)
        month_target = SaleTarget.objects.filter(month=first_day_of_month).first()
        is_consider = False
        # Validate Order if it was special_offer
        if special_offer:
            # Validate permission
            self.validate_so_perm(special_offer, user)
            # Get phone of user
            phones = PhoneNumber.objects.filter(user=user)
            # Check if SpecialOffer of livestream
            if (special_offer.live_stream is not None and
                    not LiveStreamOfferRegister.objects.filter(phone__in=phones, register=True).exists()):
                raise serializers.ValidationError({'error': f'số điện thoại không nằm trong ưu đãi livestream'
                                                            f'{special_offer.live_stream.id}'})

            if special_offer.status == 'deactivate':
                raise serializers.ValidationError({'error': 'ưu đãi đã hết hạn'})

            # Calculate max box can buy
            if special_offer.type_list == 'consider_offer_user':
                is_consider = True
                # When ConsiderOffer, calculate via <SpecialOffer object> 'target' value
                app_log.info(f"TEST:{user_sale_statistic.available_turnover} | {special_offer.target}")
                number_box_can_buy = user_sale_statistic.available_turnover // special_offer.target
                # Validate if all products in order are belonged to SO consider
                order_product_ids = {str(detail_data.get('product_id').id) for detail_data in order_details_data}
                # Get list of product_id from SpecialOfferProduct
                special_offer_product_ids = set(
                    SpecialOfferProduct.objects.filter(special_offer=special_offer).values_list('product',
                                                                                                flat=True))
                if order_product_ids != special_offer_product_ids:
                    raise serializers.ValidationError(
                        {'error': 'sản phẩm trong toa không khớp với sản phẩm trong xét duyệt ưu đãi'})
            else:
                # Normal SO use default target of SaleTarget by month
                number_box_can_buy = user_sale_statistic.available_turnover // month_target.month_target

            # Validate turnover can buy number of box in Order
            total_order_box = sum(item['order_box'] for item in order_details_data)
            if number_box_can_buy < total_order_box:
                raise serializers.ValidationError(
                    {'error': 'không đủ doanh số', 'box_can_buy': str(number_box_can_buy)})

            # Validate each OrderDetail
            for detail_data in order_details_data:
                product_id = detail_data.get('product_id')
                order_box = detail_data.get('order_box')

                # Check if product is in SpecialOfferProduct
                if not SpecialOfferProduct.objects.filter(special_offer=special_offer, product_id=product_id).exists():
                    raise serializers.ValidationError(
                        {'error': f'product {product_id} không tồn tại trong SpecialOfferProduct'})

                # Check if order_box is less than max_order_box
                special_offer_product = SpecialOfferProduct.objects.get(special_offer=special_offer,
                                                                        product_id=product_id)
                if special_offer.type_list == 'consider_offer_user':
                    if special_offer_product.max_order_box and order_box != special_offer_product.max_order_box:
                        raise serializers.ValidationError({
                            'message': f'số thùng đặt {order_box} không khớp với {special_offer_product.max_order_box} thùng xem xét cho {product_id}'})
                else:
                    if special_offer_product.max_order_box and order_box > special_offer_product.max_order_box:
                        raise serializers.ValidationError({
                            'message': f"số thùng đặt {order_box} vượt quá lương tối đa {special_offer_product.max_order_box} cho sản phẩm {product_id}"})

            return user_sale_statistic, True, is_consider
        return user_sale_statistic, False, is_consider

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
            raise serializers.ValidationError({'error': 'sản phẩm không thuộc ưu đãi hoặc bảng giá'})
        return prices, point

    def calculate_total_price_and_point(self, order, order_details_data):
        details = []
        for detail_data in order_details_data:
            quantity = detail_data.get('order_quantity')
            product_id = detail_data.pop('product_id')

            prices, point = self.calculate_price_and_point(order, product_id, quantity)

            # Add result calculate to detail_data
            detail_data['product_price'] = prices
            detail_data['point_get'] = point

            if order.is_so:
                so_obj = SpecialOfferProduct.objects.get(special_offer=order.new_special_offer, product=product_id)
                detail_data['price_list_so'] = so_obj.cashback

            # Prin logs
            app_log.info(f"Order details data: {detail_data}")

            # Assign temporary OrderDetail
            detail = OrderDetail(order_id=order, product_id=product_id, **detail_data)
            details.append(detail)
        return details

    @staticmethod
    def update_sale_statistic(order, user_sale_statistic, total_price, is_so, is_consider):
        if user_sale_statistic:
            # Calculate used turnover based on SaleTarget for the month of order.created_at
            order_month = order.date_get.replace(day=1)
            sale_target = SaleTarget.objects.filter(month=order_month).first()

            if not sale_target:
                raise serializers.ValidationError({'message': f'không tìm thấy doanh số tháng {order_month}'})
            if is_so:
                target = order.new_special_offer.target
                target = target if target != 0 else sale_target.month_target
                app_log.info(f"TESTING TARGET: {target}")

                used_turnover = sum(
                    detail.order_box * target
                    for detail in order.order_detail.all()
                )
                if order.new_special_offer.count_turnover:
                    user_sale_statistic.total_turnover += total_price

                user_sale_statistic.used_turnover += used_turnover
                user_sale_statistic.available_turnover = user_sale_statistic.total_turnover - user_sale_statistic.used_turnover
                user_sale_statistic.save()
            else:
                user_sale_statistic.total_turnover += total_price
                user_sale_statistic.available_turnover = user_sale_statistic.total_turnover - user_sale_statistic.used_turnover
                user_sale_statistic.save()

    def update_order_by(self):
        try:
            request = self.context['request']
            auth_header = request.headers.get('Authorization')

            access_token = auth_header.split(' ')[1]

            # Decode access token
            token = AccessToken(str(access_token))
            # Decode token
            phone_number = token.get('phone_number')
            app_log.info(f"Order by user {phone_number}")
            return str(phone_number)
        except Exception as e:
            app_log.error(f"Get error at order by")
            pass

    def validate_so_perm(self, special_offer, user):
        user_obj = User.objects.get(id=user)
        ValidatePermRest(special_offer, user_obj)


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


class ClientProfileSerializer(serializers.ModelSerializer):
    nvtt = serializers.CharField(source='nvtt.register_name', read_only=True)
    register_lv1 = serializers.CharField(source='register_lv1.register_name', read_only=True)

    class Meta:
        model = ClientProfile
        fields = ['id', 'register_name', 'nvtt', 'register_lv1']


class Order3Serializer(serializers.Serializer):
    id = serializers.CharField()
    date_get = serializers.DateField()
    date_company_get = serializers.DateTimeField()
    date_delay = serializers.IntegerField()
    id_offer_consider = serializers.CharField
    order_point = serializers.FloatField()
    order_price = serializers.FloatField()
    note = serializers.CharField()
    created_at = serializers.DateTimeField


class OrderDetail3Serializer(serializers.Serializer):
    product_id = serializers.CharField()
    order_quantity = serializers.FloatField()
    order_box = serializers.FloatField()
    product_price = serializers.IntegerField()
    point_get = serializers.FloatField()
    note = serializers.CharField()
