from django import forms
from django.core.exceptions import ValidationError

from account.models import User
from user_system.user_type.models import UserType


def validate_unique_userid(value):
    if User.objects.filter(id=value).exists():
        raise ValidationError("This user id is already in use.")


class CreateUserForm(forms.ModelForm):
    user_id = forms.CharField(required=True, label='User Code', validators=[validate_unique_userid])
    username = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(required=False)
    khuVuc = forms.CharField(required=False)
    status = forms.ChoiceField(choices=(
        ('active', 'Hoạt động'),
        ('pending', 'Chờ duyệt'),
        ('processing', 'Đang diễn ra'),
        ('inactive', 'Không hoạt động'),
        ('decline', 'Huỷ bỏ')
    ))
    loaiUser = forms.ModelChoiceField(queryset=UserType.objects.all(), empty_label=None)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'khuVuc', 'status', 'loaiUser']

    def clean_id(self):
        user_id = self.cleaned_data.get('id')
        if User.objects.filter(id=user_id).exists():
            raise ValidationError("This user code is already in use.")
        return user_id


class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['phone_number', 'password']
