import time

from django.http import HttpResponse
from django.shortcuts import render

from old_data.main import append_kh, append_nv, create_maNhomKH, create_chucdanh


# Create your views here.
def insertDB(r):
    start_time = time.time()
    create_chucdanh()
    create_maNhomKH()
    append_nv()
    append_kh()
    print(f"Complete time: {time.time() - start_time} seconds")
    return HttpResponse({}, content_type='application/json')
