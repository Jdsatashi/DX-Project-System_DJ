import time

from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from account.api.serializers import UserSerializer
from account.handlers.handle import handle_create_acc, handle_list_acc


def api_create_user(req):
    ctx = handle_create_acc(req)
    return HttpResponse(ctx, content_type='application/json')


# Register api view
class ApiRegister(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
