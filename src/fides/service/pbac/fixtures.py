"""YAML fixture loaders for CLI-driven PBAC evaluation.

Mirrors policy-engine/pkg/fixtures/fixtures.go. The directory layout is
the one documented in pbac/README.md at the repo root:

    <config>/consumers/*.yml   top-level key: consumer:
    <config>/purposes/*.yml    top-level key: purpose:
    <config>/datasets/*.yml    fideslang Dataset YAML, top-level: dataset:
    <config>/policies/*.yml    top-level key: policy:

The loaders produce the same shapes as the Go loaders so the Python and
Go pipelines stay interchangeable per-statement. They are deliberately
dumb — no validation beyond "file parses as a YAML mapping" — because
the pipeline treats unknown identities, missing datasets, and empty
policy sets as first-class outcomes (gaps).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from fides.service.pbac.policies.evaluate import ParsedPolicy, parsed_policy_from_dict
from fides.service.pbac.types import DatasetPurposes

# ── Dataclasses mirroring the Go structs ─────────────────────────────


@dataclass(frozen=True)
class Consumer:
    """Matches fixtures.Consumer on the Go side."""

    name: str
    description: str = ""
    members: tuple[str, ...] = ()
    purposes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Purpose:
    """Matches fixtures.Purpose on the Go side.

    data_use is the single required taxonomy binding; the CLI uses it
    to map dataset purpose keys to data_use strings when evaluating
    access policies (see Pipeline.evaluate).
    """

    fides_key: str
    name: str
    data_use: str
    data_subject: str = ""
    data_categories: tuple[str, ...] = ()
    description: str = ""


@dataclass(frozen=True)
class Datasets:
    """Matches fixtures.Datasets on the Go side.

    purposes is keyed by dataset fides_key and fed to the engine.
    tables maps a lowercase table (collection) name to its owning
    dataset's fides_key.
    """

    purposes: dict[str, DatasetPurposes] = field(default_factory=dict)
    tables: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Fixtures:
    """Everything the pipeline consumes, pre-loaded.

    Built by load_fixtures(). Kept frozen so a single Fixtures instance
    can be shared across concurrent pipeline calls.
    """

    consumers: dict[str, Consumer] = field(default_factory=dict)
    purposes: dict[str, Purpose] = field(default_factory=dict)
    datasets: Datasets = field(default_factory=Datasets)
    policies: tuple[ParsedPolicy, ...] = ()


# ── Top-level loader ─────────────────────────────────────────────────


def load_fixtures(config_dir: str | os.PathLike[str]) -> Fixtures:
    """Load consumers/, purposes/, datasets/, policies/ from config_dir.

    Missing subdirectories are treated as empty (not an error); the
    pipeline's gap outputs cover the cases where that matters.
    """
    root = Path(config_dir)
    return Fixtures(
        consumers=load_consumers(root / "consumers"),
        purposes=load_purposes(root / "purposes"),
        datasets=load_datasets(root / "datasets"),
        policies=load_policies(root / "policies"),
    )


# ── Per-kind loaders ─────────────────────────────────────────────────


def load_consumers(directory: str | os.PathLike[str]) -> dict[str, Consumer]:
    """Return a map from member identity to Consumer.

    A consumer with N members appears N times in the map, once per
    member. Empty strings in `members` are skipped. When two consumers
    claim the same member, the last file loaded wins (fixture authors
    are expected to keep membership unambiguous).
    """
    directory = Path(directory)
    result: dict[str, Consumer] = {}
    if not directory.is_dir():
        return result
    for path in sorted(directory.glob("*.yml")):
        data = _read_yaml_mapping(path)
        for entry in data.get("consumer", []) or []:
            consumer = Consumer(
                name=entry.get("name", ""),
                description=entry.get("description", ""),
                members=tuple(entry.get("members", []) or []),
                purposes=tuple(entry.get("purposes", []) or []),
            )
            for member in consumer.members:
                if member:
                    result[member] = consumer
    return result


def load_purposes(directory: str | os.PathLike[str]) -> dict[str, Purpose]:
    """Return a map from fides_key to Purpose."""
    directory = Path(directory)
    result: dict[str, Purpose] = {}
    if not directory.is_dir():
        return result
    for path in sorted(directory.glob("*.yml")):
        data = _read_yaml_mapping(path)
        for entry in data.get("purpose", []) or []:
            key = entry.get("fides_key", "")
            if not key:
                continue
            result[key] = Purpose(
                fides_key=key,
                name=entry.get("name", ""),
                data_use=entry.get("data_use", ""),
                data_subject=entry.get("data_subject", ""),
                data_categories=tuple(entry.get("data_categories", []) or []),
                description=entry.get("description", ""),
            )
    return result


def load_datasets(directory: str | os.PathLike[str]) -> Datasets:
    """Return per-dataset purposes plus the table -> dataset_key index.

    Collection names are lowercased in the index so `orders` and
    `ORDERS` resolve to the same dataset. When multiple datasets declare
    a collection with the same name, the last file loaded wins.

    Purpose inheritance mirrors the Go loader:

        dataset.data_purposes
        -> DatasetPurposes.purpose_keys

        collection.data_purposes
        | union(field.data_purposes for each field in the collection)
        -> DatasetPurposes.collection_purposes[collection_name]

    The engine later unions these in effective_purposes(collection).
    """
    directory = Path(directory)
    result = Datasets(purposes={}, tables={})
    if not directory.is_dir():
        return result

    for path in sorted(directory.glob("*.yml")):
        data = _read_yaml_mapping(path)
        for entry in data.get("dataset", []) or []:
            fides_key = entry.get("fides_key", "")
            if not fides_key:
                continue
            collection_purposes: dict[str, frozenset[str]] = {}
            for collection in entry.get("collections", []) or []:
                name = (collection.get("name") or "").lower()
                if not name:
                    continue
                effective = _collection_effective_purposes(collection)
                if effective:
                    collection_purposes[name] = frozenset(effective)
                result.tables[name] = fides_key

            result.purposes[fides_key] = DatasetPurposes(
                dataset_key=fides_key,
                purpose_keys=frozenset(entry.get("data_purposes", []) or []),
                collection_purposes=collection_purposes,
            )

    return result


def load_policies(directory: str | os.PathLike[str]) -> tuple[ParsedPolicy, ...]:
    """Return the enabled policies from YAML files in load-sorted order.

    Each file's top-level `policy:` entries are merged into one list.
    Policies with `enabled: false` are filtered out — the pipeline
    never has to care about the enabled flag after load.
    """
    directory = Path(directory)
    result: list[ParsedPolicy] = []
    if not directory.is_dir():
        return tuple(result)
    for path in sorted(directory.glob("*.yml")):
        data = _read_yaml_mapping(path)
        for entry in data.get("policy", []) or []:
            if entry.get("enabled") is False:
                continue
            result.append(parsed_policy_from_dict(entry))
    return tuple(result)


# ── Private helpers ──────────────────────────────────────────────────


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    """Parse a YAML file that must contain a top-level mapping.

    Returns an empty dict for empty files or non-mapping documents —
    consistent with the Go loader's behavior of ignoring malformed
    files rather than aborting the whole load.
    """
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _collection_effective_purposes(collection: dict[str, Any]) -> list[str]:
    """Union a collection's own data_purposes with every field's.

    Result is deduplicated; order doesn't matter because the engine
    treats it as a set. Matches policy-engine/pkg/fixtures/fixtures.go:
    collectionEffectivePurposes().
    """
    purposes: set[str] = set(collection.get("data_purposes", []) or [])
    for fld in collection.get("fields", []) or []:
        for p in fld.get("data_purposes", []) or []:
            if p:
                purposes.add(p)
    purposes.discard("")
    return sorted(purposes)
