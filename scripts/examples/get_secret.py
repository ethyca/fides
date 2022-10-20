from typing import Dict

from . import load_example_secrets


def get_secret(name: str) -> Dict[str, str]:
    """
    Checks to see if a secret is set at environment level
    before returning the value pre-programmed in the
    secrets file
    """

    try:
        secret = getattr(load_example_secrets, name)
    except AttributeError:
        raise SystemExit(f"Secret {name} not found!")
    else:
        return secret
