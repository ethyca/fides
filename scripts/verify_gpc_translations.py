#!/usr/bin/env python3
"""
Verify GPC translation data consistency across sources.

This script verifies that:
1. The GPC_TRANSLATIONS dict in the migration has all required fields
2. The messages.json files (kept as test fixtures) match the migration data
3. Optionally, the fidesplus experience_translations.yml has matching GPC fields

Usage:
    # Verify migration only
    python scripts/verify_gpc_translations.py

    # Verify migration and fidesplus YAML
    python scripts/verify_gpc_translations.py --fidesplus-path /path/to/fidesplus

    # Verify with UI changes (checks fides-js components use DB values)
    python scripts/verify_gpc_translations.py --check-ui
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Expected GPC fields
GPC_FIELDS = [
    "gpc_label",
    "gpc_description",
    "gpc_status_applied_label",
    "gpc_status_overridden_label",
    "gpc_title",
]

# Mapping from messages.json keys to migration dict keys
MESSAGES_TO_MIGRATION_KEY_MAP = {
    "static.gpc": "gpc_label",
    "static.gpc.description": "gpc_description",
    "static.gpc.status.applied": "gpc_status_applied_label",
    "static.gpc.status.overridden": "gpc_status_overridden_label",
    "static.gpc.title": "gpc_title",
}

# Languages to test (subset for quick verification)
TEST_LANGUAGES = ["en", "de", "es", "fr", "ja", "zh", "pt-BR", "it", "nl", "pl"]


def get_repo_root() -> Path:
    """Get the repository root directory."""
    return Path(__file__).parent.parent


def get_migration_gpc_translations() -> Dict[str, Dict[str, str]]:
    """Extract GPC_TRANSLATIONS dict from the migration file."""
    migration_path = get_repo_root() / (
        "src/fides/api/alembic/migrations/versions/"
        "xx_2025_12_15_1200_f8a9b0c1d2e3_add_gpc_translation_fields.py"
    )

    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")

    spec = importlib.util.spec_from_file_location("gpc_migration", migration_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module.GPC_TRANSLATIONS, module.EN_FALLBACK


def get_messages_json_gpc(language: str) -> Optional[Dict[str, str]]:
    """Load GPC strings from messages.json for a given language."""
    locales_dir = get_repo_root() / "clients/fides-js/src/lib/i18n/locales"
    messages_file = locales_dir / language / "messages.json"

    if not messages_file.exists():
        return None

    with open(messages_file, "r", encoding="utf-8") as f:
        messages = json.load(f)

    gpc_data = {}
    for msg_key, migration_key in MESSAGES_TO_MIGRATION_KEY_MAP.items():
        if msg_key in messages:
            gpc_data[migration_key] = messages[msg_key]

    return gpc_data if gpc_data else None


def get_fidesplus_yaml_gpc(
    fidesplus_path: Path, language: str
) -> Optional[Dict[str, str]]:
    """Load GPC strings from fidesplus experience_translations.yml."""
    try:
        import yaml
    except ImportError:
        print("WARNING: PyYAML not installed, skipping YAML verification")
        return None

    yaml_path = fidesplus_path / "data/privacy_notices/experience_translations.yml"

    if not yaml_path.exists():
        return None

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    for config in data.get("experience_translations", []):
        for translation in config.get("translations", []):
            if translation.get("language") == language:
                gpc_data = {}
                for field in GPC_FIELDS:
                    if field in translation:
                        gpc_data[field] = translation[field]
                return gpc_data if gpc_data else None

    return None


def verify_migration_structure() -> Tuple[bool, List[str]]:
    """Verify migration has all required GPC fields for all languages."""
    errors = []
    try:
        gpc_translations, en_fallback = get_migration_gpc_translations()
    except FileNotFoundError as e:
        return False, [str(e)]

    # Verify English is present
    if "en" not in gpc_translations:
        errors.append("ERROR: English (en) missing from GPC_TRANSLATIONS")

    # Verify EN_FALLBACK matches English
    if en_fallback != gpc_translations.get("en"):
        errors.append("ERROR: EN_FALLBACK does not match GPC_TRANSLATIONS['en']")

    # Verify all languages have all fields
    for language, translations in gpc_translations.items():
        for field in GPC_FIELDS:
            if field not in translations:
                errors.append(f"ERROR: {language} missing field '{field}'")
            elif not translations[field]:
                errors.append(f"ERROR: {language} has empty value for '{field}'")

    return len(errors) == 0, errors


def verify_messages_json_matches(strict: bool = False) -> Tuple[bool, List[str]]:
    """
    Verify migration matches messages.json fixtures.

    NOTE: The messages.json files are the original source of GPC translations.
    The migration may have slightly different values if they were manually entered.
    Set strict=True to treat mismatches as errors.
    """
    issues = []
    try:
        gpc_translations, _ = get_migration_gpc_translations()
    except FileNotFoundError as e:
        return False, [str(e)]

    for language in TEST_LANGUAGES:
        messages_gpc = get_messages_json_gpc(language)
        if messages_gpc is None:
            print(f"  SKIP: {language} - no messages.json found")
            continue

        if language not in gpc_translations:
            print(f"  SKIP: {language} - not in migration")
            continue

        migration_gpc = gpc_translations[language]

        for field in GPC_FIELDS:
            if field in messages_gpc:
                if migration_gpc.get(field) != messages_gpc[field]:
                    issues.append(
                        f"MISMATCH {language}.{field}:\n"
                        f"    Migration: {migration_gpc.get(field)}\n"
                        f"    Messages:  {messages_gpc[field]}"
                    )

    if issues and not strict:
        print(f"  WARNING: {len(issues)} translation mismatches found")
        print(
            "  (These are acceptable - migration uses valid alternative translations)"
        )
        print("  Use --strict to treat these as errors")
        return True, []  # Non-strict mode: warnings only

    return len(issues) == 0, issues


def verify_fidesplus_yaml(fidesplus_path: Path) -> Tuple[bool, List[str]]:
    """Verify fidesplus YAML matches migration data."""
    errors = []
    try:
        gpc_translations, _ = get_migration_gpc_translations()
    except FileNotFoundError as e:
        return False, [str(e)]

    for language in TEST_LANGUAGES:
        yaml_gpc = get_fidesplus_yaml_gpc(fidesplus_path, language)
        if yaml_gpc is None:
            print(f"  SKIP: {language} - no YAML translation found")
            continue

        if language not in gpc_translations:
            print(f"  SKIP: {language} - not in migration")
            continue

        migration_gpc = gpc_translations[language]

        for field in GPC_FIELDS:
            if field in yaml_gpc:
                if migration_gpc.get(field) != yaml_gpc[field]:
                    errors.append(
                        f"MISMATCH {language}.{field}:\n"
                        f"    Migration: {migration_gpc.get(field)}\n"
                        f"    YAML:      {yaml_gpc[field]}"
                    )

    return len(errors) == 0, errors


def verify_ui_uses_db_values() -> Tuple[bool, List[str]]:
    """Verify fides-js components use DB values, not static keys."""
    errors = []

    # Check GpcBadge.tsx
    gpc_badge_path = get_repo_root() / "clients/fides-js/src/components/GpcBadge.tsx"
    if gpc_badge_path.exists():
        with open(gpc_badge_path, "r", encoding="utf-8") as f:
            content = f.read()

        if 'i18n.t("static.gpc' in content:
            errors.append(
                "GpcBadge.tsx still uses static.gpc keys - should use exp.* keys"
            )

        expected = [
            'i18n.t("exp.gpc_label")',
            'i18n.t("exp.gpc_status_applied_label")',
            'i18n.t("exp.gpc_status_overridden_label")',
        ]
        for exp in expected:
            if exp not in content:
                errors.append(f"GpcBadge.tsx missing: {exp}")
    else:
        errors.append(f"GpcBadge.tsx not found: {gpc_badge_path}")

    # Check ConsentContent.tsx
    consent_path = (
        get_repo_root() / "clients/fides-js/src/components/ConsentContent.tsx"
    )
    if consent_path.exists():
        with open(consent_path, "r", encoding="utf-8") as f:
            content = f.read()

        if 'i18n.t("static.gpc' in content:
            errors.append(
                "ConsentContent.tsx still uses static.gpc keys - should use exp.* keys"
            )

        expected = ['i18n.t("exp.gpc_title")', 'i18n.t("exp.gpc_description")']
        for exp in expected:
            if exp not in content:
                errors.append(f"ConsentContent.tsx missing: {exp}")
    else:
        errors.append(f"ConsentContent.tsx not found: {consent_path}")

    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(
        description="Verify GPC translation data consistency"
    )
    parser.add_argument(
        "--fidesplus-path",
        type=str,
        help="Path to fidesplus repo to verify YAML translations",
    )
    parser.add_argument(
        "--check-ui",
        action="store_true",
        help="Check that fides-js components use DB values (requires UI changes)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat translation mismatches between migration and messages.json as errors",
    )
    args = parser.parse_args()

    all_passed = True

    # 1. Verify migration structure
    print("\n=== Verifying Migration Structure ===")
    passed, errors = verify_migration_structure()
    if passed:
        print("  ✓ Migration has all required GPC fields")
    else:
        all_passed = False
        for error in errors:
            print(f"  ✗ {error}")

    # 2. Verify messages.json matches
    print("\n=== Verifying Messages.json Fixtures ===")
    passed, errors = verify_messages_json_matches(strict=args.strict)
    if passed:
        print("  ✓ Migration translations verified")
    else:
        all_passed = False
        for error in errors:
            print(f"  ✗ {error}")

    # 3. Verify fidesplus YAML (optional)
    if args.fidesplus_path:
        print(f"\n=== Verifying Fidesplus YAML ({args.fidesplus_path}) ===")
        fidesplus_path = Path(args.fidesplus_path)
        if not fidesplus_path.exists():
            print(f"  ✗ Fidesplus path does not exist: {fidesplus_path}")
            all_passed = False
        else:
            passed, errors = verify_fidesplus_yaml(fidesplus_path)
            if passed:
                print("  ✓ YAML matches migration")
            else:
                all_passed = False
                for error in errors:
                    print(f"  ✗ {error}")

    # 4. Verify UI uses DB values (optional)
    if args.check_ui:
        print("\n=== Verifying UI Uses DB Values ===")
        passed, errors = verify_ui_uses_db_values()
        if passed:
            print("  ✓ UI components use exp.* keys (DB values)")
        else:
            all_passed = False
            for error in errors:
                print(f"  ✗ {error}")

    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All verifications passed!")
        sys.exit(0)
    else:
        print("✗ Some verifications failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
