from rich_click import secho


class DockerCheckException(Exception):
    """An exception for use when checking & verifying Docker versions."""

    def __init__(self, message: str):
        self.message = message
        secho(f"ERROR: {self.message}", fg="red")
        raise SystemExit(1)
