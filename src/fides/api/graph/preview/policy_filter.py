"""Taxonomy-aware data category filtering for preview output.

A field's data category matches a rule target when the category is equal to
the target *or* a descendant in the data-category taxonomy (e.g. a target
of ``user.contact`` matches ``user.contact.email``).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Set

from fideslang.default_taxonomy import DEFAULT_TAXONOMY


@lru_cache(maxsize=1)
def _parent_map() -> Dict[str, Optional[str]]:
    """Map of fides_key → parent fides_key drawn from DEFAULT_TAXONOMY.

    Cached so we build the dict once per process; the taxonomy is static.
    """
    return {
        cat.fides_key: cat.parent_key
        for cat in DEFAULT_TAXONOMY.data_category  # pylint: disable=not-an-iterable
    }


def _matches(category: str, targets: Set[str], parents: Dict[str, Optional[str]]) -> bool:
    cursor: Optional[str] = category
    visited: Set[str] = set()
    while cursor:
        if cursor in targets:
            return True
        if cursor in visited:
            return False  # defensive; taxonomy shouldn't cycle
        visited.add(cursor)
        cursor = parents.get(cursor)
    return False


def filter_categories_by_targets(
    categories: Iterable[str],
    targets: Optional[Set[str]],
) -> List[str]:
    """Return categories that are equal to or descendants of any target.

    When ``targets`` is ``None`` filtering is disabled and the input is
    returned unchanged (preserving the caller's order). Categories not
    present in the taxonomy are conservatively dropped only when filtering
    is active and the unknown category can't be matched to any target.
    """
    if targets is None:
        return list(categories)
    if not targets:
        return []
    parents = _parent_map()
    return [c for c in categories if _matches(c, targets, parents)]
