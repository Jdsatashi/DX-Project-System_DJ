from functools import partial

from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework import viewsets, mixins
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from user_system.user_type.api.serializers import UserTypeSerializer
from user_system.user_type.models import UserType


class UserTypeApiView(APIView):
    def get(self, request):

        user_types = UserType.objects.all()

        serializer = UserTypeSerializer(user_types, many=True)
        return Response(serializer.data)


class GenericApiUserType(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = UserTypeSerializer
    queryset = UserType.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidatePermRest, model=UserType)]
