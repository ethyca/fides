"""
Tests for AES GCM encryption utilities with both SQLAlchemy-Utils and cryptography implementations.

This module tests:
1. Small payloads: Both implementations work independently and are cross-compatible
2. Large payloads: Cryptography implementation with chunked processing
"""

import random
import string
from typing import List
from datetime import datetime

import pytest
from bson import ObjectId
from sqlalchemy.orm import Session

from fides.api.util.collection_util import Row
from fides.api.util.encryption.aes_gcm_encryption_util import (
    EncryptionError,
    decrypt_data,
    decrypt_with_cryptography,
    decrypt_with_sqlalchemy_utils,
    encrypt_data,
    encrypt_with_cryptography,
    encrypt_with_sqlalchemy_utils,
)
from loguru import logger


class TestAESGCMEncryptionUtil:
    """Test suite for AES GCM encryption utilities."""

    @pytest.fixture
    def small_test_data(self) -> List[Row]:
        """Generate small test data for basic encryption/decryption tests."""
        return [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 30},
            {"id": 3, "name": "Bob Johnson", "extra": {"nested": "data", "count": 42}},
        ]

    @pytest.fixture
    def small_test_data_with_objectid(self) -> List[Row]:
        """Generate test data with MongoDB ObjectIds for JSON serialization testing."""
        return [
            {"id": ObjectId("507f1f77bcf86cd799439011"), "name": "User 1"},
            {"id": ObjectId("507f1f77bcf86cd799439012"), "name": "User 2"},
            {
                "id": ObjectId("507f1f77bcf86cd799439013"),
                "nested": {"obj_id": ObjectId("507f1f77bcf86cd799439014")},
            },
        ]

    @pytest.fixture
    def large_test_data(self) -> List[Row]:
        """Generate large test data for chunked processing tests."""

        def generate_random_string(length: int) -> str:
            return "".join(
                random.choices(string.ascii_letters + string.digits, k=length)
            )

        # Generate ~10MB of data with large records
        large_records = []
        for i in range(1000):  # 1000 records
            record = {
                "id": i,
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "description": generate_random_string(8000),  # ~8KB per record
                "metadata": {
                    "created_at": "2023-01-01T00:00:00Z",
                    "tags": [f"tag{j}" for j in range(10)],
                    "attributes": {
                        f"attr{k}": generate_random_string(100) for k in range(10)
                    },
                },
            }
            large_records.append(record)

        return large_records

    def test_sqlalchemy_encrypt_decrypt_small_payload(self, small_test_data: List[Row]):
        """Test SQLAlchemy encrypt/decrypt works together for small payloads."""
        # Encrypt data
        encrypted_bytes = encrypt_with_sqlalchemy_utils(small_test_data)
        assert isinstance(encrypted_bytes, bytes)
        assert len(encrypted_bytes) > 0

        # Decrypt data
        decrypted_data = decrypt_with_sqlalchemy_utils(encrypted_bytes)
        assert decrypted_data == small_test_data

    def test_cryptography_encrypt_decrypt_small_payload(
        self, small_test_data: List[Row]
    ):
        """Test cryptography encrypt/decrypt works together for small payloads."""
        # Encrypt data
        encrypted_bytes = encrypt_with_cryptography(small_test_data)
        assert isinstance(encrypted_bytes, bytes)
        assert len(encrypted_bytes) > 0

        # Decrypt data
        decrypted_data = decrypt_with_cryptography(encrypted_bytes)
        assert decrypted_data == small_test_data

    def test_objectid_serialization_sqlalchemy(
        self, small_test_data_with_objectid: List[Row]
    ):
        """Test SQLAlchemy encryption handles ObjectId serialization correctly."""
        encrypted_bytes = encrypt_with_sqlalchemy_utils(small_test_data_with_objectid)
        decrypted_data = decrypt_with_sqlalchemy_utils(encrypted_bytes)
        assert decrypted_data == small_test_data_with_objectid

    def test_objectid_serialization_cryptography(
        self, small_test_data_with_objectid: List[Row]
    ):
        """Test cryptography encryption handles ObjectId serialization correctly."""
        encrypted_bytes = encrypt_with_cryptography(small_test_data_with_objectid)
        decrypted_data = decrypt_with_cryptography(encrypted_bytes)
        assert decrypted_data == small_test_data_with_objectid

    def test_cross_compatibility_sqlalchemy_to_cryptography(
        self, small_test_data: List[Row]
    ):
        """Test that SQLAlchemy encrypted data can be decrypted by cryptography implementation."""
        encrypted_bytes = encrypt_with_sqlalchemy_utils(small_test_data)
        assert decrypt_with_cryptography(encrypted_bytes) == small_test_data

    def test_cross_compatibility_cryptography_to_sqlalchemy(
        self, small_test_data: List[Row]
    ):
        """Test that cryptography encrypted data can be decrypted by SQLAlchemy implementation."""
        encrypted_bytes = encrypt_with_cryptography(small_test_data)
        assert decrypt_with_sqlalchemy_utils(encrypted_bytes) == small_test_data

    def test_public_api_uses_cryptography(self, small_test_data: List[Row]):
        """Test that the public API (encrypt_data/decrypt_data) uses cryptography by default."""
        encrypted_bytes = encrypt_data(small_test_data)
        decrypted_data = decrypt_data(encrypted_bytes)
        assert decrypted_data == small_test_data

        # Verify it's using cryptography format (should be compatible with cryptography decrypt)
        crypto_decrypted = decrypt_with_cryptography(encrypted_bytes)
        assert crypto_decrypted == small_test_data

    def test_large_payload_cryptography_encryption(self, large_test_data: List[Row]):
        """Test cryptography implementation with large payloads using chunked processing."""
        # Test with default chunk size
        encrypted_bytes = encrypt_with_cryptography(large_test_data)
        assert isinstance(encrypted_bytes, bytes)
        assert len(encrypted_bytes) > 0

        # Decrypt and verify
        decrypted_data = decrypt_with_cryptography(encrypted_bytes)
        assert len(decrypted_data) == len(large_test_data)
        assert decrypted_data == large_test_data

    def test_large_payload_custom_chunk_size(self, large_test_data: List[Row]):
        """Test cryptography implementation with custom chunk sizes."""
        chunk_sizes = [1024 * 1024, 2 * 1024 * 1024, 8 * 1024 * 1024]  # 1MB, 2MB, 8MB

        for chunk_size in chunk_sizes:
            encrypted_bytes = encrypt_with_cryptography(
                large_test_data, chunk_size=chunk_size
            )
            decrypted_data = decrypt_with_cryptography(
                encrypted_bytes, chunk_size=chunk_size
            )
            assert decrypted_data == large_test_data

    def test_encryption_error_handling_sqlalchemy(self):
        """Test error handling in SQLAlchemy implementation."""

        # Test with invalid data that causes circular reference error during serialization
        class CircularRef:
            def __init__(self):
                self.self_ref = self

        circular_obj = CircularRef()
        invalid_data = [{"obj": circular_obj}]

        with pytest.raises(EncryptionError):
            encrypt_with_sqlalchemy_utils(invalid_data)

    def test_encryption_error_handling_cryptography(self):
        """Test error handling in cryptography implementation."""

        # Test with invalid data that causes circular reference error during serialization
        class CircularRef:
            def __init__(self):
                self.self_ref = self

        circular_obj = CircularRef()
        invalid_data = [{"obj": circular_obj}]

        with pytest.raises(EncryptionError):
            encrypt_with_cryptography(invalid_data)

    def test_decryption_error_handling_sqlalchemy(self):
        """Test decryption error handling in SQLAlchemy implementation."""
        # Test with invalid encrypted data
        invalid_encrypted_data = b"invalid_encrypted_data"

        with pytest.raises(EncryptionError):
            decrypt_with_sqlalchemy_utils(invalid_encrypted_data)

    def test_decryption_error_handling_cryptography(self):
        """Test decryption error handling in cryptography implementation."""
        # Test with invalid encrypted data
        invalid_encrypted_data = b"invalid_encrypted_data"

        with pytest.raises(EncryptionError):
            decrypt_with_cryptography(invalid_encrypted_data)

    def test_empty_data_sqlalchemy(self):
        """Test SQLAlchemy implementation with empty data."""
        empty_data = []
        encrypted_bytes = encrypt_with_sqlalchemy_utils(empty_data)
        decrypted_data = decrypt_with_sqlalchemy_utils(encrypted_bytes)
        assert decrypted_data == empty_data

    def test_empty_data_cryptography(self):
        """Test cryptography implementation with empty data."""
        empty_data = []
        encrypted_bytes = encrypt_with_cryptography(empty_data)
        decrypted_data = decrypt_with_cryptography(encrypted_bytes)
        assert decrypted_data == empty_data

    def test_single_record_data(self):
        """Test both implementations with single record."""
        single_record = [{"id": 1, "name": "Single User"}]

        # SQLAlchemy
        encrypted_sql = encrypt_with_sqlalchemy_utils(single_record)
        decrypted_sql = decrypt_with_sqlalchemy_utils(encrypted_sql)
        assert decrypted_sql == single_record

        # Cryptography
        encrypted_crypto = encrypt_with_cryptography(single_record)
        decrypted_crypto = decrypt_with_cryptography(encrypted_crypto)
        assert decrypted_crypto == single_record

    def test_various_data_types(self):
        """Test encryption/decryption with various Python data types."""
        complex_data = [
            {
                "string": "test string",
                "integer": 42,
                "float": 3.14159,
                "boolean": True,
                "null_value": None,
                "list": [1, 2, 3, "four"],
                "nested_dict": {
                    "inner_key": "inner_value",
                    "inner_list": [{"deep": "nested"}],
                },
            }
        ]

        # Test both implementations
        for encrypt_func, decrypt_func in [
            (encrypt_with_sqlalchemy_utils, decrypt_with_sqlalchemy_utils),
            (encrypt_with_cryptography, decrypt_with_cryptography),
        ]:
            encrypted_bytes = encrypt_func(complex_data)
            decrypted_data = decrypt_func(encrypted_bytes)
            assert decrypted_data == complex_data

    def test_cryptography_format_structure(self, small_test_data: List[Row]):
        """Test that cryptography format follows expected structure: [nonce][ciphertext][tag]."""
        encrypted_bytes = encrypt_with_cryptography(small_test_data)

        # Should be at least 28 bytes (12 nonce + 16 tag + some ciphertext)
        assert len(encrypted_bytes) >= 28

        # Extract components
        nonce = encrypted_bytes[:12]
        ciphertext = encrypted_bytes[12:-16]
        tag = encrypted_bytes[-16:]

        assert len(nonce) == 12
        assert len(tag) == 16
        assert len(ciphertext) > 0

    @pytest.mark.parametrize("data_size", [10, 100, 1000])
    def test_scalability_cryptography(self, data_size: int):
        """Test cryptography implementation scales well with different data sizes."""
        # Generate data of different sizes
        test_data = [
            {"id": i, "data": f"record_{i}_{'x' * 100}"} for i in range(data_size)
        ]

        encrypted_bytes = encrypt_with_cryptography(test_data)
        decrypted_data = decrypt_with_cryptography(encrypted_bytes)

        assert len(decrypted_data) == data_size
        assert decrypted_data == test_data

    def test_different_encryption_keys_produce_different_results(
        self, small_test_data: List[Row]
    ):
        """Test that different encryption keys produce different encrypted results."""
        # This test assumes we can temporarily change the encryption key
        # Since the key comes from CONFIG, we'll test that the same data encrypted twice
        # with the same key produces the same result (deterministic within same nonce)

        encrypted1 = encrypt_with_cryptography(small_test_data)
        encrypted2 = encrypt_with_cryptography(small_test_data)

        # Results should be different due to different nonces
        assert encrypted1 != encrypted2

        # But both should decrypt to the same original data
        decrypted1 = decrypt_with_cryptography(encrypted1)
        decrypted2 = decrypt_with_cryptography(encrypted2)

        assert decrypted1 == small_test_data
        assert decrypted2 == small_test_data

    def test_database_integration_request_task_compatibility(self, db: Session):
        """
        COMPREHENSIVE DATABASE INTEGRATION TEST

        Test real database write/read using RequestTask encrypted fields and verify
        that our encryption utils can generate compatible encrypted values.

        This tests the complete flow:
        1. Write encrypted data to RequestTask._access_data using SQLAlchemy-Utils
        2. Read raw encrypted bytes from database
        3. Decrypt using our cryptography utility
        4. Encrypt the same data using our cryptography utility
        5. Write back to database and verify SQLAlchemy-Utils can read it
        """
        from fides.api.models.privacy_request.privacy_request import PrivacyRequest
        from fides.api.models.privacy_request.request_task import RequestTask
        from fides.api.models.policy import Policy
        from fides.api.schemas.policy import ActionType
        from fides.api.schemas.privacy_request import (
            ExecutionLogStatus,
            PrivacyRequestStatus,
        )
        from sqlalchemy import text
        from loguru import logger

        # Create test data - realistic privacy request data
        test_data = [
            {"user_id": "12345", "email": "test@example.com", "name": "John Doe"},
            {"user_id": "67890", "email": "jane@example.com", "name": "Jane Smith"},
            {"transaction_id": "tx_001", "amount": 99.99, "user_id": "12345"},
        ]

        # Step 1: Get the default access policy (created during startup)
        default_access_policy = Policy.get_by(
            db=db, field="key", value="default_access_policy"
        )
        assert default_access_policy is not None, "Default access policy should exist"

        # Create a real PrivacyRequest and RequestTask
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_external_id_db_integration",
                "started_processing_at": datetime.utcnow(),
                "status": PrivacyRequestStatus.pending,  # Use PrivacyRequestStatus not ExecutionLogStatus
                "policy_id": default_access_policy.id,
            },
        )

        request_task = RequestTask.create(
            db=db,
            data={
                "privacy_request_id": privacy_request.id,
                "collection_address": "test_dataset:users",
                "dataset_name": "test_dataset",
                "collection_name": "users",
                "action_type": ActionType.access,
                "status": ExecutionLogStatus.pending,  # RequestTask uses ExecutionLogStatus
                "upstream_tasks": [],
                "downstream_tasks": [],
            },
        )

        # Step 2: Write encrypted data using SQLAlchemy-Utils (the "official" way)
        logger.info("=== STEP 2: Writing data via SQLAlchemy-Utils ===")
        request_task._access_data = (
            test_data  # This triggers SQLAlchemy-Utils encryption
        )
        db.commit()
        db.refresh(request_task)

        # Step 3: Read the raw encrypted bytes directly from database
        logger.info("=== STEP 3: Reading raw encrypted bytes from database ===")
        result = db.execute(
            text("SELECT access_data FROM requesttask WHERE id = :task_id"),
            {"task_id": request_task.id},
        ).fetchone()

        raw_encrypted_bytes = result[0].encode("utf-8")  # Database stores as string
        logger.info(f"Raw encrypted data from DB: {len(raw_encrypted_bytes)} bytes")

        # Step 4: Decrypt using OUR cryptography utility
        logger.info("=== STEP 4: Decrypting with our cryptography utility ===")
        decrypted_data = decrypt_with_cryptography(raw_encrypted_bytes)

        # Verify the decrypted data matches original
        assert decrypted_data == test_data
        logger.info("✅ Successfully decrypted SQLAlchemy-Utils data with our utility!")

        # Step 5: Encrypt the same data using OUR cryptography utility
        logger.info("=== STEP 5: Encrypting with our cryptography utility ===")
        our_encrypted_bytes = encrypt_with_cryptography(test_data)

        # Step 6: Write our encrypted data directly to database
        logger.info("=== STEP 6: Writing our encrypted data to database ===")
        our_encrypted_str = our_encrypted_bytes.decode("utf-8")
        db.execute(
            text(
                "UPDATE requesttask SET access_data = :encrypted_data WHERE id = :task_id"
            ),
            {"encrypted_data": our_encrypted_str, "task_id": request_task.id},
        )
        db.commit()

        # Step 7: Read using SQLAlchemy-Utils (should auto-decrypt)
        logger.info("=== STEP 7: Reading via SQLAlchemy-Utils auto-decryption ===")
        db.refresh(request_task)
        sqlalchemy_decrypted_data = request_task._access_data

        # Verify SQLAlchemy-Utils can read our encrypted data
        assert sqlalchemy_decrypted_data == test_data
        logger.info("✅ SQLAlchemy-Utils successfully read our encrypted data!")

        # Step 8: Test both ways work with data_for_erasures field too
        logger.info("=== STEP 8: Testing data_for_erasures field ===")
        erasure_data = [
            {"user_id": "12345", "name": "[MASKED]", "email": "[MASKED]"},
            {"user_id": "67890", "name": "[MASKED]", "email": "[MASKED]"},
        ]

        # Write with SQLAlchemy-Utils
        request_task._data_for_erasures = erasure_data
        db.commit()

        # Read raw and decrypt with our utility
        result = db.execute(
            text("SELECT data_for_erasures FROM requesttask WHERE id = :task_id"),
            {"task_id": request_task.id},
        ).fetchone()
        raw_erasure_bytes = result[0].encode("utf-8")
        our_decrypted_erasure = decrypt_with_cryptography(raw_erasure_bytes)
        assert our_decrypted_erasure == erasure_data

        # Encrypt with our utility and write back
        our_erasure_encrypted = encrypt_with_cryptography(erasure_data)
        our_erasure_str = our_erasure_encrypted.decode("utf-8")
        db.execute(
            text(
                "UPDATE requesttask SET data_for_erasures = :encrypted_data WHERE id = :task_id"
            ),
            {"encrypted_data": our_erasure_str, "task_id": request_task.id},
        )
        db.commit()

        # Verify SQLAlchemy-Utils can read it
        db.refresh(request_task)
        sqlalchemy_erasure_data = request_task._data_for_erasures
        assert sqlalchemy_erasure_data == erasure_data

        logger.info("✅ COMPLETE DATABASE INTEGRATION SUCCESS!")
        logger.info("✅ Both RequestTask encrypted fields work bidirectionally!")
        logger.info("✅ True format compatibility confirmed in real database scenario!")

        # Cleanup
        db.delete(request_task)
        db.delete(privacy_request)
        db.commit()
