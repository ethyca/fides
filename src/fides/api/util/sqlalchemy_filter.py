import logging


class SQLAlchemyGeneratedFilter(logging.Filter):
    """
    Logging filter that removes SQLAlchemy engine logs containing timing information.

    This filter specifically targets logs containing error messages from sqlalchemy.engine.Engine
    which typically come from sqlalchemy.engine.Engine when executing cached queries.
    """

    def __init__(self) -> None:
        super().__init__()
        # List of substrings to filter out
        self.patterns = [
            "cached since",
            "caching disabled",
            "does not support caching",
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        # Only filter records from sqlalchemy.engine.Engine
        if record.name == "sqlalchemy.engine.Engine":
            message = record.getMessage()
            # Check if any of the patterns exist in the message
            for pattern in self.patterns:
                if pattern in message:
                    return False  # Filter out the log entry

        return True  # Keep all other log entries
