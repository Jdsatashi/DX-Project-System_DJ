from account.handlers.restrict_serializer import BaseRestrictSerializer
from marketing.price_list.models import PriceList, ProductPrice
from rest_framework import serializers

from marketing.product.models import Product


class ProductPriceSerializer(serializers.ModelSerializer):
    product_id = serializers.CharField(write_only=True)

    class Meta:
        model = ProductPrice
        fields = '__all__'
        read_only_fields = ('id', 'price_list', 'product')

    def to_internal_value(self, data):
        # Ensure that `product_id` remains a string
        product_id = data.get('product_id')
        if not isinstance(product_id, str):
            raise serializers.ValidationError({
                'product_id': 'Product ID must be a string.'
            })

        return super().to_internal_value(data)


class ProductPriceReadSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_id = serializers.CharField(source='product.id', read_only=True)

    class Meta:
        model = ProductPrice
        fields = ['product_id', 'product_name', 'price', 'amount', 'point']


class PriceListSerializer(BaseRestrictSerializer):
    products = ProductPriceSerializer(many=True, write_only=True)
    products_list = ProductPriceReadSerializer(source='productprice_set', many=True,
                                               read_only=True)

    class Meta:
        model = PriceList
        fields = '__all__'
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        # Split data for permission
        data, perm_data = self.split_data(validated_data)
        # Split data products from serializer
        products_data = data.pop('products', [])
        # Create price list
        price_list = PriceList.objects.create(**data)
        # Add product to price list
        for product_data in products_data:
            product_id = product_data.pop('product_id')
            price = product_data.pop('price')
            amount = product_data.pop('amount')
            point = product_data.pop('point')
            try:
                product = Product.objects.get(id=str(product_id))
                ProductPrice.objects.create(price_list=price_list, product=product,
                                            price=price,
                                            amount=amount,
                                            point=point)
            except Product.DoesNotExist:
                raise serializers.ValidationError({'product_id': f'Product with ID {product_id} does not exist.'})
        # Add permission
        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, price_list.id, self.Meta.model)
        return price_list

    def update(self, instance, validated_data):
        data, perm_data = self.split_data(validated_data)
        products_data = data.pop('products', [])

        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update products within the price list
        current_product_ids = {product.product.id for product in instance.productprice_set.all()}
        new_product_ids = {item['product_id'] for item in products_data}
        current_product_price = instance.products.all()
        print(f"Before update ProductPrice: ")
        for prod in list(current_product_price):
            print(prod)
        # Delete products that are not in the new data
        instance.productprice_set.filter(product_id__in=list(current_product_ids - new_product_ids)).delete()
        print(instance)
        current_product_price = instance.products.all()
        print(f"After remove ProductPrice: ")
        for prod in list(current_product_price):
            print(prod)

        # Update existing products and create new ones
        for product_data in products_data:
            product_id = product_data.pop('product_id')
            product, _ = Product.objects.get_or_create(id=str(product_id))
            product_price, created = ProductPrice.objects.update_or_create(
                price_list=instance,
                product=product,
                defaults={
                    'price': product_data.get('price'),
                    'amount': product_data.get('amount'),
                    'point': product_data.get('point'),
                }
            )
        print(f"After Update ProductPrice: ")
        for prod in list(current_product_price):
            print(prod)
        # Handle permissions if needed
        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, instance.id, self.Meta.model)

        return instance
