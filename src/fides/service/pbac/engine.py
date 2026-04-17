"""Python bindings for the Go PBAC evaluation library (libpbac).

Loads the compiled Go shared library and exposes its functions as
Python callables. All functions follow the same pattern: accept a
Python dict, serialize to JSON, call Go, deserialize the JSON response.

The shared library is the single source of truth for all evaluation
logic. Python never reimplements any evaluation — it only handles
SQL parsing (sqlglot) and I/O (CLI, HTTP serialization).

Usage:
    from fides.service.pbac.engine import evaluate_pipeline, load_fixtures

    fixtures = load_fixtures("/path/to/pbac/config")
    record = evaluate_pipeline(fixtures, {
        "identity": "alice@example.com",
        "tables": [{"collection": "orders"}],
    })
"""

from __future__ import annotations

import ctypes
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

# ── Library loading ──────────────────────────────────────────────────

_lib: ctypes.CDLL | None = None


def _lib_filename() -> str:
    """Platform-specific shared library filename."""
    system = platform.system()
    if system == "Darwin":
        return "libpbac.dylib"
    if system == "Windows":
        return "libpbac.dll"
    return "libpbac.so"


def _find_library() -> Path:
    """Search for libpbac in standard locations.

    Order:
      1. FIDES_PBAC_LIB_PATH env var (explicit override)
      2. fides/bin/ inside the installed package (wheel distribution)
      3. policy-engine/ build output (local dev)
    """
    env_path = os.environ.get("FIDES_PBAC_LIB_PATH")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p

    filename = _lib_filename()

    # Wheel location: fides/bin/libpbac.so
    pkg_bin = Path(__file__).parent.parent.parent / "bin" / filename
    if pkg_bin.is_file():
        return pkg_bin

    # Local dev: policy-engine/ build output
    repo_root = Path(__file__).parent.parent.parent.parent.parent
    dev_path = repo_root / "policy-engine" / filename
    if dev_path.is_file():
        return dev_path

    raise RuntimeError(
        f"Could not find {filename}. Set FIDES_PBAC_LIB_PATH or build with: "
        f"cd policy-engine && go build -buildmode=c-shared -o {filename} ./cmd/libpbac/"
    )


_lib_lock = __import__("threading").Lock()


def _get_lib() -> ctypes.CDLL:
    """Load the shared library (singleton, thread-safe)."""
    global _lib
    if _lib is not None:
        return _lib

    with _lib_lock:
        if _lib is not None:
            return _lib  # another thread won the race

        path = _find_library()
        lib = ctypes.cdll.LoadLibrary(str(path))

        # All exported functions take a C string and return a C string.
        # Use c_void_p (not c_char_p) as restype so ctypes doesn't
        # auto-convert the pointer to bytes — we need the raw pointer
        # to pass to FreeString after copying the data.
        for fn_name in (
            "EvaluatePipelineJSON",
            "EvaluatePurposeJSON",
            "EvaluatePoliciesJSON",
            "LoadFixturesJSON",
        ):
            fn = getattr(lib, fn_name)
            fn.argtypes = [ctypes.c_char_p]
            fn.restype = ctypes.c_void_p

        lib.FreeString.argtypes = [ctypes.c_void_p]
        lib.FreeString.restype = None

        _lib = lib

    return _lib


def _call(fn_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Call a Go function: dict -> JSON -> Go -> JSON -> dict.

    The Go side allocates the response via C.CString (malloc). We copy
    the bytes into Python, then free the C buffer via FreeString to
    avoid a memory leak.
    """
    lib = _get_lib()
    fn = getattr(lib, fn_name)
    input_bytes = json.dumps(payload).encode("utf-8")
    result_ptr = fn(input_bytes)
    try:
        result_bytes = ctypes.string_at(result_ptr)
        result = json.loads(result_bytes)
    finally:
        lib.FreeString(result_ptr)
    if "error" in result:
        raise RuntimeError(f"Go engine error: {result['error']}")
    return result


# ── Public API ───────────────────────────────────────────────────────


def load_fixtures(config_dir: str | os.PathLike[str]) -> dict[str, Any]:
    """Load YAML fixtures from a config directory via Go.

    Returns a dict with keys: consumers, purposes, datasets, policies.
    This dict can be passed directly as the "fixtures" field to
    evaluate_pipeline().
    """
    return _call("LoadFixturesJSON", {"config_dir": str(config_dir)})


def evaluate_pipeline(
    fixtures: dict[str, Any],
    input: dict[str, Any],
) -> dict[str, Any]:
    """Run the full PBAC pipeline via Go.

    fixtures: the output of load_fixtures() or an equivalent dict.
    input: {"identity": str, "tables": [...], "query_id": str, ...}

    Returns an EvaluationRecord dict.
    """
    return _call(
        "EvaluatePipelineJSON",
        {
            "fixtures": fixtures,
            "input": input,
        },
    )


def evaluate_purpose(
    consumer: dict[str, Any],
    datasets: dict[str, dict[str, Any]],
    collections: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Evaluate purpose overlap via Go.

    Lower-level primitive — most callers should use evaluate_pipeline()
    which runs the full pipeline including identity/dataset resolution.
    """
    return _call(
        "EvaluatePurposeJSON",
        {
            "consumer": consumer,
            "datasets": datasets,
            "collections": collections or {},
        },
    )


def evaluate_policies(
    policies: list[dict[str, Any]],
    request: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate access policies via Go.

    Lower-level primitive — most callers should use evaluate_pipeline()
    which runs the full pipeline including policy filtering.
    """
    return _call(
        "EvaluatePoliciesJSON",
        {
            "policies": policies,
            "request": request,
        },
    )
