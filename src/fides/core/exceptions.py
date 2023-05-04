from rich_click import secho


class DockerCheckException(Exception):
    """Raise an error when `local_mode` is enabled with an incompatible command."""

    def __init__(self, message: str):
        self.message = message
        secho(f"ERROR: {self.message}", fg="red")
        raise SystemExit(1)
