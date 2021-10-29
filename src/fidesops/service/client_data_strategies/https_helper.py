from typing import Dict

from fidesops.common_exceptions import FidesopsException


def create_authorization_headers(authorization: str) -> Dict[str, str]:
    """Creates headers containing authorization"""
    return {"Authorization": authorization}


def create_identity_parameters(identity: str) -> Dict[str, str]:
    """Creates request parameters containing identity"""
    return {"identity": identity}
