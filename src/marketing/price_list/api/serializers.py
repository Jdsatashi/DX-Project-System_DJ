from django.conf import settings
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from account.handlers.perms import get_full_permname, get_perm_name
from account.handlers.restrict_serializer import BaseRestrictSerializer
from account.models import GroupPerm, Perm
from account.queries import get_user_by_permname_sql, get_user_like_permname_sql
from app.logs import app_log
from marketing.price_list.models import PriceList, ProductPrice, SpecialOfferProduct, SpecialOffer
from marketing.product.models import Product
from utils.constants import so_type_list, perm_actions, so_type


class ProductPriceSerializer(serializers.ModelSerializer):
    product_id = serializers.CharField(write_only=True)
    price = serializers.FloatField()
    point = serializers.FloatField()

    class Meta:
        model = ProductPrice
        fields = '__all__'
        read_only_fields = ('id', 'price_list', 'product')

    def to_internal_value(self, data):
        # Ensure that `product_id` remains a string
        product_id = data.get('product_id')
        if not isinstance(product_id, str):
            raise serializers.ValidationError({
                'message': 'Product ID must be a string.'
            })

        return super().to_internal_value(data)


class ProductReadSerializer(serializers.ModelSerializer):
    product_type = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'product_type', 'category']

    @staticmethod
    def get_product_type(obj):
        if not obj.product_type:
            return None
        return obj.product_type.name


class ProductPriceReadSerializer(serializers.ModelSerializer):
    product = ProductReadSerializer(read_only=True)
    price = serializers.FloatField()
    point = serializers.FloatField()

    class Meta:
        model = ProductPrice
        fields = ['product', 'price', 'quantity_in_box', 'point']


class PriceListSerializer(BaseRestrictSerializer):
    products = ProductPriceSerializer(many=True, write_only=True, required=False, allow_null=True)
    import_users = serializers.FileField(required=False)

    class Meta:
        model = PriceList
        fields = '__all__'
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def to_representation(self, instance):
        """Modify the output representation based on the context."""
        ret = super().to_representation(instance)
        request = self.context.get('request')
        if (request and request.method == 'GET'
                and hasattr(request, 'resolver_match')
                and request.resolver_match.kwargs.get('pk')):
            products_list_serializer = ProductPriceReadSerializer(instance.productprice_set.all(), many=True)
            ret['products_list'] = products_list_serializer.data
            # Get user added in price list
            perm_name = get_full_permname(self.Meta.model, 'create', instance.id)
            user_group = get_user_by_permname_sql(perm_name)
            user_manage = list(user_group)
            ret['users'] = user_manage
            groups_user = GroupPerm.objects.filter(perm__name=perm_name).values_list('display_name',
                                                                                     flat=True).distinct()
            ret['groups'] = list(groups_user)
        return ret

    def validate(self, data):
        """
        Validate to ensure only one PriceList with type 'main' exists within the given date range.
        """
        date_start = data.get('date_start')
        date_end = data.get('date_end')
        price_list_type = data.get('type')
        if price_list_type == 'main':
            overlapping_price_lists = PriceList.objects.filter(
                type='main',
                date_start__lte=date_end,
                date_end__gte=date_start,
            ).exclude(id=self.instance.id if self.instance else None)

            if overlapping_price_lists.exists():
                raise serializers.ValidationError(
                    {'message': 'Chỉ có thể có một bảng giá chính (type="main") trong khoảng thời gian đã chọn.'}
                )
        return data

    def create(self, validated_data):
        # Split data for permission
        data, perm_data = self.split_data(validated_data)
        import_users = data.pop('import_users', None)

        try:
            with transaction.atomic():
                # Create price list
                price_list = PriceList.objects.create(**data)

                user_actions = [perm_actions['view'], perm_actions['create']]
                self.handle_restrict_import_users_id(import_users, perm_data, user_actions)

                # Add permission
                restrict = perm_data.get('restrict')
                if restrict:
                    self.handle_restrict(perm_data, price_list.id, self.Meta.model)
                return price_list
        except Exception as e:
            app_log.error(f"Error when create price_list: {e}")
            if settings.DEBUG:
                raise e
            else:
                raise serializers.ValidationError({'message': 'unexpected error'})

    def update(self, instance, validated_data):
        data, perm_data = self.split_data(validated_data)
        import_users = data.pop('import_users', None)

        try:
            with transaction.atomic():
                for attr, value in data.items():
                    setattr(instance, attr, value)
                instance.save()

                user_actions = [perm_actions['view'], perm_actions['create']]
                self.handle_restrict_import_users_id(import_users, perm_data, user_actions)

                # Handle permissions if needed
                restrict = perm_data.get('restrict')
                if restrict:
                    self.handle_restrict(perm_data, instance.id, self.Meta.model)

                return instance
        except Exception as e:
            app_log.error(f"Error when update price_list: {e}")
            if settings.DEBUG:
                raise e
            else:
                raise serializers.ValidationError({'message': 'unexpected error'})

    def check_user_or_group_perm(self, allow_users, allow_nhom, date_start, date_end, price_list_type):
        if price_list_type != 'sub':
            return

        if allow_users:
            for user_id in allow_users:
                overlapping_price_lists = PriceList.objects.filter(
                    type='sub',
                    date_start__lte=date_end,
                    date_end__gte=date_start,
                    created_by=user_id
                ).distinct()

                if overlapping_price_lists.exists():
                    raise ValidationError({
                        'message': f'User {user_id} is already applied to a PriceList in the same date range.'
                    })

        if allow_nhom:
            for group_name in allow_nhom:
                group_users = get_user_like_permname_sql(group_name)
                overlapping_price_lists = PriceList.objects.filter(
                    type='sub',
                    date_start__lte=date_end,
                    date_end__gte=date_start,
                    created_by__in=group_users
                    # Giả định rằng `created_by` là ID của user, bạn có thể điều chỉnh theo model của bạn
                ).distinct()

                if overlapping_price_lists.exists():
                    raise ValidationError({
                        'message': f'Group {group_name} is already applied to a PriceList in the same date range.'
                    })


class PriceList2Serializer(serializers.ModelSerializer):
    class Meta:
        model = PriceList
        # fields = '__all__'
        exclude = ('created_by', 'created_at', 'updated_at', 'products')

    def to_representation(self, instance):
        """Modify the output representation based on the context."""
        ret = super().to_representation(instance)
        products_list_serializer = ProductPriceReadSerializer(instance.productprice_set.all(), many=True)
        ret['products_list'] = products_list_serializer.data

        perm_name = get_full_permname(self.Meta.model, 'create', instance.id)
        user_group = get_user_by_permname_sql(perm_name)
        user_manage = list(user_group)
        ret['users'] = user_manage
        return ret


class SpecialOfferProductSerializer(serializers.ModelSerializer):
    max_order_box = serializers.IntegerField(default=3)

    class Meta:
        model = SpecialOfferProduct
        fields = '__all__'
        read_only_fields = ['id']


class SpecialOfferSerializer(BaseRestrictSerializer):
    import_users = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = SpecialOffer
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def to_representation(self, instance):
        """Modify the output representation based on the context."""
        ret = super().to_representation(instance)
        request = self.context.get('request')
        if (request and request.method == 'GET'
                and hasattr(request, 'resolver_match')
                and request.resolver_match.kwargs.get('pk')):
            special_offers = SpecialOfferProductSerializer(instance.special_offers.all(), many=True)
            ret['special_offers'] = special_offers.data
            # Get user added in price list
            perm_name = get_full_permname(self.Meta.model, 'create', instance.id)
            user_group = get_user_by_permname_sql(perm_name)
            user_manage = list(user_group)
            ret['users'] = user_manage
            groups_user = GroupPerm.objects.filter(perm__name=perm_name).values_list('display_name',
                                                                                     flat=True).distinct()
            ret['groups'] = list(groups_user)
        return ret

    def create(self, validated_data):
        # Split insert data
        data, perm_data = self.split_data(validated_data)
        import_users = data.pop('import_users', None)
        try:
            with transaction.atomic():
                if data.get('type_list') not in so_type_list:
                    raise ValidationError({'message': f'type_list phải thuộc danh sách {so_type_list}'})
                # Create new SpecialOffer
                special_offer = SpecialOffer.objects.create(**data)

                if special_offer.type_list == so_type.manual:
                    user_actions = [perm_actions['view'], perm_actions['create']]
                    self.handle_restrict_import_users_id(import_users, perm_data, user_actions)
                # Create perm for data
                restrict = perm_data.get('restrict')
                if restrict:
                    self.handle_restrict(perm_data, special_offer.id, self.Meta.model)
                return special_offer
        except Exception as e:
            app_log.error(f"Error when create special offer: {e}")
            if settings.DEBUG:
                raise e
            else:
                raise serializers.ValidationError({'message': 'unexpected error when create special offer'})

    def update(self, instance: SpecialOffer, validated_data):
        # Split insert data
        data, perm_data = self.split_data(validated_data)
        import_users = data.pop('import_users', None)
        try:
            with transaction.atomic():
                # Update SpecialOffer fields
                count_turnover = data.get('count_turnover')
                target = data.get('target')
                orders = instance.orders
                if orders.exists():
                    if target != instance.target:
                        message = f'Không thể thay đổi chỉ tiêu cho ưu đãi đã được sử dụng'
                        raise ValidationError({
                            'message': message,
                            'detail': {
                                'orders': orders.values_list('id', flat=True)
                            }
                        })
                    if count_turnover != instance.count_turnover:
                        message = f'Không thể thay đổi tính doanh số cho ưu đãi đã được sử dụng'
                        raise ValidationError({
                            'message': message,
                            'detail': {
                                'orders': orders.values_list('id', flat=True)
                            }
                        })
                for attr, value in data.items():
                    setattr(instance, attr, value)
                instance.save()

                # if instance.for_nvtt:
                # perm_data['groups'] = ['nvtt']
                if instance.type_list == so_type.manual:
                    user_actions = [perm_actions['view'], perm_actions['create']]
                    self.handle_restrict_import_users_id(import_users, perm_data, user_actions)

                restrict = perm_data.get('restrict')
                perm_name = get_perm_name(self.Meta.model)
                perm_name = perm_name + f"_{instance.id}"
                if restrict or Perm.objects.filter(name__endswith=perm_name).exists():
                    self.handle_restrict(perm_data, instance.id, self.Meta.model)
                return instance
        except ValidationError as ve:
            app_log.error(f"Error when update special offer: {ve}")
            raise ve
        except Exception as e:
            app_log.error(f"Error when update special offer: {e}")
            if settings.DEBUG:
                raise e
            else:
                raise serializers.ValidationError({'message': f'unexpected error when update special offer {instance.id}'})
            # raise e


"""
# create special offer for nvtt
    if special_offer.for_nvtt:
        users = perm_data.pop('allow_users', None)
        if users is None:
            raise ValidationError({'message': 'special offer cho nvtt yêu cầu allow_users'})
        users = [user.upper() for user in users]
        nvtt_ids = User.objects.filter(id__in=users).values_list('clientprofile__nvtt_id', flat=True).distinct()
        print(f"Test READ ONLY USER: {list(nvtt_ids)}")
        perm_data['read_only_users'] = list(nvtt_ids)
        perm_data['hide_users'] = users
        perm_data['allow_users'] = users + list(nvtt_ids)
"""
