from rich_click import secho


class LocalModeException(Exception):
    """Raise an error when `local_mode` is enabled with an incompatible command."""

    def __init__(self, command: str):
        self.command = command
        self.message = f"> Command: `{self.command}` not compatible with `local_mode`!"
        secho(self.message, fg="red")
        raise SystemExit(1)
