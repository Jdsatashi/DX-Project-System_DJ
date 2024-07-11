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
    "tb_UuDai": "tbl_QLTT_UuDaiKhachHang"
}
maNhomND = 'DMNKH000005'
tenNhomND = 'Khách hàng Nông dân'
# Action of Quyen
perm_actions = {
    'full': ['all', 'view', 'create', 'update', 'destroy'],
    'self': ['view', 'create', 'update'],
    'view': ['view'],
    'create': ['create'],
    'update': ['update'],
    'destroy': ['destroy']
}
status = ['active', 'deactivate', 'pending', 'draft']
user_type = {
    'client': 'client',
    'employee': 'employee'
}
actions_views = {'get': 'list', 'post': 'create'}
actions_detail = {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}
admin_role = "admin"
magic_verify_code = '240390'
phone_magic = '0943355165'
