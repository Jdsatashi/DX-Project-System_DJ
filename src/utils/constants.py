from types import SimpleNamespace

from utils.env import MAGIC_PHONE, MAGIC_OTP

old_data = {
    "tb_kh": "tbl_QLTT_KhachHang",
    "tb_nhanvien": "Sys_NhanVien",
    "tb_nhomKH": "tbl_QLTT_DanhMucNhomKhachHang",
    "tb_congty": "tbl_QLTT_DanhMucCongTy",
    "tb_loaiThuoc": "tbl_QLTT_DanhMucLoaiThuoc",
    "tb_thuoc": "tbl_QLTT_DanhMucThuoc",
    "tb_thuocChitiet": "tbl_QLTT_DanhMucThuoc_ChiTiet",
    "tb_sanpham": "tbl_QLTT_DanhMucSanPham",
    "tb_bangGia": "tbl_QLTT_SanPhamTheoNam",
    "tb_bangGiaSanPham": "tbl_QLTT_SanPhamTheoNam_SanPham",
    "tb_toa": "tbl_QLTT_DanhSachToa",
    "tb_toaDetail": "tbl_QLTT_DanhSachToa_ChiTiet",
    "tb_chucDanh": "Sys_ChucDanh",
    "tb_chucDanhUser": "Sys_ChucDanhNhanVien",
    "tb_phongBan": "Sys_PhongBan",
    "tb_phongBanUser": "Sys_PhongBanNhanVien",
    "tb_UuDai": "tbl_QLTT_UuDaiKhachHang",
    "tb_CTKM": "tbl_QLTT_ChuongTrinhKhuyenMai",
    "tb_CTKM_SanPham": "tbl_QLTT_ChuongTrinhKhuyenMai_SanPham"
}
maNhomND = 'DMNKH000005'
tenNhomND = 'Khách hàng Nông dân'
# Action of Quyen
perm_actions = {
    'fall': ['all', 'view', 'create', 'update', 'destroy'],
    'full': ['view', 'create', 'update', 'destroy'],
    'self': ['view', 'create', 'update'],
    'all': 'all',
    'view': 'view',
    'create': 'create',
    'update': 'update',
    'destroy': 'destroy'
}
user_type = {
    'client': 'client',
    'employee': 'employee'
}
actions_views = {'get': 'list', 'post': 'create'}
actions_detail = {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}
admin_role = "admin"
phone_magic = MAGIC_PHONE  # '0943355165'
magic_verify_code = MAGIC_OTP  # '240390'
max_phone = 3

status = ['active', 'deactivate', 'pending', 'draft']
data_status = SimpleNamespace(active='active', deactivate='deactivate', pending='pending', draft='draft')
so_type = SimpleNamespace(manual='manual', consider_user='consider_offer_user', template='template', special_offer='special_offer')
so_type_list = list(so_type.__dict__.values())

# Email type
mail_type = SimpleNamespace(report_order='report_order', report_nvtt='report_nvtt')
