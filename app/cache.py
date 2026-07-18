status_cache: dict[str, bool] = {}

def status_cache_key(
    company: str,
    office: str,
    resource: str,
    server: str,
    event_type: str,
) -> str:
    return "|".join(
        [
            company,
            office,
            resource,
            server,
            event_type,
        ]
    )

def is_same_status(key: str, status: bool) -> bool:
    return status_cache.get(key) == status

def remember_status(key: str, status: bool) -> None:
    status_cache[key] = status