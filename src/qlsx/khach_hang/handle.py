from .forms import CreateKhachHang
from .models import KhachHangModel


def handle_create_khach_hang(r):
    context = {}
    form = CreateKhachHang(r.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        form.clean()
        obj.save()
    context['form'] = form
    return context


def handle_list_khach_hang(r):
    context = {}
    khach_hang = KhachHangModel.objects.all()
    context['khach_hang'] = khach_hang
    return context
