import pandas as pd


def get_user_list(file):
    df = pd.read_excel(file, engine='openpyxl')

    if 'maKH' not in df.columns:
        raise ValueError("Cột 'maKH' không tồn tại trong file Excel.")

    users = df['maKH'].dropna().tolist()

    return users
