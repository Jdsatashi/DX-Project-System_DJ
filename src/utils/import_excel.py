import numpy as np
import pandas as pd
from rest_framework.exceptions import ValidationError


def get_user_list(file):
    df = pd.read_excel(file, engine='openpyxl')

    if 'maKH' not in df.columns:
        raise ValueError("Cột 'maKH' không tồn tại trong file Excel.")

    users = df['maKH'].dropna().tolist()

    return users


def file_data_to_dict(file, column_mapping: dict) -> list[dict]:
    try:
        df = pd.read_excel(file, engine='openpyxl')
    except Exception as e:
        raise ValidationError({'message': f'Error reading the Excel file: {str(e)}'})

    missing_columns = [col for col in column_mapping.keys() if col not in df.columns]
    if missing_columns:
        raise ValidationError({'message': f'Missing columns in the file: {", ".join(missing_columns)}'})

    df.rename(columns=column_mapping, inplace=True)
    df['line_number'] = df.index + 2
    df.replace({np.inf: None, -np.inf: None, np.nan: None}, inplace=True)
    data = df.to_dict(orient='records')
    return data
