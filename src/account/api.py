from django.http import HttpResponse

from account.main import append_kh, append_nv, create_chucdanh, create_maNhomKH
from account.models import User


def insertDB(reqest):
    context = {}
    create_chucdanh()
    create_maNhomKH()
    append_nv()
    append_kh()
    return HttpResponse(context, content_type='application/json')
