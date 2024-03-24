from django.shortcuts import render

from account.handle import handle_create_acc, handle_register_acc


# Create your views here.
def create_acc(request):
    ctx = handle_create_acc(request)
    return render(request, 'account/create.html', ctx)


def list_acc(request):
    ctx = list_acc(request)
    return render(request, 'account/index.html', ctx)


def register_acc(request):
    ctx = handle_register_acc(request)



def login_acc(request):
    pass
