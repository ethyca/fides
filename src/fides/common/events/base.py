"""Event class validation + dataclass <-> dict serialization.

Events are domain entities — frozen dataclasses with JSON-primitive fields.
This module enforces those constraints at decoration time so problems surface
at boot, not at dispatch.

See `docs/fides/docs/event-framework/01-design.md` §6.1.
"""

from dataclasses import asdict, fields, is_dataclass
from typing import Any, Union, get_args, get_origin
from typing import get_type_hints as _get_type_hints

# Field types accepted directly in event payloads (JSON-primitive).
_PRIMITIVE_TYPES: tuple = (str, int, float, bool, type(None))


class InvalidEventTypeError(TypeError):
    """Raised when a class is registered as an event but does not satisfy
    the framework's constraints (frozen dataclass with JSON-primitive fields)."""


def validate_event_class(cls: type) -> None:
    """Validate that ``cls`` is a usable event type.

    Requirements:
    - ``cls`` is a dataclass.
    - ``cls`` is frozen.
    - Every field's type resolves to JSON-primitive types, containers of
      those (list / tuple / set / frozenset / dict), Optional/Union of those,
      or another frozen dataclass that itself passes validation.

    Raises:
        InvalidEventTypeError: with a message identifying the offending
        class and field, if validation fails.
    """
    if not is_dataclass(cls):
        raise InvalidEventTypeError(
            f"{cls!r} is not a dataclass. Events must be defined with "
            f"@dataclass(frozen=True)."
        )
    params = getattr(cls, "__dataclass_params__", None)
    if params is None or not params.frozen:
        raise InvalidEventTypeError(
            f"{cls.__name__} must be frozen. Use @dataclass(frozen=True)."
        )

    # Resolve string annotations (handles `from __future__ import annotations`).
    try:
        hints = _get_type_hints(cls)
    except Exception as exc:  # pragma: no cover - extremely rare
        raise InvalidEventTypeError(
            f"Could not resolve type hints for {cls.__name__}: {exc}"
        ) from exc

    for f in fields(cls):
        field_type = hints.get(f.name, f.type)
        _validate_field_type(cls.__name__, f.name, field_type)


def _validate_field_type(cls_name: str, field_name: str, field_type: Any) -> None:
    """Recursive type-walker. Raises InvalidEventTypeError on first offender."""
    if field_type in _PRIMITIVE_TYPES:
        return

    origin = get_origin(field_type)
    args = get_args(field_type)

    if origin is None:
        # A non-generic type. Allow other frozen dataclasses (recursive validation).
        if isinstance(field_type, type) and is_dataclass(field_type):
            validate_event_class(field_type)
            return
        raise InvalidEventTypeError(
            f"{cls_name}.{field_name} has type {field_type!r} which is not "
            f"allowed in events. Allowed: str, int, float, bool, None, "
            f"list/tuple/set/frozenset/dict of these, Optional/Union of these, "
            f"or another frozen dataclass. UUID/datetime/Enum types are "
            f"intentionally not supported in v1 — use str representations."
        )

    # Union (incl. Optional[X], X | Y on Python 3.10+).
    if origin is Union or _is_union_type(origin):
        for arg in args:
            _validate_field_type(cls_name, field_name, arg)
        return

    # Container types.
    if origin in (list, tuple, set, frozenset, dict):
        for arg in args:
            _validate_field_type(cls_name, field_name, arg)
        return

    raise InvalidEventTypeError(
        f"{cls_name}.{field_name} has unsupported generic type {field_type!r}"
    )


def _is_union_type(origin: Any) -> bool:
    """Detect PEP 604 union types (X | Y). On 3.10+, get_origin returns
    types.UnionType for `int | None`, distinct from typing.Union."""
    try:
        from types import UnionType  # type: ignore[attr-defined]

        return origin is UnionType
    except ImportError:  # pragma: no cover - Python <3.10
        return False


def event_to_dict(event: Any) -> dict:
    """Serialize an event dataclass instance to a dict for Celery transport."""
    return asdict(event)


def dict_to_event(cls: type, payload: dict) -> Any:
    """Deserialize a Celery payload dict back into an instance of ``cls``."""
    return cls(**payload)
