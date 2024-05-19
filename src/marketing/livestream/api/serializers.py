from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import serializers

from account.handlers.restrict_serializer import BaseRestrictSerializer
from account.models import User, PhoneNumber
from marketing.livestream.models import LiveStream, LiveStreamComment, LiveStreamProductList, LiveStreamProduct, \
    LiveStreamStatistic, LiveStreamTracking, OrderLiveProduct, OrderLiveProductDetails


class LiveStreamCommentSerializer(BaseRestrictSerializer):
    class Meta:
        model = LiveStreamComment
        fields = '__all__'
        read_only_fields = ('id', 'user', 'phone', 'created_at', 'updated_at')

    def create(self, validate_data):
        data, perm_data = self.split_data(validate_data)

        request = self.context.get('request')
        user, phone = get_phone_from_token(request)

        comment = data.get('comment', None)
        live_stream = data.get('live_stream', None)
        # livestream = LiveStream.objects.get(id=live_stream)
        if not comment:
            raise ValidationError('Comment must be not empty')

        # Create comment
        comment_object = LiveStreamComment.objects.create(
            user=user,
            phone=phone,
            comment=comment,
            live_stream=live_stream
        )

        # Create permission
        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, comment_object.id, self.Meta.model)

        return comment_object


class LiveStreamDetailCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveStreamComment
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class LiveStreamSerializer(BaseRestrictSerializer):
    class Meta:
        model = LiveStream
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class LiveProduct(BaseRestrictSerializer):
    class Meta:
        model = LiveStreamProduct
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class LiveProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveStreamProduct
        fields = ['product', 'price']


class LiveProductList(BaseRestrictSerializer):
    products_list = LiveProductSerializer(many=True, write_only=True)
    livestreamproduct_set = LiveProduct(many=True, read_only=True)

    class Meta:
        model = LiveStreamProductList
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validate_data):
        data, perm_data = self.split_data(validate_data)
        products_data = data.pop('products_list')
        live_product_list = LiveStreamProductList.objects.create(**data)

        for product_data in products_data:
            LiveStreamProduct.objects.create(livestream_product_list=live_product_list, **product_data)

        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, live_product_list.id, self.Meta.model)

        return live_product_list

    def update(self, instance, validate_data):
        data, perm_data = self.split_data(validate_data)
        products_data = data.pop('products_list', None)

        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()

        if products_data is not None:
            # Clear existing products
            instance.livestreamproduct_set.all().delete()
            # Add updated products
            for product_data in products_data:
                LiveStreamProduct.objects.create(livestream_product_list=instance, **product_data)

        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, instance.id, self.Meta.model)

        return instance


class LiveStatistic(BaseRestrictSerializer):
    class Meta:
        model = LiveStreamStatistic
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class LiveTracking(BaseRestrictSerializer):
    class Meta:
        model = LiveStreamTracking
        fields = '__all__'
        read_only_fields = ['id', 'phone', 'time_watch', 'created_at', 'updated_at']

    def create(self, validate_data):
        data, perm_data = self.split_data(validate_data)

        request = self.context.get('request')
        user, phone = get_phone_from_token(request)

        time_join = data.get('time_join', None)
        live_stream = data.get('live_stream', None)
        time_leave = data.get('time_leave', None)
        note = data.get('note', None)

        # Create tracking
        tracking = LiveStreamTracking.objects.create(
            phone=phone,
            time_join=time_join,
            live_stream=live_stream,
            time_leave=time_leave,
            note=note
        )

        # Create permission
        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, tracking.id, self.Meta.model)

        return tracking

    def update(self, instance, validate_data):
        data, perm_data = self.split_data(validate_data)
        data.pop('live_stream')
        data.pop('phone')
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()

        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, instance.id, self.Meta.model)

        return instance


# OrderLiveProduct
# OrderLiveProductDetails

class LiveOrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLiveProductDetails
        fields = '__all__'
        read_only_fields = ['id', 'order_id', 'created_at', 'product_price', 'point_get']


class LiveOrderSerializer(BaseRestrictSerializer):
    product_list = LiveOrderProductSerializer(source='orderliveproductdetails_set', many=True)

    class Meta:
        model = OrderLiveProduct
        fields = '__all__'
        read_only_fields = ['id', 'phone', 'created_at', 'updated_at']

    def create(self, validated_data):
        data, perm_data = self.split_data(validated_data)
        # Get user and phone objects
        request = self.context.get('request')
        user, phone = get_phone_from_token(request)
        # Get livestream_product_list to get turn order
        livestream_product_list = data.get('livestream_product_list')
        max_orders = livestream_product_list.turn_order
        # Counting items of order
        current_order_count = OrderLiveProduct.objects.filter(
            phone__user=user,
            livestream_product_list=livestream_product_list
        ).count()
        # Validate if order > turn_order
        # if current_order_count >= max_orders:
        #     raise serializers.ValidationError(
        #         f"User has reached the maximum number of orders ({max_orders}) for this livestream.")

        products_data = data.pop('product_list')
        if products_data is None:
            raise ValidationError('Product list must be not empty')

        order = OrderLiveProduct.objects.create(phone=phone, **data)

        for product_data in products_data:
            OrderLiveProductDetails.objects.create(order_id=order, **product_data)

        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, order.id, self.Meta.model)

        return order

    def update(self, instance, validated_data):
        data, perm_data = self.split_data(validated_data)
        products_data = data.pop('product_list')

        # Update OrderLiveProduct fields
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update OrderLiveProductDetails
        keep_products = []
        for product_data in products_data:
            if "id" in product_data:
                product = OrderLiveProductDetails.objects.get(id=product_data["id"], order_id=instance)
                for attr, value in product_data.items():
                    setattr(product, attr, value)
                product.save()
                keep_products.append(product.id)
            else:
                product = OrderLiveProductDetails.objects.create(order_id=instance, **product_data)
                keep_products.append(product.id)

        # Remove products not included in the update
        for product in instance.orderliveproductdetails_set.all():
            if product.id not in keep_products:
                product.delete()

        restrict = perm_data.get('restrict')
        if restrict:
            self.handle_restrict(perm_data, instance.id, self.Meta.model)

        return instance


def get_phone_from_token(request):
    if request:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ')[1]
        else:
            raise ValidationError('Invalid token')
    else:
        raise ValidationError('Not found request')

    # Get user and phone objects from access token
    try:
        token = AccessToken(access_token)
        user = User.objects.get(id=token['user_id'])
        phone = PhoneNumber.objects.get(phone_number=token['phone_number'])
    except TokenError:
        raise ValidationError('Invalid token')
    return user, phone
