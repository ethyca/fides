from bson import ObjectId

from fidesops.graph.data_type import DataType


def test_int_convert():
    converter = DataType.integer.value
    assert converter.to_value("1") == 1
    assert converter.to_value(1.0) == 1
    assert converter.to_value(1) == 1
    assert converter.to_value("A") is None


def test_string_convert():
    converter = DataType.string.value
    assert converter.to_value(1.0) == "1.0"
    assert converter.to_value(1) == "1"
    assert (
        converter.to_value(ObjectId("abc123abc123abc123abc123"))
        == "abc123abc123abc123abc123"
    )


def test_float_convert():
    converter = DataType.float.value
    assert converter.to_value(1) == 1.0
    assert converter.to_value("1.0") == 1.0


def test_bool_convert():
    converter = DataType.boolean.value
    assert converter.to_value(1) == True
    assert converter.to_value(0) == False
    assert converter.to_value("True") == True
    assert converter.to_value("False") == False
    assert converter.to_value("NOT A BOOLEAN ") is None


def test_object_id_convert():
    converter = DataType.object_id.value
    assert converter.to_value("abc123abc123abc123abc123") == ObjectId(
        "abc123abc123abc123abc123"
    )
    assert converter.to_value("abc123abc1") is None


def test_safe_none_conversion():
    """Ensure that None is safely handled in any type."""
    for data_type in DataType:
        converter = data_type.value
        assert converter.to_value(None) is None
