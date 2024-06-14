from functools import partial

from rest_framework import mixins, viewsets, status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.handlers.validate_perm import ValidatePermRest
from user_system.employee_profile.api.serializers import EmployeeProfileSerializer, DepartmentSerializer, \
    PositionSerializer
from user_system.employee_profile.models import EmployeeProfile, Department, Position
from utils.model_filter_paginate import filter_data


class GenericApiEmployee(viewsets.GenericViewSet, mixins.ListModelMixin,
                         mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = EmployeeProfileSerializer
    queryset = EmployeeProfile.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidatePermRest, model=EmployeeProfile)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request,
                               ['employee_id__id', 'department__id', 'position__id', 'fullname', 'address'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class GenericApiDepartment(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = DepartmentSerializer
    queryset = Department.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidatePermRest, model=Department)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'name', 'note'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)


class GenericApiPosition(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = PositionSerializer
    queryset = Position.objects.all()
    #authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    #permission_classes = [partial(ValidatePermRest, model=Position)]

    def list(self, request, *args, **kwargs):
        response = filter_data(self, request, ['id', 'name', 'note'],
                               **kwargs)
        return Response(response, status.HTTP_200_OK)
