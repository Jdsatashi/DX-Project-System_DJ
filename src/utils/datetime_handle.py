from datetime import datetime

import pandas as pd


def convert_date_format(date_input):
    if isinstance(date_input, pd.Timestamp):
        return date_input.date()
    elif isinstance(date_input, datetime):
        return date_input.date()
    elif isinstance(date_input, str):
        try:
            return datetime.strptime(date_input, '%d/%m/%Y').date()
        except ValueError:
            try:
                return datetime.strptime(date_input, '%Y-%m-%d').date()
            except ValueError:
                pass
    return None
