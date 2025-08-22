from abc import abstractmethod
from typing import Any, Dict, List, Optional

from requests import Response

from fides.api.graph.traversal import TraversalNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.strategy import Strategy


class AsyncDSRStrategy(Strategy):
    """Abstract base class for async DSR strategies"""
