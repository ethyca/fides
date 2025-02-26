from typing import Any

from cassandra.util import Date, Duration, OrderedMapSerializedKey, SortedSet, Time


def scylla_to_native_python(data: Any) -> Any:  # type: ignore[misc] # pylint: disable=too-many-return-statements
    """Recursively convert some non-standard Scylla types to native Python types

    Scylla also supports 3 kinds of collections: maps, lists, and sets
    """
    if isinstance(data, OrderedMapSerializedKey):
        return scylla_to_native_python(dict(data))
    if isinstance(data, SortedSet):
        return scylla_to_native_python(set(data))
    if isinstance(data, Date):
        return data.date()
    if isinstance(data, Time):
        return data.time()
    if isinstance(data, Duration):
        # This is in a tuple format of months, days, nanoseconds
        # For now, returning as-is
        return data
    if isinstance(data, list):
        return [scylla_to_native_python(elem) for elem in data]
    if isinstance(data, set):
        return {scylla_to_native_python(elem) for elem in data}
    if isinstance(data, dict):
        return {
            scylla_to_native_python(key): scylla_to_native_python(value)
            for key, value in data.items()
        }

    return data
