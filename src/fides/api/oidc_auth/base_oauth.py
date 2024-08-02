from typing import Optional, List, Dict, TypeVar, Any, cast
from urllib.parse import urlencode
import time
import requests

T = TypeVar("T")


class BaseOAuth:
    provider: str
    client_id: str
    client_secret: str  ### SecretType
    redirect_uri: str
    authorize_url: str
    access_token_url: str
    refresh_token_url: Optional[str]
    revoke_token_url: Optional[str]
    base_scope: Optional[List[str]]
    request_header: Dict[str, str]

    def __init__(
        self,
        provider: str,
        client_id: str,
        client_secret: str,  ### SecretType
        redirect_uri: str,
        authorize_url: str,
        access_token_url: str,
        refresh_token_url: Optional[str] = None,
        revoke_token_url: Optional[str] = None,
        base_scope: Optional[List[str]] = None,
    ):

        self.provider = provider
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.authorize_url = authorize_url
        self.access_token_url = access_token_url
        self.refresh_token_url = refresh_token_url
        self.revoke_token_url = revoke_token_url
        self.base_scope = base_scope

        self.request_header = {"Accept": "application/json"}

    async def get_authorization_url(
        self,
        state: Optional[str] = None,
        scope: Optional[List[str]] = None,
        extras_params: Optional[T] = None,
    ) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
        }

        if state is not None:
            params["state"] = state

        _scope = scope or self.base_scope
        if _scope is not None:
            params["scope"] = " ".join(_scope)

        if extras_params is not None:
            params = {**params, **extras_params}  # type: ignore
        temp = f"{self.authorize_url}?{urlencode(params)}"
        print("temp = ", temp)
        return f"{self.authorize_url}?{urlencode(params)}"

    async def get_access_token(self, code: str, state: Optional[str] = None):
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": (self.client_secret),  ###
            "code": code,
            "redirect_uri": self.redirect_uri,
            "state": state,
        }

        response = requests.post(
            self.access_token_url, data=data, headers=self.request_header
        )
        print("response = ", response.text)
        if response.status_code >= 400:
            raise Exception(response.text)

        data = cast(Dict[str, Any], response.json())

        return OAuth2Token(data)

    def get_userinfo(self, access_token: str):
        raise NotImplementedError

    def get_open_id(self, user_json: dict):
        raise NotImplementedError


class OAuth2Token(Dict[str, Any]):
    def __init__(self, token_dict: Dict[str, Any]):
        if "expires_at" in token_dict:
            token_dict["expires_at"] = int(token_dict["expires_at"])
        elif "expires_in" in token_dict:
            token_dict["expires_at"] = int(time.time()) + int(token_dict["expires_in"])
        super().__init__(token_dict)

    def is_expired(self):
        if "expires_at" not in self:
            return False
        return time.time() > self["expires_at"]
