from functools import partial

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from account.models import User, UserPerm, Perm
from marketing.price_list.api.serializers import PriceListSerializer, SpecialOfferSerializer
from marketing.price_list.models import PriceList, SpecialOffer
from utils.constants import acquy
from utils.model_filter_paginate import filter_data


class GenericApiPriceList(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                          mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = PriceListSerializer
    # queryset = PriceList.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication]

    # permission_classes = [partial(ValidatePermRest, model=PriceList)]

    def get_queryset(self):
        user = self.request.user
        model_class = self.serializer_class.Meta.model
        if user.is_superuser:
            return model_class.objects.all()
        if not user.is_authenticated:
            return Response({'message': 'User is not authenticate'}, status=status.HTTP_401_UNAUTHORIZED)
        all_permissions = user.get_all_allow_perms()
        price_list_ids = []

        content = ContentType.objects.get_for_model(model_class)
        action_perm = acquy.get('list')
        perm_name = f'{content.app_label}_{content.model}'

        # Get all price list ids which required permissions
        perms_content = Perm.objects.filter(name__icontains=perm_name)
        prl_perm_ids = {v.object_id for v in perms_content if v.object_id}

        # Get all price list ids which user has permissions
        for perm in all_permissions:
            if perm.startswith(action_perm + '_' + perm_name):
                _, object_id = perm.rsplit('_', 1)
                price_list_ids.append(object_id)
        price_list_ids = list(prl_perm_ids - set(price_list_ids))
        return model_class.objects.exclude(id__in=price_list_ids)

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'name', 'date_start', 'date_end'], *args,
                               **kwargs)
        return Response(response, status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='now', url_name='now')
    def now(self, request, *args, **kwargs):
        today = timezone.localdate()
        queryset = self.get_queryset().filter(date_start__lte=today, date_end__gte=today)
        response = filter_data(self, request, ['id', 'name', 'date_start', 'date_end'], queryset=queryset,
                               **kwargs)
        return Response(response)


class ApiSpecialOffer(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = SpecialOfferSerializer
    queryset = SpecialOffer.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=PriceList)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'name', 'status', 'type_list'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class ApiSpecialOfferConsider(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = SpecialOfferSerializer
    queryset = SpecialOffer.objects.filter(type_list='consider_offer_user')
    authentication_classes = [JWTAuthentication, BasicAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=PriceList)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'name', 'status'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)
