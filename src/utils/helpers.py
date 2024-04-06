def value_or_none(value, condition, _return):
    return value if value != condition else _return
