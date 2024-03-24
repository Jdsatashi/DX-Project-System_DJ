from datetime import datetime

from django.contrib.auth.hashers import make_password

from account.forms import CreateUserForm, RegisterForm
from account.models import User
from user_system.kh_nhomkh.models import NhomKH
from user_system.kh_profile.models import KHProfile
from user_system.user_type.models import UserType
from utils.constants import type_kh, maNhomND


# Create new account
def handle_create_acc(req):
    ctx = {}
    u_type = UserType.objects.all()
    form = CreateUserForm(req.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
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


# Register view
def handle_register_acc(req):
    ctx = {}
    form = RegisterForm(req.POST or None)
    ctx['form'] = form
    if form.is_valid() and req.method == 'POST':
        obj = form.save(commit=False)
        # Set default value for user register (type = Nongdan)
        obj.loaiUser = type_kh
        nhomKH = maNhomND
        usercode = generate_usercode(nhomKH)
        obj.usercode = usercode.upper()
        obj.password = make_password(obj.password)
        # Create user
        obj.save()
        # Handle create user profile
        objNhomND = NhomKH.objects.get(maNhom=maNhomND)
        KHProfile.objects.create(maKH=obj, maNhomKH=objNhomND)
    return ctx


def generate_usercode(maNhom):
    # Get last 2 number of year (2024 => get '24')
    current_year = str(datetime.now().year)[-2:]
    if maNhom == maNhomND:
        code = 'ND'
    else:
        return None
    usercode_template = f'{code}{current_year}'

    existing_usercodes = User.objects.filter(usercode__startswith=usercode_template).values_list('usercode', flat=True)

    if not existing_usercodes:
        new_usercode = f'{usercode_template}0001'
    else:
        last_usercode = max(existing_usercodes)
        last_sequence_number = int(last_usercode[-4:])
        new_sequence_number = last_sequence_number + 1

        new_usercode = f'{usercode_template}{new_sequence_number:04d}'

    return new_usercode
