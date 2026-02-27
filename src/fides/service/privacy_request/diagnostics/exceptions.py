class DefaultStorageNotConfiguredError(Exception):
    """Raised when an operation requires a default storage backend but none is configured."""

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)
