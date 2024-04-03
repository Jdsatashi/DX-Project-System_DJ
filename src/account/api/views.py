import time

from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from account.api.serializers import UserSerializer
from account.handlers.handle import handle_create_acc, handle_list_acc


def api_create_user(req):
    ctx = handle_create_acc(req)
    return HttpResponse(ctx, content_type='application/json')


def api_list_user(request):
    start = time.time()
    token = request.COOKIES.get('token')
    ctx = {}
    if not token:
        ctx['message'] = 'Unauthorized'
        return JsonResponse(ctx)
    ctx['token'] = token
    ctx = handle_list_acc(request)
    ctx = list(ctx['users'].values())
    for user in ctx:
        user.pop('last_login')
        user.pop('is_superuser')
    print(time.time() - start)
    return JsonResponse(ctx)


# Register api view
class ApiRegister(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)