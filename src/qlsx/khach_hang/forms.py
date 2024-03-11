from django import forms

from qlsx.khach_hang.models import KhachHangModel


class CreateKhachHang(forms.ModelForm):
    class Meta:
        model = KhachHangModel
        fields = '__all__'
