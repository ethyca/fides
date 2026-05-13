"""Taxonomy-aware data category filtering for preview output.

A field's data category matches a rule target when the category is equal to
the target *or* a descendant in the data-category taxonomy (e.g. a target
of ``user.contact`` matches ``user.contact.email``).
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache

from fideslang.default_taxonomy import DEFAULT_TAXONOMY


@lru_cache(maxsize=1)
def _parent_map() -> dict[str, str | None]:
    """Map of fides_key → parent fides_key drawn from DEFAULT_TAXONOMY.

    Cached so we build the dict once per process; the taxonomy is static.
    """
    return {
        cat.fides_key: cat.parent_key
        for cat in DEFAULT_TAXONOMY.data_category  # pylint: disable=not-an-iterable
    }


def _matches(category: str, targets: set[str], parents: dict[str, str | None]) -> bool:
    cursor: str | None = category
    visited: set[str] = set()
    while cursor:
        if cursor in targets:
            return True
        if cursor in visited:
            return False  # defensive; taxonomy shouldn't cycle
        visited.add(cursor)
        cursor = parents.get(cursor)
    # Category is not in the taxonomy (custom/extended). Fall back to
    # dot-prefix matching so behavior aligns with the real DSR runner
    # which uses ``category.startswith(target)``. We add a dot boundary
    # to avoid false positives like "user_provided" matching target "user".
    if category not in parents:
        return any(category == t or category.startswith(t + ".") for t in targets)
    return False


def filter_categories_by_targets(
    categories: Iterable[str],
    targets: set[str] | None,
) -> list[str]:
    """Return categories that are equal to or descendants of any target.

    When ``targets`` is ``None`` filtering is disabled and the input is
    returned unchanged (preserving the caller's order). Categories present
    in the taxonomy are matched via parent-chain walk; custom categories
    not in the taxonomy fall back to dot-prefix matching so the preview
    stays consistent with the real DSR runner.
    """
    if targets is None:
        return list(categories)
    if not targets:
        return []
    parents = _parent_map()
    return [c for c in categories if _matches(c, targets, parents)]
