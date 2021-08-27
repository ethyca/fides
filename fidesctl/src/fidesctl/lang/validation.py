from typing import Callable, List


def sort_list_objects(cls: Callable, values: List) -> List:
    values.sort(key=lambda value: value.name)
    return values
