from typing import List


def sort_list_objects(cls, values: List) -> List:
    values.sort(key=lambda value: value.name)
    return values
