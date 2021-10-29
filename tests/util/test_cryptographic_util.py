from fidesops.core.config import config
from fidesops.util.cryptographic_util import hash_with_salt


def test_hash_with_salt() -> None:
    plain_text = "This is Plaintext. Not hashed. or salted. or chopped. or grilled."
    salt = "adobo"

    expected_hash = "3318b888645e6599289be9bee8ac0af2e63eb095213b7269f84845303abde55c7c0f9879cd69d7f453716e439ba38dd8d9b7f0bec67fe9258fb55d90e94c972d"
    hashed = hash_with_salt(
        plain_text.encode(config.security.ENCODING),
        salt.encode(config.security.ENCODING),
    )

    assert hashed == expected_hash
