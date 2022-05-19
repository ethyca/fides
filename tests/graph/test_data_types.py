from bson import ObjectId

from fidesops.graph.data_type import (
    DataType,
    NoOpTypeConverter,
    StringTypeConverter,
    get_data_type_converter,
    is_valid_data_type,
    parse_data_type_string,
)


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


def test_get_data_type_converter():
    assert isinstance(get_data_type_converter(None), NoOpTypeConverter)
    assert isinstance(get_data_type_converter(""), NoOpTypeConverter)
    assert isinstance(get_data_type_converter("string"), StringTypeConverter)


def test_parse_data_type_string():
    assert parse_data_type_string("string") == ("string", False)
    assert parse_data_type_string("string[]") == ("string", True)


def test_valid():
    for s in ["string", "integer", "float", "boolean", "object_id", "object", None]:
        assert is_valid_data_type(s)

    assert not is_valid_data_type("unknown")
