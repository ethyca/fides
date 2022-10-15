import os


class SecretMissing(Exception):
    """An exception to denote the omission of a required secret."""


def get_secret(name: str) -> str:
    """
    Checks to see if a secret is set at environment level
    before returning the value pre-programmed in the
    secrets file
    """
    # First try to get the secret from the environment
    secret = os.getenv(name)
    if secret:
        return secret

    # Otherwise get the secret from the secrets file
    try:
        import setup.secrets as secrets
    except ModuleNotFoundError:
        raise SecretMissing(
            f"secret {name} not present in os env and secrets.py file not found"
        )

    try:
        secret = getattr(secrets, name)
    except AttributeError:
        raise SecretMissing(f"secret {name} not present in os env or secrets.py")
    else:
        return secret
