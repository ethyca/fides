import boto3
import requests
from boto3 import Session
from requests import Response

from fidesops.schemas.third_party.onetrust import OneTrustOAuthResponse


def get_s3_session(aws_access_key_id: str, aws_secret_access_key: str) -> Session:
    """Abstraction to retrieve s3 session using secrets"""
    session = boto3.session.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )

    # Check that credentials are valid
    client = session.client("sts")
    client.get_caller_identity()

    # Returns session
    return session


def get_onetrust_access_token(client_id: str, client_secret: str, hostname: str) -> str:
    """Retrieves onetrust access token using secrets"""
    form_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    response: Response = requests.post(
        f"https://{hostname}.com/api/access/v1/oauth/token",
        files=form_data,
    )
    res_body: OneTrustOAuthResponse = response.json()
    return res_body.access_token
