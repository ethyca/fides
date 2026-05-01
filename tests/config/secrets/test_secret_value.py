import pytest

from fides.config.secrets.base import SecretValue


class TestSecretValue:
    def test_subscript_access(self):
        sv = SecretValue({"username": "admin", "password": "hunter2"})
        assert sv["username"] == "admin"
        assert sv["password"] == "hunter2"

    def test_missing_key_raises_key_error(self):
        sv = SecretValue({"username": "admin"})
        with pytest.raises(KeyError):
            _ = sv["nonexistent"]

    def test_contains(self):
        sv = SecretValue({"username": "admin"})
        assert "username" in sv
        assert "missing" not in sv

    def test_repr_is_redacted(self):
        sv = SecretValue({"password": "super-secret"})
        assert repr(sv) == "<redacted>"

    def test_str_is_redacted(self):
        sv = SecretValue({"password": "super-secret"})
        assert str(sv) == "<redacted>"

    def test_fstring_is_redacted(self):
        sv = SecretValue({"password": "super-secret"})
        assert f"value={sv}" == "value=<redacted>"

    def test_equality(self):
        a = SecretValue({"k": "v"})
        b = SecretValue({"k": "v"})
        assert a == b

    def test_inequality(self):
        a = SecretValue({"k": "v1"})
        b = SecretValue({"k": "v2"})
        assert a != b

    def test_equality_with_non_secret_value(self):
        sv = SecretValue({"k": "v"})
        assert sv != {"k": "v"}

    def test_keys(self):
        sv = SecretValue({"username": "admin", "password": "hunter2"})
        assert set(sv.keys()) == {"username", "password"}
