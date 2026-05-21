"""Tenant taxonomy resolver.

For v1, the taxonomy is sourced from fideslang's bundled DEFAULT_TAXONOMY.
A future iteration will overlay tenant-specific custom taxonomies from the
Fides DB (data_category, data_use, data_subject tables).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from fideslang.default_taxonomy import DEFAULT_TAXONOMY


@dataclass(frozen=True)
class TenantTaxonomy:
    data_uses: frozenset[str]
    data_categories: frozenset[str]
    data_subjects: frozenset[str]

    @classmethod
    def from_fideslang_defaults(cls) -> "TenantTaxonomy":
        return _build_default_taxonomy()

    def is_known_data_use(self, key: str) -> bool:
        return key in self.data_uses

    def is_known_data_category(self, key: str) -> bool:
        return key in self.data_categories

    def is_known_data_subject(self, key: str) -> bool:
        return key in self.data_subjects

    def allowed_data_uses(self) -> list[str]:
        return sorted(self.data_uses)

    def allowed_data_categories(self) -> list[str]:
        return sorted(self.data_categories)

    def allowed_data_subjects(self) -> list[str]:
        return sorted(self.data_subjects)


@lru_cache(maxsize=1)
def _build_default_taxonomy() -> TenantTaxonomy:
    uses = frozenset(item.fides_key for item in DEFAULT_TAXONOMY.data_use)
    cats = frozenset(item.fides_key for item in DEFAULT_TAXONOMY.data_category)
    subs = frozenset(item.fides_key for item in DEFAULT_TAXONOMY.data_subject)
    return TenantTaxonomy(data_uses=uses, data_categories=cats, data_subjects=subs)
