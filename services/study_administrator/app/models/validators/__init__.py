def ensure_list(value: str) -> list[str]:
    if value and not isinstance(value, list):
        return value.split(",")
    else:
        return value
