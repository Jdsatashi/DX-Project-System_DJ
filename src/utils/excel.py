import pandas as np

from app.settings import PROJECT_DIR

excel_file = np.read_excel(PROJECT_DIR / 'test/sptn.xlsx', usecols="A:D")

for index, row in excel_file.iterrows():
    product_id = row['maSanPham']
    product_price = row['donGia']
    quantity_in_box = row['soLuongTrenThung']
    point = row['diemTrenThung']
