from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password

from account.forms import CreateUserForm, RegisterForm
from account.models import User
from app.logs import app_log
# from user_system.client_group.models import ClientGroup
from user_system.client_profile.models import ClientProfile
from utils.constants import maNhomND
from utils.helpers import generate_id


# Create new account
def handle_create_acc(req):
    ctx = {}
    form = CreateUserForm(req.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.email = obj.email if obj.email != '' else None
        obj.phone_number = obj.phone_number if obj.phone_number != '' else None
        obj.password = make_password(obj.id.lower())
        obj.save()
        form.clean()
    ctx['form'] = form
    return ctx


def handle_list_acc(req):
    ctx = {}
    users = User.objects.all()
    ctx['users'] = users
    return ctx


# Register view
def handle_register_acc(req):
    ctx = {}
    form = RegisterForm(req.POST or None)
    ctx['form'] = form
    if form.is_valid() and req.method == 'POST':
        obj = form.save(commit=False)
        # Set default value for user register (type = Nongdan)
        type_kh = "client"
        obj.loaiUser = type_kh
        nhomKH = maNhomND
        user_id = generate_id(nhomKH)
        obj.id = user_id.upper()
        obj.password = make_password(obj.password)
        # Create user
        obj.save()
        # Handle create user profile
        # objNhomND = ClientGroup.objects.get(maNhom=maNhomND)
        # ClientProfile.objects.create(maKH=obj, maNhomKH=objNhomND)
    return ctx


def handle_login_acc(req):
    ctx = {}
    if req.method == 'POST':
        user_id = req.POST.get('user_id')
        password = req.POST.get('password')
        user = None
        try:
            user = authenticate(req, id=user_id.upper(), password=password)
            app_log.info(user)
            app_log.info("logged in")
        except Exception as e:
            app_log.info(e)
        ctx['user'] = user
    return ctx
