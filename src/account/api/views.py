from functools import partial

from django.http import HttpResponse
from rest_framework import mixins, viewsets
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.api.serializers import UserSerializer
from account.handlers.handle import handle_create_acc
from account.handlers.validate_quyen import ValidateQuyenRest
from account.models import User
from user_system.user_type.api.views import filter_data


def api_create_user(req):
    ctx = handle_create_acc(req)
    return HttpResponse(ctx, content_type='application/json')


# Register api view
class ApiAccount(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidateQuyenRest, model=User)]


def filter_user(r):
    print(f"---------- Here Testing ----------\n")
    query_params = r.query_params
    search_query = query_params.get('query', {})
    limit = query_params.get('limit', 10)
    page_number = query_params.get('page', 1)
    print([search_query, limit, page_number, search_query])
    return filter_data(search_query, limit, page_number, User)
