old_data = {
    "tb_kh": "tbl_QLTT_KhachHang",
    "tb_nhanvien": "Sys_NhanVien",
    "tb_chucdanh": "Sys_ChucDanh",
    "tb_nhomKH": "tbl_QLTT_DanhMucNhomKhachHang",
    "tb_congty": "tbl_QLTT_DanhMucCongTy",
    "tb_loaiThuoc": "tbl_QLTT_DanhMucLoaiThuoc",
    "tb_thuoc": "tbl_QLTT_DanhMucThuoc",
    "tb_thuocChitiet": "tbl_QLTT_DanhMucThuoc_ChiTiet",
    "tb_sanpham": "tbl_QLTT_DanhMucSanPham",
}
api_path = 'api/v1/'
maNhomND = 'DMNKH000005'
tenNhomND = 'Khách hàng Nông dân'
# Action of Quyen
acquy = {
    'full': ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy'],
    'self': ['list', 'create', 'retrieve', 'update', 'partial_update'],
    'view': ['list', 'retrieve'],
    'create': 'create',
    'retrieve': 'retrieve',
    'list': 'list',
    'update': 'update',
    'partial_update': 'partial_update',
    'destroy': 'destroy'
}
