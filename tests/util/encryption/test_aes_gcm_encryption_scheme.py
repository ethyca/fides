import pytest

from fidesops.util import cryptographic_util
from fidesops.util.encryption.aes_gcm_encryption_scheme import encrypt, decrypt

NONCE = b"B\xab\x93&\x99u\x0c\xea\xe9\xb7\x8dU"
KEY = b"y\xc5I\xd4\x92\xf6G\t\x80\xb1$\x06\x19t/\xc4"


def test_encrypt_decrypt_standard():
    plaintext = "Be sure to drink your Ovaltine"
    encrypted_response = encrypt(plaintext, KEY, NONCE)
    decrypted_text = decrypt(encrypted_response, KEY, NONCE)
    assert decrypted_text == plaintext


def test_encrypt_bad_nonce():
    with pytest.raises(ValueError):
        encrypt("anything", KEY, b"")


def test_encrypt_bad_key():
    with pytest.raises(ValueError):
        encrypt(
            "anything",
            cryptographic_util.generate_secure_random_string(13).encode("UTF-8"),
            NONCE,
        )


def test_decrypt_bad_nonce():
    with pytest.raises(ValueError):
        decrypt("anything", KEY, b"")


def test_decrypt_bad_key():
    with pytest.raises(ValueError):
        decrypt(
            "anything",
            cryptographic_util.generate_secure_random_string(13).encode("UTF-8"),
            NONCE,
        )
