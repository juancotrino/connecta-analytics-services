def ensure_list(value: str) -> list[str] | None:
    if value:
        if not isinstance(value, list):
            return value.split(",")
        else:
            return value
    else:
        return None
