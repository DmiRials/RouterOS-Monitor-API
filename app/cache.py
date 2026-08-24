class StatusCache:
    def __init__(self, max_size: int = 10_000) -> None:
        self._values: dict[str, bool] = {}
        self.max_size = max_size

    def is_same(self, key: str, status: bool) -> bool:
        return self._values.get(key) == status

    def remember(self, key: str, status: bool) -> None:
        if len(self._values) >= self.max_size and key not in self._values:
            self._values.pop(next(iter(self._values)))
        self._values[key] = status

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
