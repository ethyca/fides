from enum import Enum


class DataType(Enum):
    """Supported data types for data retrieval and erasure.

    This type list is based on json-schema, with some alterations:
    - mongo_object_id is added to address mongodb keys
    - the json-schema 'null' type is omitted
    """

    string = "string"
    integer = "integer"
    number = "number"
    boolean = "boolean"
    mongo_object_id = "mongo_object_id"
