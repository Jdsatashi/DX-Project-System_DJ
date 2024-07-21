import time

from django.db import transaction
from django.db.models import Q
from rest_framework import serializers

from account.handlers.perms import get_full_permname, get_user_by_permname
from account.handlers.restrict_serializer import BaseRestrictSerializer
from account.models import GroupPerm, User
from account.queries import get_user_by_permname_sql
from app.logs import app_log
from marketing.price_list.models import PriceList, ProductPrice, PointOfSeason, SpecialOfferProduct, SpecialOffer
from marketing.product.models import Product


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
        return obj.product_type.name


class ProductPriceReadSerializer(serializers.ModelSerializer):
    product = ProductReadSerializer(read_only=True)
    price = serializers.FloatField()
    point = serializers.FloatField()

    class Meta:
        model = ProductPrice
        fields = ['product', 'price', 'quantity_in_box', 'point']


class PriceListSerializer(BaseRestrictSerializer):
    products = ProductPriceSerializer(many=True, write_only=True, required=False)

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
        # Split data products from serializer
        products_data = data.pop('products', [])
        try:
            with transaction.atomic():
                # Create price list
                price_list = PriceList.objects.create(**data)
                # Add product to price list
                for product_data in products_data:
                    product_id = product_data.pop('product_id')
                    price = product_data.pop('price')
                    quantity_in_box = product_data.pop('quantity_in_box')
                    point = product_data.pop('point')
                    try:
                        product = Product.objects.get(id=str(product_id))
                        ProductPrice.objects.create(price_list=price_list, product=product,
                                                    price=price,
                                                    quantity_in_box=quantity_in_box,
                                                    point=point)
                    except Product.DoesNotExist:
                        raise serializers.ValidationError({'message': f'Product with ID {product_id} does not exist.'})
                # Add permission
                restrict = perm_data.get('restrict')
                if restrict:
                    self.handle_restrict(perm_data, price_list.id, self.Meta.model)
                return price_list
        except Exception as e:
            app_log.error(f"Error when create price_list: {e}")
            raise serializers.ValidationError({'message': 'unexpected error'})

    def update(self, instance, validated_data):
        data, perm_data = self.split_data(validated_data)
        products_data = data.pop('products', [])
        try:
            with transaction.atomic():
                for attr, value in data.items():
                    setattr(instance, attr, value)
                instance.save()

                # Update products within the price list
                current_product_ids = {product.product.id for product in instance.productprice_set.all()}
                new_product_ids = {item['product_id'] for item in products_data}

                # Delete products that are not in the new data
                instance.productprice_set.filter(product_id__in=list(current_product_ids - new_product_ids)).delete()

                # Update existing products and create new ones
                for product_data in products_data:
                    product_id = product_data.pop('product_id')
                    product, _ = Product.objects.get_or_create(id=str(product_id))
                    product_price, created = ProductPrice.objects.update_or_create(
                        price_list=instance,
                        product=product,
                        defaults={
                            'price': product_data.get('price'),
                            'quantity_in_box': product_data.get('quantity_in_box'),
                            'point': product_data.get('point'),
                        }
                    )
                # Handle permissions if needed
                restrict = perm_data.get('restrict')
                if restrict:
                    self.handle_restrict(perm_data, instance.id, self.Meta.model)

                return instance
        except Exception as e:
            app_log.error(f"Error when update price_list: {e}")
            raise serializers.ValidationError({'message': 'unexpected error'})


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


class UserPointView(serializers.ModelSerializer):
    class Meta:
        model = PointOfSeason
        fields = ['point']


class UserPoint(BaseRestrictSerializer):
    class Meta:
        model = PointOfSeason
        fields = '__all__'


class SpecialOfferProductSerializer(serializers.ModelSerializer):
    max_order_box = serializers.IntegerField(default=3)

    class Meta:
        model = SpecialOfferProduct
        fields = '__all__'
        read_only_fields = ['id']


class SpecialOfferSerializer(BaseRestrictSerializer):
    # special_offers = SpecialOfferProductSerializer(many=True, required=False)

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
        return ret

    def create(self, validated_data):
        # Split insert data
        data, perm_data = self.split_data(validated_data)
        app_log.info(f"Test SpecialOfferSerializer ---------------")

        products_data = data.pop('special_offers', [])

        # Create new SpecialOffer
        special_offer = SpecialOffer.objects.create(**data)
        # Add product to SpecialOfferProduct
        for product_data in products_data:
            self.check_product_in_price_list(special_offer, product_data.get('product'))
            self.set_default_values(special_offer, product_data)
            app_log.info(f"Check product_data: {product_data}")
            SpecialOfferProduct.objects.create(special_offer=special_offer, **product_data)

        # Create perm for data
        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, special_offer.id, self.Meta.model)
        return special_offer

    def update(self, instance, validated_data):
        # Split insert data
        data, perm_data = self.split_data(validated_data)
        products_data = data.pop('special_offers', [])

        # Update SpecialOffer fields
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update SpecialOfferProduct details
        keep_products = []
        for product_data in products_data:
            if "id" in product_data:
                product = SpecialOfferProduct.objects.get(id=product_data["id"], special_offer=instance)
                for attr, value in product_data.items():
                    if attr != 'special_offer':  # Avoid setting special_offer attribute again
                        setattr(product, attr, value)
                product.save()
                keep_products.append(product.id)
            else:
                self.check_product_in_price_list(instance, product_data['product'])
                self.set_default_values(instance, product_data)
                product_data.pop('special_offer', None)  # Remove special_offer from product_data if exists
                product = SpecialOfferProduct.objects.create(special_offer=instance, **product_data)
                keep_products.append(product.id)

        # Remove products not included in the update
        for product in instance.special_offers.all():
            if product.id not in keep_products:
                product.delete()

        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, instance.id, self.Meta.model)
        return instance

    @staticmethod
    def set_default_values(special_offer, product_data):
        """Set default values for price, point, and quantity_in_box from ProductPrice"""
        app_log.info(f"set_default_values")
        if 'price' not in product_data or product_data['price'] is None:
            app_log.info(f"When not have price")

            current_pl = PriceList.get_main_pl()
            product_price = ProductPrice.objects.filter(price_list=current_pl,
                                                        product=product_data.get('product')).first()
            app_log.info(f"Test product price: {product_price}")
            if product_price:
                product_data['price'] = product_price.price
                product_data['point'] = product_price.point
                product_data['quantity_in_box'] = product_price.quantity_in_box

    @staticmethod
    def check_product_in_price_list(special_offer, product):
        """Check if the product exists in the PriceList"""
        current_pl = PriceList.get_main_pl()
        print(f"Check price list: {current_pl}")
        if not ProductPrice.objects.filter(price_list=current_pl, product=product).exists():
            raise serializers.ValidationError({'message': f'Product {product.id} is not in the PriceList'})
