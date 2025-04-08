import json
import os
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Generator
from unittest import mock
from unittest.mock import Mock
from zipfile import ZipFile

import pandas as pd
import pytest
from bson import ObjectId
from sqlalchemy.orm import Session

from fides.api.common_exceptions import StorageUploadError
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import (
    AWSAuthMethod,
    FileNaming,
    ResponseFormat,
    StorageDetails,
    StorageSecrets,
    StorageType,
)
from fides.api.service.storage.storage_uploader_service import get_extension, upload
from fides.api.tasks.storage import (
    LOCAL_FIDES_UPLOAD_DIRECTORY,
    encrypt_access_request_results,
    write_to_in_memory_buffer,
)
from fides.api.util.encryption.aes_gcm_encryption_scheme import (
    decrypt_combined_nonce_and_message,
)
from fides.config import CONFIG


@mock.patch("fides.api.service.storage.storage_uploader_service.upload_to_s3")
def test_uploader_s3_success_secrets_auth(
    mock_upload_to_s3: Mock, db: Session, privacy_request: PrivacyRequest
) -> None:
    request_id = privacy_request.id

    mock_config = {
        "name": "test dest",
        "key": "test_dest_key",
        "type": StorageType.s3.value,
        "details": {
            "auth_method": AWSAuthMethod.SECRET_KEYS.value,
            "bucket": "some-bucket",
            "naming": FileNaming.request_id.value,
            "max_retries": 10,
        },
        "secrets": {
            StorageSecrets.AWS_ACCESS_KEY_ID.value: "1345234524",
            StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "23451345834789",
        },
    }
    storage_config = StorageConfig.create(db, data=mock_config)

    mock_upload_to_s3.return_value = (
        f"https://some-bucket.s3.amazonaws.com/{request_id}.json"
    )
    upload_data = {"phone": "1231231234"}

    upload(
        db=db,
        privacy_request=privacy_request,
        data=upload_data,
        storage_key=mock_config["key"],
    )

    mock_upload_to_s3.assert_called_with(
        mock_config["secrets"],
        upload_data,
        mock_config["details"][StorageDetails.BUCKET.value],
        f"{request_id}.json",
        "json",
        privacy_request,
        None,
        AWSAuthMethod.SECRET_KEYS.value,
    )

    storage_config.delete(db)


def test_write_to_in_memory_buffer_handles_bson(privacy_request: PrivacyRequest):
    OBJECT_ID_STR = "5b4a61b1326bd9777aa61c19"
    data = {
        "collection:users": [
            {
                "paymentCustomerIds": {"stripe": "cus_abc"},
                "birthday": datetime(1997, 1, 8, 0, 0),
                "geolocation": {
                    "type": "Point",
                    "coordinates": [-122.272782, 37.871666],
                },
                "firstName": "Test",
                "number": "+12345678910",
                "name": "Test User",
                "email": "user@example.com",
            }
        ],
        "mongo_collection:purchases": [
            {
                "user": {"_id": ObjectId(OBJECT_ID_STR)},
                "geolocation": {
                    "type": "Point",
                    "coordinates": [-122.41210448012356, 37.773223876953125],
                },
                "customerName": None,
            },
            {
                "user": {"_id": ObjectId(OBJECT_ID_STR)},
                "geolocation": {
                    "type": "Point",
                    "coordinates": [-122.4157451701343, 37.773162841796875],
                },
                "customerName": None,
            },
        ],
        "firebase_auth:user": [
            {
                "provider_data": [
                    {"email": "user@example.com", "display_name": "Test User"}
                ],
                "display_name": "Test User",
                "phone_number": "+12345678910",
                "email": "user@example.com",
            }
        ],
    }
    # This will throw a `ValueError: Circular reference detected` if no ObjectId
    # handler is available to the JSON encoder.
    bytesio = write_to_in_memory_buffer(
        resp_format="json",
        data=data,
        privacy_request=privacy_request,
    )
    assert bytesio is not None
    data = json.loads(bytesio.read())
    assert data["collection:users"][0]["birthday"] == "1997-01-08T00:00:00"
    assert data["mongo_collection:purchases"][0]["user"]["_id"] == {
        "$oid": OBJECT_ID_STR
    }


@mock.patch("fides.api.service.storage.storage_uploader_service.upload_to_s3")
def test_uploader_s3_success_automatic_auth(
    mock_upload_to_s3: Mock, db: Session, privacy_request: PrivacyRequest
) -> None:
    request_id = privacy_request.id

    mock_config = {
        "name": "test dest",
        "key": "test_dest_key",
        "type": StorageType.s3.value,
        "details": {
            "auth_method": AWSAuthMethod.AUTOMATIC.value,
            "bucket": "some-bucket",
            "naming": FileNaming.request_id.value,
            "max_retries": 10,
        },
    }
    storage_config = StorageConfig.create(db, data=mock_config)

    mock_upload_to_s3.return_value = (
        f"https://some-bucket.s3.amazonaws.com/{request_id}.json"
    )
    upload_data = {"phone": "2018675309"}

    upload(
        db=db,
        privacy_request=privacy_request,
        data=upload_data,
        storage_key=mock_config["key"],
    )

    mock_upload_to_s3.assert_called_with(
        None,
        upload_data,
        mock_config["details"][StorageDetails.BUCKET.value],
        f"{request_id}.json",
        "json",
        privacy_request,
        None,
        AWSAuthMethod.AUTOMATIC.value,
    )

    storage_config.delete(db)


@mock.patch("fides.api.service.storage.storage_uploader_service.upload_to_s3")
def test_uploader_s3_invalid_file_naming(
    mock_upload_to_s3: Mock, db: Session, privacy_request: PrivacyRequest
) -> None:
    request_id = "214513r"

    mock_config = {
        "name": "test dest",
        "key": "test_dest_key",
        "type": StorageType.s3.value,
        "details": {
            "bucket": "some-bucket",
            "naming": "something invalid",
            "max_retries": 10,
        },
        "secrets": {
            StorageSecrets.AWS_ACCESS_KEY_ID.value: "1345234524",
            StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "23451345834789",
        },
    }
    sc = StorageConfig.create(db, data=mock_config)

    upload_data = {"phone": "1231231234"}

    with pytest.raises(ValueError):
        upload(
            db=db,
            privacy_request=privacy_request,
            data=upload_data,
            storage_key=mock_config["key"],
        )

    mock_upload_to_s3.assert_not_called()
    sc.delete(db)


@mock.patch("fides.api.service.storage.storage_uploader_service.upload_to_s3")
def test_uploader_no_config(
    mock_upload_to_s3: Mock, db: Session, privacy_request: PrivacyRequest
) -> None:
    request_id = privacy_request.id
    storage_key = "s3_key"

    upload_data = {"phone": "1231231234"}

    with pytest.raises(StorageUploadError):
        upload(
            db=db,
            privacy_request=privacy_request,
            data=upload_data,
            storage_key=storage_key,
        )

    mock_upload_to_s3.assert_not_called()


def test_uploader_local_success(db: Session, privacy_request: PrivacyRequest) -> None:
    request_id = privacy_request.id

    mock_config = {
        "name": "test dest",
        "key": "test_dest_local",
        "type": StorageType.local.value,
        "details": {
            StorageDetails.NAMING.value: FileNaming.request_id.value,
        },
        "secrets": None,
    }
    config = StorageConfig.create(db, data=mock_config)

    upload_data = {
        "mysql.users": {"name": "Hannah Testing"},
        "mongo.orders": {
            "orderId": "23456",
            "phone": "234523454",
            "address": "123 mains st",
            "birthday": datetime(1995, 1, 1),
            "city": "Plainville",
        },
    }

    resulting_uploaded_data = {
        "mysql.users": {"name": "Hannah Testing"},
        "mongo.orders": {
            "orderId": "23456",
            "phone": "234523454",
            "address": "123 mains st",
            "birthday": "1995-01-01T00:00:00",
            "city": "Plainville",
        },
    }

    upload(
        db=db,
        privacy_request=privacy_request,
        data=upload_data,
        storage_key=mock_config["key"],
    )
    with open(f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{request_id}.json") as f:
        d = json.load(f)
        assert d == resulting_uploaded_data
    os.remove(f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{request_id}.json")
    config.delete(db)


def test_uploader_local_dsr_package(
    db: Session, privacy_request: PrivacyRequest
) -> None:
    mock_config = {
        "name": "test dest",
        "key": "test_dest_local",
        "type": StorageType.local.value,
        "details": {
            StorageDetails.NAMING.value: FileNaming.request_id.value,
        },
        "secrets": None,
        "format": ResponseFormat.html.value,
    }
    config = StorageConfig.create(db, data=mock_config)

    upload_data = {
        "mysql:users": [{"name": "Hannah Testing"}],
        "mongo:orders": [
            {
                "orderId": "23456",
                "phone": "234523454",
                "address": "123 mains st",
                "birthday": datetime(1995, 1, 1),
                "city": "Plainville",
            }
        ],
    }

    upload(
        db=db,
        privacy_request=privacy_request,
        data=upload_data,
        storage_key=mock_config["key"],
    )

    dsr_report_path = f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{privacy_request.id}.zip"
    assert os.path.isfile(dsr_report_path)
    os.remove(dsr_report_path)
    config.delete(db)


class TestWriteToInMemoryBuffer:
    key = "test--encryption"

    @pytest.fixture(scope="function")
    def privacy_request_with_encryption_keys(self, privacy_request) -> Generator:
        privacy_request.cache_encryption(self.key)
        return privacy_request

    @pytest.fixture(scope="function")
    def data(self) -> Dict[str, Any]:
        return {
            "mongo:address": [
                {"id": 1, "zip": 10024, "city": "Cañon City"},
                {"id": 2, "zip": 10011, "city": "Venice"},
            ],
            "mysql:customer": [
                {"uuid": "xyz-112-333", "name": "foo", "email": "foo@bar"},
                {"uuid": "xyz-122-333", "name": "foo1", "email": "foo@bar1"},
            ],
            "mongo:foobar": [{"_id": 1, "customer": {"x": 1, "y": [1, 2]}}],
            "filing_cabinet": [{"id": "123"}],  # represents manual data
        }

    def test_json_data(self, data, privacy_request):
        buff = write_to_in_memory_buffer("json", data, privacy_request)
        assert isinstance(buff, BytesIO)
        assert json.load(buff) == data

    def test_csv_format(self, data, privacy_request):
        buff = write_to_in_memory_buffer("csv", data, privacy_request)
        assert isinstance(buff, BytesIO)

        zipfile = ZipFile(buff)
        assert zipfile.namelist() == [
            "mongo:address.csv",
            "mysql:customer.csv",
            "mongo:foobar.csv",
            "filing_cabinet.csv",
        ]

        with zipfile.open("mongo:address.csv") as address_csv:
            df = pd.read_csv(address_csv, encoding="utf-8")

            assert list(df.columns) == [
                "id",
                "zip",
                "city",
            ]
            assert list(df.iloc[0]) == [
                1,
                10024,
                "Cañon City",
            ]

            assert list(df.iloc[1]) == [
                2,
                10011,
                "Venice",
            ]

        with zipfile.open("mysql:customer.csv") as foobar_csv:
            df = pd.read_csv(foobar_csv, encoding="utf-8")

            assert list(df.columns) == [
                "uuid",
                "name",
                "email",
            ]
            assert list(df.iloc[0]) == [
                "xyz-112-333",
                "foo",
                "foo@bar",
            ]

            assert list(df.iloc[1]) == [
                "xyz-122-333",
                "foo1",
                "foo@bar1",
            ]

        with zipfile.open("mongo:foobar.csv") as customer_csv:
            df = pd.read_csv(customer_csv, encoding="utf-8")

            assert list(df.columns) == [
                "_id",
                "customer.x",
                "customer.y",
            ]

            assert list(df.iloc[0]) == [
                1,
                1,
                "[1, 2]",
            ]

    def test_html_format(self, data, privacy_request):
        buff = write_to_in_memory_buffer("html", data, privacy_request)
        assert isinstance(buff, BytesIO)

        zipfile = ZipFile(buff)
        assert zipfile.namelist() == [
            "data/main.css",
            "data/back.svg",
            "data/mongo/address/1.html",
            "data/mongo/address/2.html",
            "data/mongo/address/index.html",
            "data/mongo/foobar/1.html",
            "data/mongo/foobar/index.html",
            "data/mongo/index.html",
            "data/mysql/customer/1.html",
            "data/mysql/customer/2.html",
            "data/mysql/customer/index.html",
            "data/mysql/index.html",
            "data/manual/filing_cabinet/1.html",
            "data/manual/filing_cabinet/index.html",
            "data/manual/index.html",
            "welcome.html",
        ]

    def test_not_implemented(self, data, privacy_request):
        with pytest.raises(NotImplementedError):
            write_to_in_memory_buffer("not-a-valid-format", data, privacy_request)

    def test_encrypted_json(self, data, privacy_request_with_encryption_keys):
        original_data = data
        buff = write_to_in_memory_buffer(
            "json", data, privacy_request_with_encryption_keys
        )
        assert isinstance(buff, BytesIO)
        encrypted = buff.read()
        data = encrypted.decode(CONFIG.security.encoding)
        decrypted = decrypt_combined_nonce_and_message(
            data, self.key.encode(CONFIG.security.encoding)
        )
        assert json.loads(decrypted) == original_data

    def test_encrypted_csv(self, data, privacy_request_with_encryption_keys):
        buff = write_to_in_memory_buffer(
            "csv", data, privacy_request_with_encryption_keys
        )
        assert isinstance(buff, BytesIO)

        zipfile = ZipFile(buff)

        with zipfile.open("mongo:address.csv", "r") as address_csv:
            data = address_csv.read().decode(CONFIG.security.encoding)

            decrypted = decrypt_combined_nonce_and_message(
                data, self.key.encode(CONFIG.security.encoding)
            )

            binary_stream = BytesIO(decrypted.encode(CONFIG.security.encoding))
            df = pd.read_csv(binary_stream, encoding=CONFIG.security.encoding)
            assert list(df.columns) == [
                "id",
                "zip",
                "city",
            ]
            assert list(df.iloc[0]) == [
                1,
                10024,
                "Cañon City",
            ]

            assert list(df.iloc[1]) == [
                2,
                10011,
                "Venice",
            ]


class TestEncryptResultsPackage:
    def test_no_encryption_keys_set(self):
        data = "test data"
        ret = encrypt_access_request_results(data, request_id="test-request-id")

        assert ret == data

    def test_key_and_nonce_set(self, privacy_request):
        key = "abvnfhrke8398398"
        privacy_request.cache_encryption("abvnfhrke8398398")
        data = "test data"
        ret = encrypt_access_request_results(data, request_id=privacy_request.id)
        decrypted = decrypt_combined_nonce_and_message(
            ret, key.encode(CONFIG.security.encoding)
        )
        assert data == decrypted


def test_get_extension():
    assert get_extension(ResponseFormat.json) == "json"
    assert get_extension(ResponseFormat.csv) == "zip"
    assert get_extension(ResponseFormat.html) == "zip"
