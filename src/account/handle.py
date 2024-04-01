from datetime import datetime

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password

from account.forms import CreateUserForm, RegisterForm
from account.models import User
from user_system.kh_nhomkh.models import NhomKH
from user_system.kh_profile.models import KHProfile
from user_system.user_type.models import UserType
from utils.constants import maNhomND


# Create new account
def handle_create_acc(req):
    ctx = {}
    u_type = UserType.objects.all()
    form = CreateUserForm(req.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.email = obj.email if obj.email != '' else None
        obj.phone_number = obj.phone_number if obj.phone_number != '' else None
        obj.password = make_password(obj.id.lower())
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


# Register view
def handle_register_acc(req):
    ctx = {}
    form = RegisterForm(req.POST or None)
    ctx['form'] = form
    if form.is_valid() and req.method == 'POST':
        obj = form.save(commit=False)
        # Set default value for user register (type = Nongdan)
        type_kh, _ = UserType.objects.get_or_create(loaiUser="khachhang")
        obj.loaiUser = type_kh
        nhomKH = maNhomND
        user_id = generate_id(nhomKH)
        obj.id = user_id.upper()
        obj.password = make_password(obj.password)
        # Create user
        obj.save()
        # Handle create user profile
        objNhomND = NhomKH.objects.get(maNhom=maNhomND)
        KHProfile.objects.create(maKH=obj, maNhomKH=objNhomND)
    return ctx


def handle_login_acc(req):
    ctx = {}
    if req.method == 'POST':
        user_id = req.POST.get('user_id')
        password = req.POST.get('password')
        user = None
        try:
            user = authenticate(req, id=user_id.upper(), password=password)
            print(user)
            print("logged in")
        except Exception as e:
            print(e)
        ctx['user'] = user
    return ctx


def generate_id(maNhom):
    # Get last 2 number of year (2024 => get '24')
    current_year = str(datetime.now().year)[-2:]
    if maNhom == maNhomND:
        code = 'ND'
    else:
        return None
    id_template = f'{code}{current_year}'

    existing_ids = User.objects.filter(id__startswith=id_template).values_list('id', flat=True)

    if not existing_ids:
        new_id = f'{id_template}0001'
    else:
        last_id = max(existing_ids)
        last_sequence_number = int(last_id[-4:])
        new_sequence_number = last_sequence_number + 1

        new_id = f'{id_template}{new_sequence_number:04d}'

    return new_id
