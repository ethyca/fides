from fidesops.schemas.masking.masking_configuration import HmacMaskingConfiguration
from fidesops.util.encryption.hmac_encryption_scheme import (
    hmac_encrypt_return_bytes,
    hmac_encrypt_return_str,
)

KEY = "aksdjhflajsdf"
SALT = "lqio3nrulionqwjlfkj"


def test_encrypt_return_bytes():
    plaintext = "I am a cat meow"
    encrypted = hmac_encrypt_return_bytes(
        plaintext, KEY, SALT, HmacMaskingConfiguration.Algorithm.sha_256
    )
    assert (
        encrypted
        == b"\x16\xb6\x88\xf2\xab\xfe\x0c\xd4\xe9bc&.\xb2e\xe2\xd7\xf1\xde\xf2Gb\xa3\x9d\xa7\xf8\xe9\xc4\x18\xf9\x95\t"
    )


def test_encrypt_return_string():
    plaintext = "I am a dog woof"
    encrypted = hmac_encrypt_return_str(
        plaintext, KEY, SALT, HmacMaskingConfiguration.Algorithm.sha_256
    )
    assert (
        encrypted == "360a7d27a927d1fb3436e7edabe86cba5f96f671874975e628fb80245cc229ab"
    )
