from django.http import HttpResponse
from django.shortcuts import render

from qlsx.khach_hang.handle import *


# Create your views here.
def create_khach_hang(request):
    context = handle_create_khach_hang(request)
    return render(request, 'qlsx/khach_hang/index.html', context)


def list_khach_hang(request):
    context = handle_list_khach_hang(request)
    clients = list(context['khach_hang'].values())
    return HttpResponse(clients, content_type='application/json')
