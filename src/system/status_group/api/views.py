from rest_framework import response
from rest_framework.views import APIView

from system.status_group.api.serializers import StatusSerializer
from system.status_group.models import Status


class ApiStatus(APIView):
    def get(self, request):
        status_list = Status.objects.all()
        serializer = StatusSerializer(status_list, many=True)
        return response.Response(serializer.data)
