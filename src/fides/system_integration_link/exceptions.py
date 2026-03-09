class SystemIntegrationLinkNotFoundError(Exception):
    def __init__(self, connection_key: str, system_fides_key: str) -> None:
        self.connection_key = connection_key
        self.system_fides_key = system_fides_key
        super().__init__(
            f"No link found between connection '{connection_key}' "
            f"and system '{system_fides_key}'"
        )


class ConnectionConfigNotFoundError(Exception):
    def __init__(self, connection_key: str) -> None:
        self.connection_key = connection_key
        super().__init__(f"Connection config '{connection_key}' not found")


class SystemNotFoundError(Exception):
    def __init__(self, system_fides_key: str) -> None:
        self.system_fides_key = system_fides_key
        super().__init__(f"System '{system_fides_key}' not found")


class TooManyLinksError(Exception):
    def __init__(self, connection_key: str, max_links: int = 1) -> None:
        self.connection_key = connection_key
        self.max_links = max_links
        super().__init__(
            f"Only {max_links} system link(s) per integration supported. "
            f"Connection '{connection_key}' would exceed this limit."
        )
