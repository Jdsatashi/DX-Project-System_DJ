from user_system.kh_nhomkh.models import NhomKH
from user_system.user_type.models import UserType

old_data = {
    "tb_kh": "tbl_QLTT_KhachHang",
    "tb_nhanvien": "Sys_NhanVien",
    "tb_chucdanh": "Sys_ChucDanh",
    "tb_nhomKH": "tbl_QLTT_DanhMucNhomKhachHang"
}
api_path = 'api/v1/'
type_nv, _ = UserType.objects.get_or_create(loaiUser="nhanvien")
type_kh, _ = UserType.objects.get_or_create(loaiUser="khachhang")
maNhomND = 'DMNKH000005'
tenNhomND = 'Khách hàng Nông dân'
