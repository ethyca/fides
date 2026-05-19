import pytest

from fides.config.secrets.base import SecretValue


class TestSecretValue:
    def test_subscript_access(self):
        sv = SecretValue({"username": "admin", "password": "s3cret"})
        assert sv["username"] == "admin"
        assert sv["password"] == "s3cret"

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

    def test_contains_checks_fields(self):
        sv = SecretValue({"username": "admin", "password": "s3cret"})
        assert "username" in sv
        assert "password" in sv
        assert "other" not in sv

    def test_dict_conversion_blocked(self):
        sv = SecretValue({"password": "s3cret"})
        with pytest.raises(TypeError):
            dict(sv)

    def test_unpacking_blocked(self):
        sv = SecretValue({"password": "s3cret"})
        with pytest.raises(TypeError):
            {**sv}

    def test_vars_blocked(self):
        sv = SecretValue({"password": "s3cret"})
        with pytest.raises(TypeError):
            vars(sv)

    def test_no_dict(self):
        sv = SecretValue({"password": "s3cret"})
        assert not hasattr(sv, "__dict__")

    def test_pickle_blocked(self):
        import pickle  # local import — only used in this test

        sv = SecretValue({"password": "s3cret"})
        with pytest.raises(TypeError, match="cannot be pickled"):
            pickle.dumps(sv)

    def test_getstate_blocked(self):
        sv = SecretValue({"password": "s3cret"})
        with pytest.raises(TypeError, match="cannot be serialized"):
            sv.__getstate__()

    def test_copy_blocked(self):
        import copy  # local import — only used in this test

        sv = SecretValue({"password": "s3cret"})
        with pytest.raises(TypeError):
            copy.copy(sv)
