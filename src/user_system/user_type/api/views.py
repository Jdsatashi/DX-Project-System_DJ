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

        user_types = filter_user_type(request)

        serializer = UserTypeSerializer(user_types, many=True)
        return Response(serializer.data)


class GenericApiUserType(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = UserTypeSerializer
    queryset = UserType.objects.all()
    # authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    # permission_classes = [partial(ValidatePermRest, model=UserType)]


def filter_user_type(r):
    print(f"---------- Here Testing ----------\n")
    query_params = r.query_params
    search_query = query_params.get('query', {})
    limit = query_params.get('limit', 10)
    page_number = query_params.get('page', 1)
    print([search_query, limit, page_number, search_query])
    return filter_data(search_query, limit, page_number, UserType)


def filter_data(query: dict, limit: int, page_number: int, _model):
    print(f"---------- Here Testing ----------\n")
    content_type = ContentType.objects.get_for_model(_model)
    print(content_type)
    model_class = content_type.model_class()
    query_set = model_class.objects.all()
    print(query.items())
    if query.items():
        search_conditions = []

        for key, value in query.items():
            search_condition = Q(**{f"{key}__icontains": value})
            search_conditions.append(search_condition)
        final_search_query = search_conditions.pop()
        for condition in search_conditions:
            final_search_query |= condition
        query_set = query_set.filter(final_search_query)

    paginate = Paginator(query_set, limit)
    page_obj = paginate.get_page(page_number)
    return page_obj.object_list
