import json
import time
from datetime import datetime

import pandas as pd
import pytz
from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.db.models import Sum, F
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import AccessToken

from account.handlers.restrict_serializer import BaseRestrictSerializer
from account.handlers.validate_perm import ValidatePermRest
from account.models import PhoneNumber, User
from app.logs import app_log
from app.settings import TIME_ZONE
from marketing.livestream.models import LiveStreamOfferRegister
from marketing.order.models import Order, OrderDetail, SeasonalStatistic, SeasonalStatisticUser, \
    update_season_stats_users, create_or_get_sale_stats_user
from marketing.pick_number.models import UserJoinEvent
from marketing.price_list.models import ProductPrice, SpecialOfferProduct, SpecialOffer
from marketing.sale_statistic.models import SaleTarget, SaleStatistic, UserSaleStatistic
from system_func.models import PeriodSeason, PointOfSeason
from user_system.client_profile.models import ClientProfile
from user_system.employee_profile.models import EmployeeProfile
from utils.constants import so_type


class OrderDetailSerializer(BaseRestrictSerializer):
    product_name = serializers.CharField(source='product_id.name', read_only=True)

    class Meta:
        model = OrderDetail
        fields = ['product_id', 'product_name', 'order_quantity', 'order_box', 'product_price', 'point_get',
                  'price_so']


class OrderSerializer(BaseRestrictSerializer):
    order_detail = OrderDetailSerializer(many=True, allow_null=True)
    list_type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    status = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'order_point', 'order_price',
                            'is_so', 'id_so', 'id_offer_consider'
                            ]
        extra_kwargs = {
            'client_id': {
                'allow_null': True,
                'required': False
            },
            'new_special_offer': {
                'allow_null': True,
                'required': False
            }
        }

    def create(self, validated_data):
        # Split insert data
        data, perm_data = self.split_data(validated_data)
        client = data.get('client_id', None)
        if not client:
            raise ValidationError({'message': 'client_id field is required'})
        # Get order detail data
        order_details_data = data.pop('order_detail', [])
        # Validate product order details
        user_sale_statistic, is_so, is_consider = self.validate_special_offer(data, order_details_data)
        try:
            with transaction.atomic():
                price_list_id = data.get('price_list_id', None)
                # Validate orders
                if price_list_id is None:
                    raise ValidationError({'message': 'toa yêu cầu bảng giá'})
                if price_list_id.status == 'deactivate':
                    raise ValidationError({'message': 'bảng giá không hoạt động'})

                local_datetime = data.get('date_company_get')
                if datetime.utcoffset(local_datetime) is None:
                    # If date data not have timezone
                    local_datetime = pytz.utc.localize(local_datetime)
                # Change timezone to local
                local_timezone = pytz.timezone(TIME_ZONE)
                local_datetime = local_datetime.astimezone(local_timezone)

                data['date_company_get'] = local_datetime

                order = Order.objects.create(**data)

                # Add order_by
                order_by = update_order_by(self)
                if order_by:
                    order.created_by = order_by
                    order.save()

                # Calculate total price and point
                details = calculate_total_price_and_point(order, order_details_data)
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
                        special_offer: SpecialOffer = data.get('new_special_offer')
                        special_offer.status = 'deactivate'
                        special_offer.used = True
                        special_offer.save()

                    app_log.info(f"Testing user sale statistic: {user_sale_statistic}")

                    update_point(order.client_id)
                    update_season_stats_user(order.client_id, order.date_get)
                    order_month = order.date_get.replace(day=1)
                    user_stats = create_or_get_sale_stats_user(order.client_id, order_month)
                    print(user_stats)
                    update_user_turnover(order.client_id, order, order.is_so)
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
            raise e
            # raise serializers.ValidationError({'message': 'unexpected error'})

    def delete(self, instance):
        try:
            with transaction.atomic():
                print(f"Deleting")
                # Implement any custom logic before deletion here
                user = instance.client_id
                date_get = instance.date_get
                month = instance.date_get.replace(day=1)
                order = instance
                old_order_data = OrderSerializer(instance).data
                order.status = 'deactivate'
                # if instance.status == 'deactivate':
                #     print(f"Status deactivate")
                #     pass
                # else:
                #     print(f"Status active")
                #     user_stats = create_or_get_sale_stats_user(user, month)
                #     print(user_stats)
                # Delete related order details
                # Delete the order instance
                update_user_turnover(user, order, order.is_so, old_order_data)
                OrderDetail.objects.filter(order_id=instance).delete()
                instance.delete()
                update_point(user)
                update_season_stats_user(user, date_get)
                user_stats = create_or_get_sale_stats_user(user, month)
        except Exception as e:
            app_log.error(f"Error when deleting order: {e}")
            # raise serializers.ValidationError({'message': 'unexpected error during deletion'})
            raise e

    def validate_special_offer(self, data, order_details_data):
        # Get user and phone from token
        user = data.get('client_id')
        # Get special offer
        special_offer: SpecialOffer = data.get('new_special_offer', None)
        # Get current SaleStatistic of user
        get_date = data.get('date_get')
        first_day_of_month = get_date.replace(day=1)
        user_sale_statistic = create_or_get_sale_stats_user(user=user, month=first_day_of_month)
        if user_sale_statistic is None:
            user_sale_statistic, _ = SaleStatistic.objects.get_or_create(user=user, month=first_day_of_month)
        month_target = SaleTarget.objects.filter(month=first_day_of_month).first()

        user_sale_stats = UserSaleStatistic.objects.filter(user=user).first()
        if not user_sale_stats:
            user_sale_stats = UserSaleStatistic.objects.create(user=user)

        is_consider = False
        # Validate Order if it was special_offer
        if special_offer:
            # Validate permission
            if not special_offer.for_nvtt:
                validate_so_perm(special_offer, user)
            # Get phone of user
            phones = PhoneNumber.objects.filter(user=user)
            # Check if SpecialOffer of livestream
            if (special_offer.live_stream is not None and
                    not LiveStreamOfferRegister.objects.filter(phone__in=phones, register=True).exists()):
                raise serializers.ValidationError({'message': f'số điện thoại không nằm trong ưu đãi livestream'
                                                              f'{special_offer.live_stream.id}'})

            # Compare date
            get_date = datetime.combine(get_date, datetime.min.time())
            # time_start = special_offer.time_start.replace(tzinfo=None)
            # time_end = special_offer.time_end.replace(tzinfo=None)
            time_start = datetime.combine(special_offer.time_start.date(), datetime.min.time())
            time_end = datetime.combine(special_offer.time_end.date(), datetime.min.time())
            can_use = time_start <= get_date < time_end
            print(f"Test can user: {can_use}")
            print(f"Test: {time_start} <= {get_date} < {time_end}")
            if special_offer.status == 'deactivate' or special_offer.used is True or not can_use:
                raise serializers.ValidationError({'message': 'ưu đãi đã hết hạn'})

            buy_target = special_offer.target if special_offer.target >= 0 else month_target.month_target

            # Calculate max box can buy
            if special_offer.type_list == so_type.consider_user:
                is_consider = True
                # When ConsiderOffer, calculate via <SpecialOffer object> 'target' value
                # app_log.info(f"TEST:{user_sale_statistic.available_turnover} | {special_offer.target}")
                # number_box_can_buy = user_sale_statistic.available_turnover // special_offer.target
                # Validate if all products in order are belonged to SO consider
                order_product_ids = {str(detail_data.get('product_id').id) for detail_data in order_details_data}
                # Get list of product_id from SpecialOfferProduct
                special_offer_product_ids = set(
                    SpecialOfferProduct.objects.filter(special_offer=special_offer).values_list('product',
                                                                                                flat=True))
                if order_product_ids != special_offer_product_ids:
                    raise serializers.ValidationError(
                        {'message': 'sản phẩm trong toa không khớp với sản phẩm trong xét duyệt ưu đãi'})
            else:
                print(f"Check buy target: {buy_target}")
                # Normal SO use default target of SaleTarget by month
                number_box_can_buy = user_sale_statistic.available_turnover // buy_target

                # Validate turnover can buy number of box in Order
                total_order_box = sum(item['order_box'] for item in order_details_data)

                number_box_can_buy2 = user_sale_stats.turnover // buy_target

                # if number_box_can_buy < total_order_box:
                #     raise serializers.ValidationError(
                #         {'message': 'không đủ doanh số'})

                if number_box_can_buy2 < total_order_box:
                    raise serializers.ValidationError(
                        {'message': 'không đủ doanh số'})

            # Validate each OrderDetail
            for detail_data in order_details_data:
                product_id = detail_data.get('product_id')
                order_box = detail_data.get('order_box')

                # Check if product is in SpecialOfferProduct
                if not SpecialOfferProduct.objects.filter(special_offer=special_offer, product_id=product_id).exists():
                    raise serializers.ValidationError(
                        {'message': f'product {product_id} không tồn tại trong SpecialOfferProduct'})

                # Check if order_box is less than max_order_box
                special_offer_product = SpecialOfferProduct.objects.get(special_offer=special_offer,
                                                                        product_id=product_id)
                if special_offer.type_list == so_type.consider_user:
                    if special_offer_product.max_order_box and order_box != special_offer_product.max_order_box:
                        raise serializers.ValidationError({
                            'message': f'số thùng đặt {order_box} không khớp với {special_offer_product.max_order_box} thùng xem xét cho {product_id}'})
                else:
                    if special_offer_product.max_order_box and order_box > special_offer_product.max_order_box:
                        raise serializers.ValidationError({
                            'message': f"số thùng đặt {order_box} vượt quá lương tối đa {special_offer_product.max_order_box} cho sản phẩm {product_id}"})

            return user_sale_statistic, True, is_consider
        return user_sale_statistic, False, is_consider


def calculate_price_and_point(order, product_id, quantity):
    try:
        if order.new_special_offer:
            product_price = SpecialOfferProduct.objects.get(special_offer=order.new_special_offer,
                                                            product=product_id)
        else:
            product_price = ProductPrice.objects.get(price_list=order.price_list_id, product=product_id)
        prices, point, box = calculate_box_point(product_price, quantity)
    except (ProductPrice.DoesNotExist, SpecialOfferProduct.DoesNotExist):
        raise serializers.ValidationError({'message': 'sản phẩm không thuộc ưu đãi hoặc bảng giá'})
    return prices, point, box


def calculate_box_point(product_price, quantity):
    prices = float(product_price.price) * float(quantity) if product_price.price is not None else 0
    point = (float(product_price.point) * (quantity / product_price.quantity_in_box)
             if product_price.point is not None else 0)
    try:
        box = int(quantity) / int(product_price.quantity_in_box)
    except ZeroDivisionError:
        box = 0
    return prices, point, box


def calculate_total_price_and_point(order, order_details_data):
    details = []
    for detail_data in order_details_data:
        quantity = detail_data.get('order_quantity')
        product_id = detail_data.pop('product_id')

        prices, point, box = calculate_price_and_point(order, product_id, quantity)

        # Add result calculate to detail_data
        detail_data['product_price'] = prices
        detail_data['point_get'] = point
        detail_data['order_box'] = float(box)
        if order.is_so:
            so_obj = SpecialOfferProduct.objects.get(special_offer=order.new_special_offer, product=product_id)
            detail_data['price_so'] = so_obj.cashback

        # Prin logs
        app_log.info(f"Order details data: {detail_data}")

        # Assign temporary OrderDetail
        detail = OrderDetail(order_id=order, product_id=product_id, **detail_data)
        details.append(detail)
    return details


def update_order_by(self):
    request = self.context['request']

    try:
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
        try:
            user = request.user
            return user.id
        except Exception as e:
            return None


def validate_so_perm(special_offer, user):
    user_obj = User.objects.get(id=user)
    # ValidatePermRest(special_offer, user_obj)


class ProductStatisticsSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    product_name = serializers.CharField()
    current = serializers.DictField(required=False)
    one_year_ago = serializers.DictField(required=False)
    total_cashback = serializers.IntegerField(required=False)


class SeasonStatsUserPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeasonalStatisticUser
        exclude = ('total_turnover',)
        read_only_fields = ('redundant_point', 'total_point',)


class SeasonStatsUserPointRead(serializers.ModelSerializer):
    nvtt = serializers.SerializerMethodField()
    npp = serializers.SerializerMethodField()

    class Meta:
        model = SeasonalStatisticUser
        exclude = ('total_turnover', 'season_stats')
        read_only_fields = ('redundant_point', 'total_point',)

    def get_nvtt(self, obj):
        nvtt_id = obj.user.clientprofile.nvtt_id
        nvtt = User.objects.filter(id=nvtt_id).first()
        if nvtt:
            return nvtt.employeeprofile.register_name
        return None

    def get_npp(self, obj):
        npp = User.objects.filter(id=obj.npp_id).first()
        if npp:
            return npp.clientprofile.register_name
        return None


class SeasonalStatisticSerializer(serializers.ModelSerializer):
    # users_stats = serializers.SerializerMethodField()
    users = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    user_file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = SeasonalStatistic
        # exclude = ('users', )
        fields = '__all__'
        read_only_fields = ('id', 'created_by', 'created_at')
        extra_kwargs = {
            'note': {'allow_null': True}
        }

    def to_representation(self, instance: SeasonalStatistic):
        ret = super().to_representation(instance)
        ret['users'] = instance.users.filter().values_list('id', flat=True).distinct()
        request = self.context.get('request')

        if (request and request.method == 'GET'
                and hasattr(request, 'resolver_match')
                and request.resolver_match.kwargs.get('pk')):
            ret['users_stats'] = self.get_users_stats(instance)
        return ret

    def get_users_stats(self, obj):
        if obj.type == 'point':
            users_stats = SeasonalStatisticUser.objects.filter(season_stats=obj)
            serializer = SeasonStatsUserPointRead(users_stats, many=True)
            return serializer.data
        return []

    def create(self, validated_data):
        user_ids = validated_data.pop('users', [])
        user_file = validated_data.pop('user_file', None)

        try:
            if user_file:
                user_ids = self.handle_user_file(user_file)
            with transaction.atomic():
                instance = SeasonalStatistic.objects.create(**validated_data)
                self.update_users(instance, user_ids)
                return instance
        except Exception as e:
            # Log the exception if needed
            app_log.error(f"Error creating user: {e}")
            # Rollback transaction and re-raise the exception
            raise ValidationError({'message': 'lỗi bất ngờ khi create SeasonalStatistic', 'error': e})

    def update(self, instance, validated_data):
        user_ids = validated_data.pop('users', [])
        user_file = validated_data.pop('user_file', None)

        try:
            if user_file:
                user_ids = self.handle_user_file(user_file)
            with transaction.atomic():
                for attr, value in validated_data.items():
                    setattr(instance, attr, value)
                instance.save()
                self.update_users(instance, user_ids)
                return instance
        except Exception as e:
            # Log the exception if needed
            app_log.error(f"Error creating user: {e}")
            # Rollback transaction and re-raise the exception
            # raise ValidationError({'message': 'lỗi bất ngờ khi update SeasonalStatistic', 'error': e})
            raise e

    def handle_user_file(self, file):
        # Read the Excel file using pandas
        try:
            df = pd.read_excel(file, engine='openpyxl')
            # Clean data to ensure there are no NaN values where not expected
            df = df.fillna({'diem_1_tem': 0, 'so_tem': 0})  # Replace NaN with 0 in these columns
            df = df.dropna(subset=['maKH'])  # Ensure no NaN values in 'maKH'

            # Transform dataframe to the desired list of dictionaries format
            user_data = [
                {row['maKH']: {'turn_per_point': row['diem_1_tem'], 'turn_pick': row['so_tem']}}
                for index, row in df.iterrows()
            ]
            return user_data
        except Exception as e:
            raise ValidationError({'user_file': f'Failed to read file: {str(e)}'})

    def update_users(self, instance: SeasonalStatistic, user_ids: list):
        # Assign list for create objects
        create_stats_users = list()
        update_stats_users = list()
        print(f"Test: {user_ids}")
        exclude_user_ids = list()
        for user_id in user_ids:
            if isinstance(user_id, str):
                # Validate user exists
                user = User.objects.filter(id=user_id)
                if not user.exists():
                    continue
                # Get objects SeasonalStatisticUser for handling
                stats_user = SeasonalStatisticUser.objects.filter(user_id=user_id, season_stats=instance)
                # Not existed, add to create list
                if not stats_user.exists():
                    new_statistic_user = SeasonalStatisticUser(user_id=user_id, season_stats=instance)
                    new_statistic_user = update_season_stats_users(new_statistic_user)
                    create_stats_users.append(new_statistic_user)
                # Existed, update stats
                else:
                    upd_stats_user = update_season_stats_users(stats_user.first())
                    update_stats_users.append(upd_stats_user)
                exclude_user_ids.append(user_id)
            elif isinstance(user_id, dict):
                # Get user id from dict user data
                user_data = user_id
                my_user_id = list(user_data.keys())[0]
                # Validate user id
                user = User.objects.filter(id=my_user_id)
                if not user.exists():
                    continue
                # Get data of user dict
                input_data = user_data[my_user_id]
                # Query season user stats
                stats_user = SeasonalStatisticUser.objects.filter(user_id=my_user_id, season_stats=instance)
                # Prepare input data
                turn_per_point = input_data['turn_per_point']
                turn_pick = input_data['turn_pick']
                # Create when stats user not exits
                if not stats_user.exists():
                    new_statistic_user = SeasonalStatisticUser(
                        user_id=my_user_id, season_stats=instance, turn_pick=turn_pick, turn_per_point=turn_per_point)
                    # Update total point
                    new_statistic_user = update_season_stats_users(new_statistic_user)
                    # Add stats object to bulk create list
                    create_stats_users.append(new_statistic_user)
                # Existed, update stats
                else:
                    # Get stats
                    stats_user = stats_user.first()
                    # Update turn_pick and turn_per_point
                    stats_user.turn_pick = turn_pick
                    stats_user.turn_per_point = turn_per_point
                    # Update total point and redundant point
                    upd_stats_user = update_season_stats_users(stats_user)
                    # Add stats object to update bulk list
                    update_stats_users.append(upd_stats_user)
                exclude_user_ids.append(my_user_id)
            else:
                raise ValidationError({'message': 'user_ids not acceptable type'})
        # Remove un-use user
        SeasonalStatisticUser.objects.filter(season_stats=instance).exclude(user_id__in=exclude_user_ids).delete()
        # Create all users stats on create list
        print("Im update here")
        SeasonalStatisticUser.objects.bulk_create(create_stats_users)
        SeasonalStatisticUser.objects.bulk_update(update_stats_users,
                                                  ['turn_per_point', 'turn_pick', 'redundant_point', 'total_point'])


class SpecialOfferUsageSerializer(serializers.ModelSerializer):
    time_used = serializers.SerializerMethodField()
    orders_used = serializers.SerializerMethodField()
    total_used_box = serializers.SerializerMethodField()

    class Meta:
        model = SpecialOffer
        fields = ['id', 'time_used', 'orders_used', 'total_used_box']

    def get_time_used(self, obj):
        orders = Order.objects.filter(new_special_offer=obj)
        return orders.count()

    def get_orders_used(self, obj):
        orders = Order.objects.filter(new_special_offer=obj)
        return [order.id for order in orders]

    def get_total_used_box(self, obj):
        order_ids = Order.objects.filter(new_special_offer=obj).values_list('id', flat=True)
        total_box = OrderDetail.objects.filter(order_id__in=order_ids).aggregate(
            total_box=Sum('order_box'))['total_box'] or 0
        return total_box


def update_point(user):
    period = PeriodSeason.objects.filter(type='point', period='current').first()
    point, _ = PointOfSeason.objects.get_or_create(user=user, period=period)
    point.auto_point()
    point.save()


def update_season_stats_user(user: User, date_get):
    season_stats_users = SeasonalStatisticUser.objects.filter(
        user=user,
        season_stats__type='point',
        season_stats__start_date__lte=date_get,
        season_stats__end_date__gte=date_get
    )

    if season_stats_users.exists():
        update_stats_users = []

        for stats_user in season_stats_users:
            updated_stats_user = update_season_stats_users(stats_user)
            update_stats_users.append(updated_stats_user)

            user_join_events = UserJoinEvent.objects.filter(user=user, event__table_point=stats_user.season_stats)
            for user_join_event in user_join_events:
                user_join_event.turn_per_point = updated_stats_user.turn_per_point
                user_join_event.turn_pick = updated_stats_user.turn_pick
                user_join_event.total_point = updated_stats_user.total_point
                user_join_event.save()

        SeasonalStatisticUser.objects.bulk_update(update_stats_users,
                                                  ['turn_per_point', 'turn_pick', 'redundant_point', 'total_point'])


def update_user_turnover(user: User, order: Order, is_so: bool, old_order=None, *args, **kwargs):
    if old_order is None:
        old_order = {}
    if order.nvtt_id == '' or order.nvtt_id is None:
        return
    today = datetime.now().date()
    first_date_of_month = today.replace(day=1)
    last_date_of_month = first_date_of_month + relativedelta(months=1) - relativedelta(days=1)
    in_range = first_date_of_month <= order.date_get <= last_date_of_month
    app_log.info(f"Check in range: {order.id} - {in_range}")
    if not in_range:
        app_log.info(f"Not in_range reutrn None")
        return
    user_sale_stats = UserSaleStatistic.objects.filter(user=user).first()
    if not user_sale_stats:
        user_sale_stats = UserSaleStatistic.objects.create(user=user)

    totals = order.order_detail.filter().aggregate(
        total_box=Sum('order_box'),
        total_price=Sum('product_price')
    )
    print(f"Total: {totals}")
    total_box = totals['total_box'] if totals['total_box'] is not None else 0

    total_price = totals['total_price'] if totals['total_price'] is not None else 0

    old_turnover = old_order.get('order_price', 0)
    old_status = old_order.get('status', 'active')
    so_data = kwargs.get('so_data', {})
    print(f"so_data: {so_data.get('minus', None)}")
    print(f"so_data: {so_data.get('count', None)}")
    if is_so:
        print("Is special offer")
        # order.new_special_offer.type_list != so_type.consider_user:
        first_date = order.date_get.replace(day=1)
        sale_target, _ = SaleTarget.objects.get_or_create(month=first_date)
        if so_data.get('minus', None) is not None and isinstance(so_data.get('minus'), (int, float)):
            target = so_data.get('minus')
        elif so_data.get('minus', None) == 'x':
            target = sale_target.month_target
        else:
            try:
                so_target = order.new_special_offer.target
                target = so_target if so_target >= 0 else sale_target.month_target
            except AttributeError:
                target = sale_target.month_target
        # print(f"|__ Fix target: {target} | {so_target}")
        fix_price = (target * total_box)
        print(f"|__ Fix price: {fix_price}")

        count_turnover = False
        if order.new_special_offer is not None:
            if order.new_special_offer.count_turnover:
                count_turnover = order.new_special_offer.count_turnover
        elif so_data.get('count', None) not in ['', 'nan', None]:
            count_turnover = so_data.get('count')
        else:
            count_turnover = False

        if count_turnover is False:
            if order.status == 'deactivate':
                user_sale_stats.turnover += fix_price
            else:
                user_sale_stats.turnover -= fix_price
        else:
            if order.status == 'deactivate':
                user_sale_stats.turnover += fix_price - total_price
            else:
                user_sale_stats.turnover += total_price - fix_price
        print(f"|__ Final turnover: {user_sale_stats.turnover}")
    else:
        if so_data.get('count', None) not in ['', 'nan', None]:
            if not so_data.get('count'):
                pass
            else:
                user_sale_stats.turnover += total_price
        else:
            if order.status == 'deactivate':
                print(f"Test old turnover: {old_turnover}")
                user_sale_stats.turnover -= old_turnover
            else:
                if old_status == 'active':
                    user_sale_stats.turnover += (total_price - old_turnover)
                if old_status == 'deactivate':
                    user_sale_stats.turnover += total_price
    print(f"TEST DATA: {old_turnover} | {user_sale_stats.turnover}")
    user_sale_stats.save()


class OrderUpdateSerializer(BaseRestrictSerializer):
    order_detail = OrderDetailSerializer(many=True, allow_null=True)
    list_type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    status = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'order_point', 'order_price',
                            'is_so', 'id_so', 'id_offer_consider'
                            ]
        extra_kwargs = {
            'client_id': {
                'allow_null': True,
                'required': False
            },
            'new_special_offer': {
                'allow_null': True,
                'required': False
            }
        }

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        nvtt_id = instance.nvtt_id if instance.nvtt_id else instance.client_id.clientprofile.nvtt_id

        nvtt = EmployeeProfile.objects.filter(employee_id=nvtt_id).first()
        nvtt_name = nvtt.register_name if nvtt else None
        client_lv1 = ClientProfile.objects.filter(client_id=instance.npp_id).first()

        client_lv1_name = client_lv1.register_name if client_lv1 else None

        client_info = {
            'id': instance.client_id.id if instance.client_id else '',
            'name': instance.client_id.clientprofile.register_name,
            'nvtt': nvtt_name,
            'register_lv1': client_lv1_name
        }
        ret['clients'] = client_info
        return ret

    def update(self, instance: Order, validated_data):
        # Split insert data
        data, perm_data = self.split_data(validated_data)
        # Get order detail data
        order_details_data = data.pop('order_detail', None)

        with transaction.atomic():
            # Update Order fields
            data.pop('client_id', None)
            data.pop('new_special_offer', None)
            for attr, value in data.items():
                setattr(instance, attr, value)
            instance.save()

            # Update OrderDetail
            current_details_id = [detail.id for detail in instance.order_detail.all()]
            new_details_id = []
            total_point = float(0)
            total_price = float(0)
            old_order_data = OrderSerializer(instance).data
            # Update order details
            if order_details_data:
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
                        prices, point, box = calculate_price_and_point(instance, product_id, quantity)
                        detail_data['product_price'] = prices
                        detail_data['point_get'] = point
                        detail_data['order_box'] = float(box)
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
            # app_log.info(f"Testing user sale statistic: {user_sale_statistic}")
            update_point(instance.client_id)
            update_season_stats_user(instance.client_id, instance.date_get)
            order_month = instance.date_get.replace(day=1)
            user_stats = create_or_get_sale_stats_user(instance.client_id, order_month)
            update_user_turnover(instance.client_id, instance, instance.is_so, old_order_data)
            print(user_stats)
            restrict = perm_data.get('restrict')
            if restrict:
                self.handle_restrict(perm_data, instance.id, self.Meta.model)

        return instance
