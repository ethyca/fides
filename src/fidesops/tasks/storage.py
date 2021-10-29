import logging
from typing import Any, Dict

import json
import zipfile
from io import BytesIO
import requests

import pandas as pd

from botocore.exceptions import ClientError, ParamValidationError

from fidesops.models.storage import ResponseFormat
from fidesops.schemas.storage.storage import StorageSecrets

from fidesops.util.storage_authenticator import (
    get_s3_session,
    get_onetrust_access_token,
)

logger = logging.getLogger(__name__)


def write_to_in_memory_buffer(resp_format: str, data: Dict[str, Any]) -> BytesIO:
    """Write JSON/CSV data to in-memory file-like object to be passed to S3
    :param resp_format: str, should be one of ResponseFormat
    :param data: Dict
    """
    logger.info("Writing data to in-memory buffer")

    if resp_format == ResponseFormat.json.value:
        return BytesIO(json.dumps(data, indent=2).encode("utf-8"))

    if resp_format == ResponseFormat.csv.value:
        zipped_csvs = BytesIO()
        with zipfile.ZipFile(zipped_csvs, "w") as f:
            for key in data:
                df = pd.json_normalize(data[key])
                buffer = BytesIO()
                df.to_csv(buffer, index=False, encoding="utf-8")
                buffer.seek(0)
                f.writestr(f"{key}.csv", buffer.getvalue())

        zipped_csvs.seek(0)
        return zipped_csvs

    raise NotImplementedError(f"No handling for response format {resp_format}.")


def upload_to_s3(
    storage_secrets: Dict[StorageSecrets, Any],
    data: Dict,
    bucket_name: str,
    file_key: str,
    resp_format: str,
) -> str:
    """Uploads arbitrary data to s3 returned from a SAR request"""
    logger.info(f"Starting S3 Upload of {file_key}")
    try:
        my_session = get_s3_session(
            aws_access_key_id=storage_secrets[StorageSecrets.AWS_ACCESS_KEY_ID.value],
            aws_secret_access_key=storage_secrets[
                StorageSecrets.AWS_SECRET_ACCESS_KEY.value
            ],
        )

        s3 = my_session.client("s3")

        # handles file chunking
        s3.upload_fileobj(
            Fileobj=write_to_in_memory_buffer(resp_format, data),
            Bucket=bucket_name,
            Key=file_key,
        )
        # todo- move to outbound_urn_registry
        return "https://%s.s3.amazonaws.com/%s" % (bucket_name, file_key)
    except ClientError as e:
        raise e
    except ParamValidationError as e:
        raise ValueError(f"The parameters you provided are incorrect: {e}")


def upload_to_onetrust(
    payload: Dict,
    storage_secrets: Dict[StorageSecrets, Any],
    ref_id: str,
) -> str:
    """Uploads arbitrary data to onetrust returned from a SAR request"""
    logger.info(f"Starting OneTrust Upload for ref_id {ref_id}")

    onetrust_hostname = storage_secrets[StorageSecrets.ONETRUST_HOSTNAME.value]
    access_token = get_onetrust_access_token(
        client_id=storage_secrets[StorageSecrets.ONETRUST_CLIENT_ID.value],
        client_secret=storage_secrets[StorageSecrets.ONETRUST_CLIENT_SECRET.value],
        hostname=onetrust_hostname,
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    requests.post(
        # todo- move to outbound_urn_registry
        f"https://{onetrust_hostname}.com/api/datasubject/v3/datadiscovery/requestqueues/{ref_id}",
        data=payload,
        headers=headers,
    )
    return "success"
