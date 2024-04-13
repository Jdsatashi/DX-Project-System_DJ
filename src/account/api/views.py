from functools import partial

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import mixins, viewsets, status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import api_view
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.api.serializers import UserSerializer, RegisterSerializer
from account.handlers.handle import handle_create_acc
from account.handlers.validate_perm import ValidatePermRest
from account.models import User, Verify
from user_system.user_type.api.views import filter_data
from utils.constants import status as user_status


def api_create_user(req):
    ctx = handle_create_acc(req)
    return HttpResponse(ctx, content_type='application/json')


# Register api view
class ApiAccount(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    authentication_classes = [JWTAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [partial(ValidatePermRest, model=User)]


def filter_user(r):
    print(f"---------- Here Testing ----------\n")
    query_params = r.query_params
    search_query = query_params.get('query', {})
    limit = query_params.get('limit', 10)
    page_number = query_params.get('page', 1)
    print([search_query, limit, page_number])
    return filter_data(search_query, limit, page_number, User)


def register_otp(request):
    method = request.method
    if method == 'POST':
        ctx = {}
        phone = request.get('phone', None)
        ctx['phone'] = phone
        return HttpResponse(ctx, content_type='application/json')
    raise MethodNotAllowed(request.method, f"{method} method is not allowed")


class RegisterSMS(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def register_verify(request, pk):
    try:
        user = User.objects.get(id=pk)
    except User.DoesNotExist:
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)
    if request.method == 'POST':
        otp_code = request.data.get('otp_code', None)
        print(f"___ || TEST VERIFY || ____")
        print(f"{otp_code}")
        verify = Verify.objects.filter(user=user).latest('created_at')

        if otp_code == verify.verify_code and not verify.is_verify:
            if verify.is_verify_valid():
                verify.is_verify = True
                verify.verify_time = timezone.now()
                verify.save()
                user.status = user_status[0]
                user.is_active = True
                user.save()
                print(f"Valid verify")
                return Response({'message': 'Successful register account'}, status=status.HTTP_200_OK)
            print("OTP code is expired")
            return Response({'message': 'Mã otp đã hết hạn'}, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)
