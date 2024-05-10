from django import forms
from django.core.exceptions import ValidationError

from account.models import User


def validate_unique_userid(value):
    if User.objects.filter(id=value).exists():
        raise ValidationError("This user id is already in use.")


class CreateUserForm(forms.ModelForm):
    user_id = forms.CharField(required=True, label='User Code', validators=[validate_unique_userid])
    username = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    khuVuc = forms.CharField(required=False)
    status = forms.ChoiceField(choices=(
        ('active', 'Hoạt động'),
        ('pending', 'Chờ duyệt'),
        ('processing', 'Đang diễn ra'),
        ('inactive', 'Không hoạt động'),
        ('decline', 'Huỷ bỏ')
    ))

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'khuVuc', 'status']

    def clean_id(self):
        user_id = self.cleaned_data.get('id')
        if User.objects.filter(id=user_id).exists():
            raise ValidationError("This user code is already in use.")
        return user_id


class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password']
