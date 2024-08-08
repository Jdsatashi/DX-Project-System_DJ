from functools import partial

from rest_framework import viewsets, mixins
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from system_func.api.serializers import PeriodSeasonSerializer
from system_func.models import PeriodSeason


class ApiPeriodSeason(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = PeriodSeasonSerializer
    queryset = PeriodSeason.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidatePermRest, model=PeriodSeason)]
