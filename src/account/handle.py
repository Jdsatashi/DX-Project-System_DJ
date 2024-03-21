from django.contrib.auth.hashers import make_password

from account.forms import CreateUserForm
from account.models import User
from user_system.user_type.models import UserType


def handle_create_acc(req):
    ctx = {}
    u_type = UserType.objects.all()
    form = CreateUserForm(req.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.usercode = obj.usercode.upper()
        obj.email = obj.email if obj.email != '' else None
        obj.phone_number = obj.phone_number if obj.phone_number != '' else None
        obj.password = make_password(obj.usercode.lower())
        obj.save()
        form.clean()
    ctx['form'] = form
    ctx['user_type'] = u_type
    return ctx


def handle_list_acc(req):
    ctx = {}
    users = User.objects.all()
    ctx['users'] = users
    return ctx


def register_acc(req):
    ctx = {}
