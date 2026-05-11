#!/usr/bin/env python3
"""Fail CI if ``lethe.state`` (Postgres ``DSRStore``) violates package boundaries.

``lethe.state`` must remain a thin persistence facade: no Redis client usage, no
transaction control (``commit``/``rollback``), and no application-wide ``get_cache``.
One-off Redis reads belong in ``lethe.migration`` only.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    state_dir = root / "src" / "lethe" / "state"
    if not state_dir.is_dir():
        print(f"Expected lethe state dir at {state_dir}", file=sys.stderr)
        return 1

    failures: list[str] = []
    for path in sorted(state_dir.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root)
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            lower = stripped.lower()
            if "from redis" in lower or lower.startswith("import redis"):
                failures.append(f"{rel}:{i}: forbidden Redis import in lethe.state")
            if ".commit(" in stripped:
                failures.append(f"{rel}:{i}: forbidden .commit( in lethe.state")
            if "rollback(" in stripped:
                failures.append(f"{rel}:{i}: forbidden rollback( in lethe.state")
            if "get_cache(" in stripped:
                failures.append(f"{rel}:{i}: forbidden get_cache( in lethe.state")

    if failures:
        print("Lethe state boundary violations:\n", file=sys.stderr)
        for msg in failures:
            print(msg, file=sys.stderr)
        return 1

    print("OK: lethe.state boundary check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
